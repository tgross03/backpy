from enum import Enum as PyEnum


class Enum(PyEnum):

    @classmethod
    def values(cls):
        return list(cls.__members__.values())

    @classmethod
    def has_member(cls, member: str):
        return member in cls.__members__
