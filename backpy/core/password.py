from pathlib import Path

from cryptography.fernet import Fernet

import backpy


def _get_fernet() -> Fernet:
    key_file = Path(backpy.__file__).parent.parent / ".config/.key"

    if key_file.is_file():

        if oct(key_file.stat().st_mode & 0o777) != 0o600:
            key_file.chmod(mode=0o600)

        with open(key_file, "r") as f:
            key = f.readline().encode()
    else:
        key_file.touch(mode=0o600)

        key = Fernet.generate_key()

        with open(key_file, "w") as f:
            f.write(key.decode())

    return Fernet(key=key)


def encrypt(password: str | None) -> str | None:

    if password is None:
        return None

    return _get_fernet().encrypt(data=password.encode()).decode()


def decrypt(token: str | None) -> str | None:
    if token is None:
        return None

    return _get_fernet().decrypt(token=token.encode()).decode()
