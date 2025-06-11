import datetime


def get_local_timezone() -> datetime.tzinfo:
    return datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo


class TimeObject:
    def __init__(self, dt: datetime.datetime):
        self._datetime: datetime.datetime = dt

    def isoformat(self) -> str:
        return self._datetime.isoformat()

    def printformat(self) -> str:
        return self._datetime.strftime("%Y-%m-%d %H:%M:%S.%f")

    @classmethod
    def utcnow(cls) -> "TimeObject":
        return cls(datetime.datetime.now(datetime.UTC))

    @classmethod
    def localnow(cls) -> "TimeObject":
        return cls(datetime.datetime.now().astimezone(get_local_timezone()))

    @classmethod
    def fromisoformat(cls, string: str) -> "TimeObject":
        return cls(datetime.datetime.fromisoformat(string))
