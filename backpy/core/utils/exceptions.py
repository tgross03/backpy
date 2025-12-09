class InvalidBackupError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class InvalidBackupSpaceError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class UnsupportedCompressionAlgorithmError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class UnsupportedProtocolError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class InvalidRemoteError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class InvalidScheduleError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class InvalidChecksumError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class InvalidTOMLConfigurationError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class InvalidInputError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class BackupLimitExceededError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
