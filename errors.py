from abc import ABC


class Error(Exception):
    pass


class UserAlreadyInDataBase(Error):
    pass


class UserIsNotInDataBase(Error):
    pass


class AutoAdditionToDatabaseIsImmposible(Error):
    pass
