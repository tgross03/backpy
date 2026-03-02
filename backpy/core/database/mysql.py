import subprocess
import time
import uuid
from dataclasses import dataclass
from os import PathLike
from pathlib import Path

import numpy as np
from _mysql_connector import MySQLError
from mergedeep import merge
from mysql.connector.connection import MySQLConnection

from backpy import TOMLConfiguration, VariableLibrary
from backpy.core.encryption.password import decrypt, encrypt

__all__ = ["MySQLServer", "MySQLDump", "test_mysqldump"]

from backpy.core.utils.exceptions import InvalidDatabaseException

_DEFAULT_CONTEXT_VERBOSITY: int = 1

_PROTECTED_DATABASES = {"mysql", "performance_schema", "information_schema", "sys"}


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
        database: str | None = None,
    ):
        self._uuid: uuid.UUID = (
            unique_id if isinstance(unique_id, uuid.UUID) else uuid.UUID(unique_id)
        )
        self._name: str = name
        self._hostname: str = hostname
        self._port: int = port
        self._user: str = user
        self._token: str = token
        self._database: str | None = database
        self._connection: MySQLConnection | None = None

        self._context_managed: bool = False
        self._context_verbosity: int = _DEFAULT_CONTEXT_VERBOSITY

        self._config: TOMLConfiguration = TOMLConfiguration(
            path=Path(VariableLibrary.get_variable("database.mysql_directory"))
            / f"{self._uuid}.toml",
            create_if_not_exists=True,
        )

    def __call__(self, context_verbosity: int = 1, *args, **kwargs):
        self._context_verbosity = context_verbosity
        return self

    def __enter__(self) -> "MySQLServer":
        if self._context_managed:
            return self

        self._context_managed = True
        self.connect(verbosity_level=self._context_verbosity)
        return self

    def __exit__(self, *args, **kwargs) -> bool:
        if not self._context_managed:
            return False

        self._context_managed = False
        self.disconnect(verbosity_level=self._context_verbosity)
        self._context_verbosity = _DEFAULT_CONTEXT_VERBOSITY
        return False

    def update_config(self) -> None:

        current_content = self._config.asdict()

        content = {
            "uuid": str(self._uuid),
            "name": self._name,
            "hostname": self._hostname,
            "port": self._port,
            "user": self._user,
            "token": self._token,
            "database": self._database if self._database is not None else "",
        }

        self._config.dump(content=dict(merge({}, current_content, content)))

    def connect(self, verbosity_level: int = 1) -> MySQLConnection:
        if self.is_connected():
            self.disconnect(verbosity_level=verbosity_level)

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
            if verbosity_level > 1:
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

        if not self._connection.is_connected() or self._connection is None:
            return False

        self.disconnect(verbosity_level=verbosity_level)
        return True

    def get_connection_args(self) -> str:
        result = (
            f"--host={self._hostname} "
            f"--user={self._user} "
            f"--password={decrypt(self._token)} "
            f"--port={self._port} "
        )

        if self.get_database() is not None:
            result += f"--database={self._database} "

        return result

    def restore_dump(
        self, input_file: PathLike[str], dump: MySQLDump, verbosity_level: int = 1
    ) -> None:

        input_file = Path(input_file)

        if not input_file.exists():
            raise FileNotFoundError(
                f"The input file at {input_file} does not exist. "
                f"You can create it using the MySQLDump.create method."
            )

        if not self.test_connection():
            raise ConnectionError(
                "No connection could be established with the MySQL server."
            )

        database_was_none = self._database is None
        if len(dump.databases) == 1 and database_was_none:
            self._database = dump.databases[0]

        cmd = f"mysql {self.get_connection_args()} < {input_file}"

        start_time = time.time()

        # TODO: Add I/O size progress

        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
        )

        if database_was_none:
            self._database = None

        proc_time = time.time() - start_time

        if result.returncode != 0:

            error = ""

            if result.stdout != "":
                error += f"STDOUT -> {result.stdout}"

            if result.stderr != "":
                if error != "":
                    error += "\n\n"
                error += f"STDERR -> {result.stderr}"

            raise MySQLError(
                f"An error occurred during the restoring of the MySQL dump at {input_file}.\n\n"
                f"--- Reason (Code {result.returncode}) ---\n\n{error}"
            )

        if verbosity_level >= 1:
            print(
                f"Restored MySQL dump {input_file} to server '{self.get_hostname()}'. "
                f"Took {np.round(proc_time, 3)} seconds!"
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

            if not config.exists():
                continue

            if name != config["name"]:
                continue

            try:
                return MySQLServer.load_by_uuid(unique_id=config["uuid"])
            except InvalidDatabaseException:
                break

        raise InvalidDatabaseException(
            f"There is no valid MySQL server present with the name '{name}'."
        )

    @classmethod
    def load_by_uuid(cls, unique_id: str | uuid.UUID) -> "MySQLServer":

        unique_id = uuid.UUID(unique_id) if isinstance(unique_id, str) else unique_id
        config = TOMLConfiguration(
            path=Path(VariableLibrary.get_variable("database.mysql_directory"))
            / f"{unique_id}.toml",
            create_if_not_exists=False,
        )

        if not config.exists():
            raise InvalidDatabaseException(
                f"The MySQL server with UUID '{unique_id}' could not be found."
            )

        instance = cls(
            unique_id=unique_id,
            name=config["name"],
            hostname=config["hostname"],
            port=config["port"],
            user=config["user"],
            token=config["token"],
            database=config["database"] if config["database"] != "" else None,
        )

        return instance

    @classmethod
    def new(
        cls,
        name: str,
        user: str,
        password: str,
        hostname: str = "localhost",
        port: int = 3306,
        database: str | None = None,
        test_connection: bool = True,
        verbosity_level: int = 1,
    ) -> "MySQLServer":

        if hostname.lower() == "localhost":
            hostname = "127.0.0.1"

        try:
            MySQLServer.load_by_name(name=name)
            raise NameError("There is already a database with this name!")
        except InvalidDatabaseException:
            pass

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
            instance._config.get_path().unlink(missing_ok=True)
            raise ConnectionError(
                f"Could not connect to MySQL server at {hostname}:{port} "
                f"as user '{user}'."
            )

        instance.update_config()

        return instance

    #####################
    #       GETTER      #
    #####################

    def is_connected(self) -> bool:
        return self._connection is not None and self._connection.is_connected()

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

    def get_database(self) -> str | None:
        return self._database if self._database != "" else None


@dataclass
class MySQLDump:
    databases: list[str]
    tables: list[str]
    lock_tables: bool
    include_data: bool
    include_routines: bool
    include_events: bool
    include_triggers: bool
    force: bool
    exclude_databases: list[str]
    exclude_tables: list[str]
    exclude_table_data: list[str]
    flush_privileges: bool
    include_create_options: bool = True
    custom_condition: str | None = None

    def get_databases(self, server: MySQLServer) -> list[str]:
        with server() as s:
            cursor = s.get_connection().cursor()
            cursor.execute("SHOW DATABASES;")
            databases = [db[0] for db in cursor.fetchall()]

        databases = set(databases) - _PROTECTED_DATABASES - set(self.exclude_databases)

        if "*" in self.databases:
            return list(databases)

        return list(databases | set(self.databases))

    def get_tables(self, server: MySQLServer) -> list[str]:
        if len(self.databases) == 1 and len(self.tables) > 0:
            with server() as s:
                cursor = s.get_connection().cursor()
                cursor.execute(f"SHOW TABLES IN {self.databases[0]};")
                tables = set(
                    [f"{self.databases[0]}.{table[0]}" for table in cursor.fetchall()]
                )

            tables = tables - set(self.exclude_tables)

            return list(
                tables | set([f"{self.databases[0]}.{table}" for table in self.tables])
            )

        else:
            databases = self.get_databases(server=server)

            tables = set()
            with server() as s:
                cursor = s.get_connection().cursor()
                for database in databases:
                    cursor.execute(f"SHOW TABLES IN {database};")
                    tables = tables | set(
                        [f"{database}.{table[0]}" for table in cursor.fetchall()]
                    )

            tables = tables - set(self.exclude_tables)

            return list(tables)

    def get_triggers(self, server: MySQLServer) -> list[str]:
        tables = self.get_tables(server=server)

        triggers = set()
        with server() as s:
            for table in tables:
                database = table.split(".")[0]
                table_name = table.split(".")[1]
                cursor = s.get_connection().cursor()
                cursor.execute(f"SHOW TRIGGERS IN {database} LIKE '{table_name}';")
                triggers = triggers | set([trigger[0] for trigger in cursor.fetchall()])

        return list(triggers)

    def create(
        self,
        output_path: PathLike[str],
        server: MySQLServer,
        overwrite: bool,
        replace_data: bool,
        insert_ignore: bool,
        exclude_databases: list[str] | None = None,
        exclude_tables: list[str] | None = None,
        exclude_table_data: list[str] | None = None,
        verbosity_level: int = 1,
    ) -> None:

        exclude_databases = exclude_databases if exclude_databases is not None else []
        exclude_tables = exclude_tables if exclude_tables is not None else []
        exclude_table_data = (
            exclude_table_data if exclude_table_data is not None else []
        )

        exclude_databases.extend(self.exclude_databases)
        exclude_tables.extend(self.exclude_tables)
        exclude_table_data.extend(self.exclude_table_data)

        file_path = Path(output_path)

        if not server.test_connection():
            raise ConnectionError(
                "No connection could be established with the MySQL server."
            )

        cmd = f"mysqldump {server.get_connection_args()}"

        all_databases = "*" in self.databases

        if all_databases:
            cmd += "--all-databases "
        else:
            cmd += f"--databases {' '.join(self.databases)} "

        if (all_databases or len(self.databases) > 1) and len(self.tables) > 0:
            raise ValueError(
                "There cannot be specific tables given if "
                "multiple databases are included in one dump."
            )

        if not self.lock_tables:
            cmd += "--skip-lock-tables "

        if len(self.databases) == 1 and len(self.tables) > 0:
            cmd += f"--tables {' '.join(self.tables)} "

        if not self.include_create_options:
            cmd += "--skip-create-options "
            cmd += "--no-create-db "
            cmd += "--no-create-info "

        if not self.include_data:
            cmd += "--no-data "

        if self.include_routines:
            cmd += "--routines "

        if self.include_events:
            cmd += "--events "

        if not self.include_triggers:
            cmd += "--skip-triggers "

        if self.force:
            cmd += "--force "

        if (
            len(self.databases) == 1
            and not all_databases
            and self.databases[0] in self.exclude_databases
        ):
            raise ValueError("There has to be at least one database in the dump.")

        for database in exclude_databases:
            cmd += f"--ignore-database={database} "

        for table in exclude_tables:
            cmd += f"--ignore-table={table} "

        for table in exclude_table_data:
            cmd += f"--ignore-table-data={table} "

        if self.flush_privileges:
            cmd += "--flush-privileges "

        if replace_data:
            cmd += "--replace "

        if insert_ignore:
            cmd += "--insert-ignore "

        if self.custom_condition is not None:
            cmd += f'--where="{self.custom_condition}" '

        if verbosity_level > 3:
            cmd += "--verbose"

        start_time = time.time()

        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
        )

        # TODO: Add file size progress

        proc_time = time.time() - start_time

        exception = None
        text = None

        match result.returncode:
            case 1:
                exception = SyntaxError
                text = "A syntax error occurred during the MySQL dump."
            case 2:
                exception = MySQLError
                text = "A MySQL error occurred during the dump."
            case 3:
                exception = RuntimeError
                text = "A consistency error occurred during the dump."
            case 4:
                exception = MemoryError
                text = "A memory error occurred during the dump."
            case 5:
                exception = IOError
                text = "A file error occurred during the dump."
            case 6:
                exception = MySQLError
                text = "An illegal table error occurred during the dump."

        if verbosity_level > 2:
            print(f"Command STDOUT:\n\n{result.stdout}")
            print(f"Command STDERR:\n\n{result.stderr}")

        if result.returncode > 0 and exception is not None and text is not None:
            error = ""

            if "Error" in result.stdout:
                error += "\n\nSTDOUT -> Error" + result.stdout.split("Error")[1]

            if len(result.stderr) > 0:
                if error != "":
                    error += "\n\n"
                error += "STDERR -> " + result.stderr

            else:
                error += "\n\nTo show the full output of the execution, set the verbosity > 2!"
            raise exception(
                f"{text} (Code {result.returncode}).\n\n" f"--- Reason ---\n\n{error}"
            )

        if overwrite and file_path.exists():
            if verbosity_level > 1:
                print(f"Overwriting existing MySQL dump ... Deleting {file_path} ...")

            file_path.unlink(missing_ok=True)

        with open(file_path, "a") as file:
            file.write(result.stdout)

        if verbosity_level >= 1:
            print(
                f"Created MySQL dump to file {file_path}. "
                f"Took {np.round(proc_time, 3)} seconds!"
            )

        print(cmd)

    def asdict(self) -> dict:
        keys = [
            "databases",
            "tables",
            "lock_tables",
            "include_create_options",
            "include_data",
            "include_routines",
            "include_events",
            "include_triggers",
            "force",
            "exclude_databases",
            "exclude_tables",
            "exclude_table_data",
            "flush_privileges",
            "custom_condition",
        ]

        result = self.__dict__

        result_copy = result.copy()

        for key in result.keys():
            if key not in keys:
                del result_copy[key]

        return result_copy

    @classmethod
    def from_dict(cls, dictionary: dict) -> "MySQLDump":
        return cls(**dictionary)
