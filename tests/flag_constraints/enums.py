"""
"strict" -> error is raised  [default for Flag]
"conform" -> extra bits are discarded
"eject" -> lose flag status [default for IntFlag]
"keep" -> keep flag status and all bits
"""

import sys

if sys.version_info >= (3, 11):
    from enum import CONFORM, EJECT, KEEP, STRICT, Flag, IntFlag

    class KeepFlagEnum(IntFlag, boundary=KEEP):
        VAL1 = 2**12  # 4096
        VAL2 = 2**13  # 8192
        VAL3 = 2**14  # 16384

    class EjectFlagEnum(IntFlag, boundary=EJECT):
        VAL1 = 2**12
        VAL2 = 2**13
        VAL3 = 2**14

    class StrictFlagEnum(Flag, boundary=STRICT):
        VAL1 = 2**12
        VAL2 = 2**13
        VAL3 = 2**14

    class ConformFlagEnum(IntFlag, boundary=CONFORM):
        VAL1 = 2**12
        VAL2 = 2**13
        VAL3 = 2**14
