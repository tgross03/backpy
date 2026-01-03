import subprocess
import uuid
from pathlib import Path

from mergedeep import merge
from mysql.connector.connection import MySQLConnection

from backpy import TOMLConfiguration, VariableLibrary
from backpy.core.encryption.password import decrypt, encrypt

__all__ = ["MySQLServer", "test_mysqldump"]

from backpy.core.utils.exceptions import InvalidDatabaseException


def test_mysqldump(verbosity_level: int = 1) -> bool:
    try:
        result = subprocess.run(
            ["mysqldump --version"],
            shell=True,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        if verbosity_level > 0:
            print(
                "'mysqldump' command not found or not working properly. Return code:",
                e.returncode,
            )
        return False

    if verbosity_level > 1:
        print("Found 'mysqldump' command with version info:", result.stdout)

    return True


class MySQLServer:
    def __init__(
        self,
        unique_id: str | uuid.UUID,
        name: str,
        hostname: str,
        port: int,
        user: str,
        token: str,
        database: str | None,
    ):
        self._uuid: uuid.UUID = (
            unique_id if isinstance(unique_id, uuid.UUID) else uuid.UUID(unique_id)
        )
        self._name: str = name
        self._hostname: str = hostname
        self._port: int = port
        self._user: str = user
        self._token: str = token
        self._database: str = database if database is not None else ""
        self._connection = None

        self._config: TOMLConfiguration = TOMLConfiguration(
            path=Path(VariableLibrary.get_variable("database.mysql_directory"))
            / f"{self._uuid}.toml",
            create_if_not_exists=True,
        )

    def update_config(self) -> None:

        current_content = self._config.as_dict()

        content = {
            "uuid": str(self._uuid),
            "name": self._name,
            "hostname": self._hostname,
            "port": self._port,
            "user": self._user,
            "token": self._token,
            "database": self._database,
        }

        self._config.dump_dict(content=dict(merge({}, current_content, content)))

    def connect(self, verbosity_level: int = 1) -> MySQLConnection:
        if self.is_connected():
            self.disconnect()

        if verbosity_level > 1:
            print(
                f"Connecting to MySQL server at {self._hostname}:{self._port} "
                f"as user '{self._user}'..."
            )

        self._connection = MySQLConnection(
            host=self._hostname,
            port=self._port,
            user=self._user,
            password=decrypt(self._token),
            database=self._database,
        )
        return self._connection

    def disconnect(self, verbosity_level: int = 1) -> None:
        if self.is_connected():
            print(
                f"Closing MySQL connection for server '{self._hostname}:{self._port}'..."
            )
            self._connection.close()

        if verbosity_level > 1:
            print(f"Disconnected from MySQL server '{self._hostname}:{self._port}'.")

        self._connection = None

    def test_connection(self, verbosity_level: int = 1) -> bool:
        try:
            self.connect(verbosity_level=verbosity_level)
        except Exception:
            return False

        if not self._connection.is_connected or self._connection is None:
            return False

        self.disconnect(verbosity_level=verbosity_level)
        return True

    def create_dump(
        self,
        output_directory: Path | str,
        databases: list[str],
        tables: list[str],
        include_data: bool,
        include_routines: bool,
        verbosity_level: int = 1,
    ) -> None:

        output_directory = (
            Path(output_directory)
            if isinstance(output_directory, str)
            else output_directory
        )

    #####################
    #    CLASSMETHODS   #
    #####################

    @classmethod
    def load_by_name(cls, name: str) -> "MySQLServer":

        for tomlf in Path(
            VariableLibrary.get_variable("database.mysql_directory")
        ).rglob("*.toml"):
            config = TOMLConfiguration(path=tomlf, create_if_not_exists=False)

            if not config.is_valid():
                continue

            if name != config["name"]:
                continue

            try:
                return MySQLServer.load_by_uuid(unique_id=config["uuid"])
            except InvalidDatabaseException:
                break

        raise InvalidDatabaseException(
            f"There is no valid MySQL server present" f"with the name '{name}'."
        )

    @classmethod
    def load_by_uuid(cls, unique_id: str | uuid.UUID) -> "MySQLServer":

        unique_id = uuid.UUID(unique_id) if isinstance(unique_id, str) else unique_id
        config = TOMLConfiguration(
            path=Path(VariableLibrary.get_variable("database.mysql_directory"))
            / f"{unique_id}.toml",
            create_if_not_exists=False,
        )

        if not config.is_valid():
            raise InvalidDatabaseException(
                f"The MySQL server with UUID '{unique_id}' " "could not be found."
            )

        instance = cls(
            unique_id=unique_id,
            name=config["name"],
            hostname=config["hostname"],
            port=config["port"],
            user=config["user"],
            token=config["token"],
            database=config["database"],
        )

        return instance

    @classmethod
    def new(
        cls,
        name: str,
        user: str,
        password: str,
        hostname: str = "127.0.0.1",
        port: int = 3306,
        database: str | None = None,
        test_connection: bool = True,
        verbosity_level: int = 1,
    ) -> "MySQLServer":

        unique_id = uuid.uuid4()

        instance = cls(
            unique_id=unique_id,
            name=name,
            hostname=hostname,
            port=port,
            user=user,
            token=encrypt(password),
            database=database,
        )

        if test_connection and not instance.test_connection(
            verbosity_level=verbosity_level
        ):
            raise ConnectionError(
                f"Could not connect to MySQL server at {hostname}:{port} "
                f"as user '{user}'."
            )

        return instance

    #####################
    #       GETTER      #
    #####################

    def is_connected(self) -> bool:
        return self._connection is not None and self._connection.is_connected

    def get_connection(self) -> MySQLConnection | None:
        return self._connection

    def get_hostname(self) -> str:
        return self._hostname

    def get_port(self) -> int:
        return self._port

    def get_user(self) -> str:
        return self._user

    def get_uuid(self) -> uuid.UUID:
        return self._uuid

    def get_database(self) -> str:
        return self._database
