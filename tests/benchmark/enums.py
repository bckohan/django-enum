from enum import IntFlag

enums = []

for num_flags in range(0, 63):
    enums.append(
        IntFlag(
            f"Flags{num_flags:03d}",
            {f"FLG_{flg}": 2**flg for flg in range(0, num_flags + 1)},
        )
    )


class Index16(IntFlag):
    FLG_0 = 1
    FLG_1 = 2
    FLG_2 = 4
    FLG_3 = 8
    FLG_4 = 16
    FLG_5 = 32
    FLG_6 = 64
    FLG_7 = 128
    FLG_8 = 256
    FLG_9 = 512
    FLG_10 = 1024
    FLG_11 = 2048
    FLG_12 = 4096
    FLG_13 = 8192
    FLG_14 = 16384
    FLG_15 = 32768
