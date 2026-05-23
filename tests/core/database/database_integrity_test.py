import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

from backpy.core.database.mysql import MySQLServer

_DATA_URL = "https://github.com/datacharmer/test_db/releases/download/v1.0.7/test_db-1.0.7.tar.gz"
_LOCAL_DB_CREDENTIALS = {
    "username": "test_user",
    "password": "test123",
}


def setup_database(temporary_path: Path) -> Path:

    outdir = temporary_path / _DATA_URL.split("/")[-1].split("-")[0]

    server = MySQLServer.new(
        name="test_db",
        user=_LOCAL_DB_CREDENTIALS["username"],
        password=_LOCAL_DB_CREDENTIALS["password"],
    )
    connection = server.connect()
    cursor = connection.cursor()

    exists_command = """
    SELECT SCHEMA_NAME
    FROM INFORMATION_SCHEMA.SCHEMATA
    WHERE SCHEMA_NAME = 'employees'
    """

    cursor.execute(exists_command)
    db_exists = len(cursor.fetchall())

    if outdir.exists() and db_exists:
        return outdir

    try:
        subprocess.run(
            f"wget --no-verbose {_DATA_URL}",
            check=True,
            cwd=str(temporary_path),
            shell=True,
            stdout=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        try:
            subprocess.run(
                f"curl {_DATA_URL} > {_DATA_URL.split('/')[-1]}",
                check=True,
                cwd=str(temporary_path),
                shell=True,
                stdout=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            raise RuntimeError(
                "Either there is a problem with the URL or neither curl nor wget are not installed."
            )

    archive_path = temporary_path / _DATA_URL.split("/")[-1]

    subprocess.run(
        f"tar -xzf {archive_path.name}", check=True, shell=True, cwd=str(temporary_path)
    )
    archive_path.unlink()

    cursor.execute(exists_command)
    db_exists = len(cursor.fetchall())

    if db_exists:
        return outdir

    subprocess.run(
        f"mysql -t -u {_LOCAL_DB_CREDENTIALS["username"]} "
        f"-p{_LOCAL_DB_CREDENTIALS["password"]} < employees.sql",
        cwd=outdir,
        shell=True,
        check=True,
    )

    return outdir


def test_database_integrity(tmp_path: Path):
    test_dir = setup_database(temporary_path=tmp_path)
    print(test_dir)
    print(test_dir.exists())
    print(tmp_path)
    print(tmp_path.exists())

    print(
        subprocess.run(
            "ls -la", shell=True, cwd=tmp_path, capture_output=True, text=True
        ).stdout
    )

    output = subprocess.run(
        f"mysql -t -u {_LOCAL_DB_CREDENTIALS["username"]} "
        f"-p{_LOCAL_DB_CREDENTIALS["password"]} < test_employees_sha.sql",
        cwd=test_dir,
        capture_output=True,
        text=True,
        shell=True,
    ).stdout.split("\n")

    expected = dict()
    found = dict()
    match = dict()

    output_clean = []
    for row in output:
        if row.startswith("+"):
            continue
        mod_row = []
        for col in row.strip().split("|"):
            if col == "":
                continue
            mod_row.append(col.strip())

        if len(mod_row) < 3:
            continue

        output_clean.append(mod_row)

    table_section = None
    for row in output_clean:
        if (
            row[1].startswith("expected")
            and row[2].startswith("expected")
            and table_section != "expected"
        ):
            table_section = "expected"
            continue
        elif (
            row[1].startswith("found")
            and row[2].startswith("found")
            and table_section != "found"
        ):
            table_section = "found"
            continue
        elif (
            row[1].endswith("match")
            and row[2].endswith("match")
            and table_section != "match"
        ):
            table_section = "match"
            continue

        match table_section:
            case "expected":
                expected[row[0]] = [int(row[1]), row[2]]
            case "found":
                found[row[0]] = [int(row[1]), row[2]]
            case "match":
                match[row[0]] = [row[1].upper() == "OK", row[2].upper() == "OK"]

    all_match = bool(np.all(list(match.values())))

    record_df = pd.DataFrame(
        {
            "table_name": list(found.keys()),
            "expected_records": np.array(list(expected.values()))[:, 0].tolist(),
            "found_records": np.array(list(found.values()))[:, 0].tolist(),
            "records_match": np.array(list(match.values()))[:, 0].tolist(),
        }
    )

    crc_df = pd.DataFrame(
        {
            "table_name": list(found.keys()),
            "expected_crc": np.array(list(expected.values()))[:, 1].tolist(),
            "found_crc": np.array(list(found.values()))[:, 1].tolist(),
            "crc_match": np.array(list(match.values()))[:, 1].tolist(),
        }
    )

    if not all_match:
        raise AssertionError(
            "The Database Integrity test failed!\n\n"
            "-----------------------------------\n"
            "----------- TEST OUTPUT -----------\n"
            f"-----------------------------------\n\n{record_df}\n\n{crc_df}"
        )

    print(
        "-----------------------------------\n"
        "----------- TEST OUTPUT -----------\n"
        f"-----------------------------------\n\n{record_df}\n\n{crc_df}"
    )
