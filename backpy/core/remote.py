import uuid
from dataclasses import dataclass
from pathlib import Path

import paramiko
from paramiko import SSHClient
from paramiko.ssh_exception import SSHException

from backpy.core.configuration import TOMLConfiguration
from backpy.core.variables import VariableLibrary


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


_protocols = [
    Protocol(
        "scp",
        "Uses the the 'scp.py' module to transfer files using scp (Secure Copy).",
        True,
    ),
    Protocol(
        "sftp",
        "Uses the 'paramiko' module to transfer files using SFTP "
        "(Safe File Transport Protocol).",
        False,
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
        password: str | None,
        ssh_key: Path | None,
        use_system_keys: bool,
        root_dir: str,
    ):
        self._name: str = name
        self._uuid: uuid.UUID = unique_id
        self._protocol: Protocol = protocol

        self._hostname: str = hostname

        self._username: str = username
        self._password: str = password

        self._ssh_key: Path | None = ssh_key
        self._use_system_keys: bool = use_system_keys

        self._client: SSHClient | None = None
        self._root_dir: str = root_dir

    def connect(self):

        if self._client is not None:
            self._client.close()

        self._client = SSHClient()
        self._client.set_missing_host_key_policy(paramiko.client.WarningPolicy)

        try:
            private_key = paramiko.rsakey.RSAKey(filename=self._ssh_key)
        except SSHException:
            private_key = paramiko.ed25519key.Ed25519Key(filename=self._ssh_key)
        except FileNotFoundError:
            private_key = None

        self._client.connect(
            hostname=self._hostname,
            username=self._username,
            password=self._password,
            pkey=private_key,
            look_for_keys=self._use_system_keys,
        )

    def test_connection(self):
        self.connect()
        self._client.close()

    @classmethod
    def load_by_uuid(cls, unique_id: str):

        unique_id = uuid.UUID(unique_id)

        config = TOMLConfiguration(
            Path(VariableLibrary().get_variable("paths.remote_directory"))
            / (str(unique_id) + ".toml"),
            create_if_not_exists=False,
        )

        if not config.is_valid():
            raise FileNotFoundError(
                f"The remote with UUID '{str(unique_id)}' could not be found!"
            )

        cls = cls(
            name=config["name"],
            unique_id=unique_id,
            protocol=Protocol.from_name(config["protocol"]),
            hostname=config["hostname"],
            username=config["username"],
            password=config["password"] if config["password"] != "" else None,
            ssh_key=Path(config["ssh_key"]).expanduser().absolute()
            if config["ssh_key"] != ""
            else None,
            use_system_keys=config["use_system_keys"],
            root_dir=config["root_dir"],
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
            except FileNotFoundError:
                break

        raise FileNotFoundError(
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
    ):

        _protocol = Protocol.from_name(protocol)

        if protocol is None:
            raise NameError(f"The protocol '{protocol}' is not supported!")

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
            password=password,
            ssh_key=Path(ssh_key).expanduser().absolute() if ssh_key else None,
            use_system_keys=use_system_keys,
            root_dir=root_dir,
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
                "password": cls._password if cls._password else "",
                "ssh_key": str(cls._ssh_key) if cls._ssh_key else "",
                "use_system_keys": cls._use_system_keys,
                "root_dir": cls._root_dir,
            }
        )
        cls._config.prepend_no_edit_warning()

        cls.test_connection()

        return cls
