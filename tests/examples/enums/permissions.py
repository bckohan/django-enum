# flake8: noqa
from enum import IntFlag


class Permissions(IntFlag):

    READ    = 1 << 0
    WRITE   = 1 << 1
    EXECUTE = 1 << 2
