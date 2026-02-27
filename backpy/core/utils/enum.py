from enum import Enum as PyEnum
from enum import EnumMeta as PyEnumMeta


# Based on the concept from https://stackoverflow.com/a/24717640
class EnumMeta(PyEnumMeta):
    def __getitem__(self, item: str):
        try:
            return super().__getitem__(item)
        except KeyError:
            try:
                return super().__getitem__(item.upper())
            except KeyError:
                raise KeyError(item)


class Enum(PyEnum, metaclass=EnumMeta):
    @classmethod
    def names(cls):
        return list(cls.__members__.keys())

    @classmethod
    def values(cls):
        return list(cls.__members__.values())

    @classmethod
    def has_member(cls, member: str):
        return member in cls.__members__
