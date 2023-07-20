from enum import IntFlag

enums = []

for num_flags in range(0, 63):
    enums.append(
        IntFlag(
            f'Flags{num_flags:03d}',
            {
                f'FLG_{flg}': 2**flg
                for flg in range(0, num_flags+1)
            }
        )
    )
