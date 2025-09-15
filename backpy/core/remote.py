import shutil
import uuid
import warnings
from dataclasses import dataclass
from hashlib import file_digest
from pathlib import Path
from stat import S_ISDIR

import numpy as np
import paramiko
from paramiko import SSHClient
from paramiko.sftp_client import SFTPClient
from paramiko.ssh_exception import SSHException
from rich.progress import DownloadColumn, Progress, TransferSpeedColumn
from scp import SCPClient

from backpy import TOMLConfiguration, VariableLibrary
from backpy.core.password import decrypt, encrypt
from backpy.exceptions import (
    InvalidChecksumError,
    InvalidRemoteError,
    UnsupportedProtocolError,
)


def _calculate_hash(path: Path) -> str:
    with open(path, "rb") as f:
        digest = file_digest(f, "sha256")
    return digest.hexdigest()


@dataclass
class Protocol:
    name: str
    description: str
    supports_ssh_keys: bool

    @classmethod
    def from_name(cls, name: str):
        for protocol in _protocols:
            if protocol.name == name:
                return protocol
        return None


def get_remotes():
    return [
        Remote.load_by_uuid(tomlf.stem)
        for tomlf in Path(
            VariableLibrary().get_variable("paths.remote_directory")
        ).rglob("*.toml")
    ]


_protocols = [
    Protocol(
        name="scp",
        description="Uses the the 'scp.py' module to transfer files using scp (Secure Copy).",
        supports_ssh_keys=True,
    ),
    Protocol(
        name="sftp",
        description="Uses the 'paramiko' module to transfer files using SFTP "
        "(Safe File Transport Protocol).",
        supports_ssh_keys=True,
    ),
]


class Remote:
    def __init__(
        self,
        name: str,
        unique_id: uuid.UUID,
        protocol: Protocol,
        hostname: str,
        username: str,
        token: str | None,
        ssh_key: Path | None,
        use_system_keys: bool,
        root_dir: str,
        sha256_cmd: str,
    ):
        self._name: str = name
        self._uuid: uuid.UUID = unique_id
        self._protocol: Protocol = protocol

        self._hostname: str = hostname

        self._username: str = username
        self._token: str = token

        self._ssh_key: Path | None = ssh_key
        self._use_system_keys: bool = use_system_keys

        self._client: SSHClient | None = None
        self._root_dir: str = root_dir
        self._sha256_cmd: str = sha256_cmd

    def connect(self, verbosity_level: int = 1) -> None:

        if self._client is not None:
            self._client.close()

        self._client = SSHClient()
        self._client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy)

        if self._ssh_key:
            try:
                private_key = paramiko.rsakey.RSAKey.from_private_key_file(
                    filename=self._ssh_key, password=decrypt(self._token)
                )
            except SSHException:
                private_key = paramiko.ed25519key.Ed25519Key.from_private_key_file(
                    filename=self._ssh_key, password=decrypt(self._token)
                )
            except FileNotFoundError:
                private_key = None
        else:
            private_key = None

        self._client.connect(
            hostname=self._hostname,
            username=self._username,
            password=decrypt(self._token),
            pkey=private_key,
            look_for_keys=self._use_system_keys,
        )

        if verbosity_level > 1:
            print(f"Connected to {self._hostname} with user {self._username}.")

    def disconnect(self, verbosity_level: int = 1) -> None:
        self._client.close()

        if verbosity_level > 1:
            print(f"Connection to {self._hostname} was closed.")

    def test_connection(self, verbosity_level: int = 1) -> None:
        self.connect()
        self.disconnect()

        if verbosity_level > 1:
            print(
                f"Connection test to {self._hostname} with "
                f"user {self._username} was successful."
            )

    def upload(
        self,
        source: Path | str,
        target: str,
        check_hash: bool = True,
        retry_on_hash_missmatch: bool = True,
        max_retries: int = 3,
        verbosity_level: int = 1,
    ) -> None:

        if isinstance(source, str):
            source = Path(source)

        self.connect(verbosity_level=verbosity_level)
        with Progress(
            *Progress.get_default_columns(), DownloadColumn(), TransferSpeedColumn()
        ) as progress:

            task = progress.add_task(
                f"Uploading {source.name}", visible=verbosity_level >= 1
            )

            match self._protocol.name:
                case "sftp":
                    sftp_client = self._client.open_sftp()

                    if source.is_file():
                        size = source.stat().st_size
                    else:
                        size = int(
                            np.sum(
                                [
                                    file.stat().st_size if file.is_file() else 0
                                    for file in source.rglob("*")
                                ]
                            )
                        )

                    progress.update(task, total=size)
                    cur_file = source
                    cur_sent = 0
                    _progress = lambda sent, total: progress.update(
                        task,
                        completed=sent + cur_sent,
                        total=size,
                        description=f"Uploading {cur_file.name}",
                    )

                    target_paths = target.split("/")

                    if len(target_paths) > 1:
                        self.mkdir(
                            "/".join(target_paths[:-1]),
                            parents=True,
                            close_afterwards=False,
                            client=sftp_client,
                        )

                    if source.is_file():
                        sftp_client.put(
                            localpath=source, remotepath=target, callback=_progress
                        )
                    else:
                        for root, dirs, files in Path(source).walk(
                            follow_symlinks=False
                        ):

                            self.mkdir(
                                target=str(target / root),
                                parents=True,
                                close_afterwards=False,
                                client=sftp_client,
                            )

                            for file in files:
                                cur_file = str(root / file)
                                cur_sent = progress._tasks[task].completed
                                sftp_client.put(
                                    localpath=root / file,
                                    remotepath=target + "/" + str(root / file),
                                    callback=_progress,
                                )

                case "scp":

                    _progress = lambda filename, total, sent: progress.update(
                        task, total=total, completed=sent
                    )

                    scp_client = SCPClient(
                        self._client.get_transport(), progress=_progress
                    )

                    if len(target.split("/")) > 1:
                        self.mkdir(
                            target=target,
                            parents=True,
                            close_afterwards=False,
                            client=scp_client,
                        )

                    scp_client.put(files=source, remote_path=target, recursive=True)

        self.disconnect(verbosity_level=verbosity_level)

        if check_hash:
            if (
                _calculate_hash(source).lower()
                != self.get_hash(target, verbosity_level).lower()
            ):
                if retry_on_hash_missmatch and max_retries > 0:
                    warnings.warn(
                        "The SHA256 of the downloaded file did not match the"
                        "remote file. Retrying download."
                    )
                    self.remove(target)
                    self.upload(
                        source=source,
                        target=target,
                        check_hash=check_hash,
                        retry_on_hash_missmatch=retry_on_hash_missmatch,
                        max_retries=max_retries - 1,
                        verbosity_level=verbosity_level,
                    )
                else:
                    warnings.warn(
                        "The SHA256 of the downloaded file did not match the "
                        "remote file. Did not attempt retry."
                    )
            elif verbosity_level > 1:
                print(f"Checksum matched: {_calculate_hash(source).lower()}")

    def download(
        self,
        source: str,
        target: Path | str,
        check_hash: bool = True,
        retry_on_hash_missmatch: bool = True,
        max_retries: int = 3,
        verbosity_level: int = 1,
    ) -> None:

        if isinstance(target, str):
            target = Path(target)

        self.connect(verbosity_level=verbosity_level)

        with Progress(
            *Progress.get_default_columns(), DownloadColumn(), TransferSpeedColumn()
        ) as progress:
            task = progress.add_task(
                f"Downloading {source}", visible=verbosity_level >= 1
            )

            match self._protocol.name:
                case "sftp":
                    _progress = lambda received, total: progress.update(
                        task, total=total, completed=received
                    )

                    sftp_client = self._client.open_sftp()
                    sftp_client.get(
                        remotepath=source, localpath=target, callback=_progress
                    )

                case "scp":
                    _progress = lambda filename, received, total: progress.update(
                        task, total=total, completed=received
                    )

                    scp_client = SCPClient(
                        self._client.get_transport(), progress=_progress
                    )
                    scp_client.get(remote_path=source, local_path=str(target))

        self.disconnect(verbosity_level=verbosity_level)

        if check_hash:
            if (
                _calculate_hash(target).lower()
                != self.get_hash(source, verbosity_level).lower()
            ):
                if retry_on_hash_missmatch and max_retries > 0:
                    warnings.warn(
                        "The SHA256 of the downloaded file did not match the "
                        "remote file. Retrying download."
                    )
                    target.unlink()
                    self.download(
                        source=source,
                        target=target,
                        check_hash=check_hash,
                        retry_on_hash_missmatch=retry_on_hash_missmatch,
                        max_retries=max_retries - 1,
                        verbosity_level=retry_on_hash_missmatch,
                    )
                else:
                    raise InvalidChecksumError(
                        "The SHA256 of the downloaded file did not match the "
                        "remote file. Not retrying."
                    )
            elif verbosity_level > 1:
                print(f"Checksum matched: {_calculate_hash(target).lower()}")

    def mkdir(
        self,
        target: str,
        parents: bool = False,
        close_afterwards: bool = True,
        client: SFTPClient | SCPClient | None = None,
        verbosity_level: int = 1,
    ) -> None:

        if not client:
            self.connect(verbosity_level=verbosity_level)

        subdirs = target.split("/")

        match self._protocol.name:
            case "sftp":
                sftp_client = (
                    client
                    if isinstance(client, SFTPClient)
                    else self._client.open_sftp()
                )

                if parents:
                    for i in range(len(subdirs)):
                        try:
                            sftp_client.mkdir(path="/".join(subdirs[: i + 1]))
                        except OSError:
                            pass
                else:
                    try:
                        sftp_client.mkdir(path=target)
                    except OSError:
                        pass

            case "scp":
                scp_client = (
                    client
                    if isinstance(client, SCPClient)
                    else SCPClient(self._client.get_transport())
                )

                # create a temporary version of the directory tree
                path = Path(str(uuid.uuid4()))
                while path.exists():
                    path = Path(str(uuid.uuid4()))
                path.mkdir()

                directory = path / target
                directory.mkdir(parents=True)

                try:
                    if parents:
                        scp_client.put(
                            files=str(path / subdirs[0]),
                            remote_path=subdirs[0],
                            recursive=True,
                        )
                    else:
                        scp_client.put(
                            files=str(directory), remote_path=target, recursive=True
                        )
                except Exception as e:
                    shutil.rmtree(path)
                    raise e

                # delete the temporary tree
                shutil.rmtree(path)

        if close_afterwards:
            self.disconnect(verbosity_level=verbosity_level)

        if verbosity_level > 1:
            print(
                f"Created directory {target} on {self._hostname}. "
                f"(Including parent directories: {parents})"
            )

    def _is_dir(
        self,
        target: str,
        sftp_client: SFTPClient | None = None,
        close_afterwards: bool = True,
    ) -> bool:

        if not sftp_client:
            self.connect()
            sftp_client = self._client.open_sftp()

        result = False
        try:
            result = S_ISDIR(sftp_client.stat(target).st_mode)
        except IOError:
            pass

        if close_afterwards:
            self.disconnect()

        return result

    def remove(
        self,
        target: str,
        sftp_client: SFTPClient | None = None,
        close_afterwards: bool = True,
        verbosity_level: int = 1,
    ) -> None:

        if not sftp_client:
            self.connect(verbosity_level=verbosity_level)
            sftp_client = self._client.open_sftp()

        if not self._is_dir(target, sftp_client=sftp_client, close_afterwards=False):
            sftp_client.remove(target)

            if verbosity_level >= 2:
                print(f"File at remote path '{target}' was removed.")
        else:
            files = sftp_client.listdir(path=target)

            for f in files:
                filepath = str(Path(target) / f)
                if self._is_dir(
                    filepath, sftp_client=sftp_client, close_afterwards=False
                ):
                    self.remove(
                        filepath,
                        sftp_client=sftp_client,
                        verbosity_level=verbosity_level,
                        close_afterwards=False,
                    )
                else:
                    sftp_client.remove(filepath)
                    if verbosity_level >= 2:
                        print(f"File at remote path '{target}' was removed.")

            sftp_client.rmdir(target)

            if verbosity_level >= 2:
                print(f"Directory at remote path '{target}' was removed.")

        if close_afterwards:
            self.disconnect(verbosity_level=verbosity_level)

    def get_hash(self, target: str, verbosity_level: int = 1) -> str:
        self.connect(verbosity_level=verbosity_level)

        checksum = (
            self._client.exec_command(self._sha256_cmd + " " + target)[1]
            .read()
            .decode()
            .split(" ")[0]
        )

        self.disconnect(verbosity_level=verbosity_level)

        return checksum

    #####################
    #    CLASSMETHODS   #
    #####################

    @classmethod
    def load_by_uuid(cls, unique_id: str) -> "Remote":

        unique_id = uuid.UUID(unique_id)

        config = TOMLConfiguration(
            Path(VariableLibrary().get_variable("paths.remote_directory"))
            / (str(unique_id) + ".toml"),
            create_if_not_exists=False,
        )

        if not config.is_valid():
            raise InvalidRemoteError(
                f"The remote with UUID '{str(unique_id)}' could not be found!"
            )

        cls = cls(
            name=config["name"],
            unique_id=unique_id,
            protocol=Protocol.from_name(config["protocol"]),
            hostname=config["hostname"],
            username=config["username"],
            token=config["token"] if config["token"] != "" else None,
            ssh_key=Path(config["ssh_key"]).expanduser().absolute()
            if config["ssh_key"] != ""
            else None,
            use_system_keys=config["use_system_keys"],
            root_dir=config["root_dir"],
            sha256_cmd=config["sha256_cmd"],
        )

        return cls

    @classmethod
    def load_by_name(cls, name: str) -> "Remote":
        for tomlf in Path(
            VariableLibrary().get_variable("paths.remote_directory")
        ).rglob("*.toml"):
            config = TOMLConfiguration(tomlf, create_if_not_exists=False)

            if not config.is_valid():
                continue

            if name != config["name"]:
                continue

            try:
                return Remote.load_by_uuid(unique_id=config["uuid"])
            except InvalidRemoteError:
                break

        raise InvalidRemoteError(
            f"There is no valid remote present with the name '{name}'."
        )

    @classmethod
    def new(
        cls,
        name: str,
        protocol: str,
        hostname: str,
        username: str,
        password: str | None = None,
        ssh_key: str | None = None,
        use_system_keys: bool = False,
        root_dir: str = VariableLibrary().get_variable(
            "backup.states.default_remote_root_dir"
        ),
        sha256_cmd: str = VariableLibrary().get_variable(
            "backup.states.default_sha256_cmd"
        ),
        verbosity_level: int = 1,
        test_connection: bool = True,
    ) -> "Remote":

        _protocol = Protocol.from_name(protocol)

        if protocol is None:
            raise UnsupportedProtocolError(
                f"The protocol '{protocol}' is not supported!"
            )

        if not _protocol.supports_ssh_keys and ssh_key is not None:
            raise ValueError("The chosen protocol does not support SSH keys!")

        if username is None:
            raise ValueError("The username has to be specified!")

        if password is None and not _protocol.supports_ssh_keys:
            raise ValueError(
                f"The '{_protocol.name}' does not support usage of SSH keys. "
                "Choose a different protocol or provide a password!"
            )

        if password is None and ssh_key is None and not use_system_keys:
            raise ValueError(
                "It is necessary to provide at least one valid authorization method."
            )

        unique_id = uuid.uuid4()

        cls = cls(
            name=name,
            unique_id=unique_id,
            protocol=_protocol,
            hostname=hostname,
            username=username,
            token=encrypt(password),
            ssh_key=Path(ssh_key).expanduser().absolute() if ssh_key else None,
            use_system_keys=use_system_keys,
            root_dir=root_dir,
            sha256_cmd=sha256_cmd,
        )

        cls._config = TOMLConfiguration(
            Path(VariableLibrary().get_variable("paths.remote_directory"))
            / (str(unique_id) + ".toml"),
            create_if_not_exists=True,
        )

        cls._config.dump_dict(
            {
                "name": cls._name,
                "uuid": str(cls._uuid),
                "protocol": cls._protocol.name,
                "hostname": cls._hostname,
                "username": cls._username,
                "token": cls._token if cls._token else "",
                "ssh_key": str(cls._ssh_key) if cls._ssh_key else "",
                "use_system_keys": cls._use_system_keys,
                "root_dir": cls._root_dir,
                "sha256_cmd": cls._sha256_cmd,
            }
        )
        cls._config.prepend_no_edit_warning()

        if test_connection:
            cls.test_connection(verbosity_level=verbosity_level)

        if verbosity_level >= 1:
            print(
                f"Created remote {cls._name} (Hostname: {cls._hostname}, "
                f"User: {cls._username}).\n"
                f"Using Protocol {cls._protocol.name}."
            )

        return cls

    #####################
    #       GETTER      #
    #####################

    def get_name(self) -> str:
        return self._name

    def get_uuid(self) -> uuid.UUID:
        return self._uuid

    def get_protocol(self) -> Protocol:
        return self._protocol

    def get_hostname(self) -> str:
        return self._hostname

    def get_username(self) -> str:
        return self._username

    def get_ssh_key(self) -> Path:
        return self._ssh_key

    def should_use_system_keys(self) -> bool:
        return self._use_system_keys

    def get_root_dir(self) -> str:
        return self._root_dir

    def get_sha256_cmd(self) -> str:
        return self._sha256_cmd

    def get_relative_to_root(self, path: Path | str) -> str:
        return str(Path(self.get_root_dir()) / path)
