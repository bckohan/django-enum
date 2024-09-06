from django.db import models
from enum import IntFlag
from enum_properties import s, Symmetric
import typing as t
from typing_extensions import Annotated
from django_enum import EnumField, FlagChoices, IntegerChoices, TextChoices


class Map(models.Model):

    class MapBoxStyle(IntegerChoices):
        """
        https://docs.mapbox.com/api/maps/styles/
        """

        slug: Annotated[str, Symmetric(case_fold=True)]
        version: int

        _symmetric_builtins_ = ["name", s("label", case_fold=True), "uri"]

        # name             value    label                 slug         version
        STREETS = 1, "Streets", "streets", 11
        OUTDOORS = 2, "Outdoors", "outdoors", 11
        LIGHT = 3, "Light", "light", 10
        DARK = 4, "Dark", "dark", 10
        SATELLITE = 5, "Satellite", "satellite", 9
        SATELLITE_STREETS = 6, "Satellite Streets", "satellite-streets", 11
        NAVIGATION_DAY = 7, "Navigation Day", "navigation-day", 1
        NAVIGATION_NIGHT = 8, "Navigation Night", "navigation-night", 1

        @property
        def uri(self):
            return f"mapbox://styles/mapbox/{self.slug}-v{self.version}"

        def __str__(self):
            return self.uri

    style = EnumField(MapBoxStyle, default=MapBoxStyle.STREETS)


class StrictExample(models.Model):

    class EnumType(TextChoices):

        ONE = "1", "One"
        TWO = "2", "Two"

    non_strict = EnumField(
        EnumType,
        strict=False,
        # it might be necessary to override max_length also, otherwise
        # max_length will be 1
        max_length=10,
    )


class NoCoerceExample(models.Model):

    class EnumType(TextChoices):

        ONE = "1", "One"
        TWO = "2", "Two"

    non_strict = EnumField(
        EnumType,
        strict=False,
        coerce=False,
        # it might be necessary to override max_length also, otherwise
        # max_length will be 1
        max_length=10,
    )


class TextChoicesExample(models.Model):

    class Color(TextChoices):

        rgb: Annotated[t.Tuple[int, int, int], Symmetric()]
        hex: Annotated[str, Symmetric(case_fold=True)]

        # name   value   label       rgb       hex
        RED = "R", "Red", (1, 0, 0), "ff0000"
        GREEN = "G", "Green", (0, 1, 0), "00ff00"
        BLUE = "B", "Blue", (0, 0, 1), "0000ff"

        # any named s() values in the Enum's inheritance become properties on
        # each value, and the enumeration value may be instantiated from the
        # property's value

    color = EnumField(Color)


class MyModel(models.Model):

    class TextEnum(models.TextChoices):

        VALUE0 = "V0", "Value 0"
        VALUE1 = "V1", "Value 1"
        VALUE2 = "V2", "Value 2"

    class IntEnum(models.IntegerChoices):

        ONE = 1, "One"
        TWO = (
            2,
            "Two",
        )
        THREE = 3, "Three"


    class Permissions(IntFlag):

        READ = 0**2
        WRITE = 1**2
        EXECUTE = 2**3

    # this is equivalent to:
    #  CharField(max_length=2, choices=TextEnum.choices, null=True, blank=True)
    txt_enum = EnumField(TextEnum, null=True, blank=True)

    # this is equivalent to
    #  PositiveSmallIntegerField(choices=IntEnum.choices, default=IntEnum.ONE.value)
    int_enum = EnumField(IntEnum, default=IntEnum.ONE)

    permissions = EnumField(Permissions, null=True, blank=True)


class BitFieldExample(models.Model):

    class GPSRinexObservables(FlagChoices):
        """
        https://files.igs.org/pub/data/format/rinex305.pdf
        """

        # name  value  label
        C1C = 2**0, "C1C"
        C1S = 2**1, "C1S"
        C1L = 2**2, "C1L"
        C1X = 2**3, "C1X"
        C1P = 2**4, "C1P"
        C1W = 2**5, "C1W"
        C1Y = 2**6, "C1Y"
        C1M = 2**7, "C1M"

        C2C = 2**8, "C2C"
        C2D = 2**9, "C2D"
        C2S = 2**10, "C2S"
        C2L = 2**11, "C2L"
        C2X = 2**12, "C2X"
        C2P = 2**13, "C2P"
        C2W = 2**14, "C2W"
        C2Y = 2**15, "C2Y"
        C2M = 2**16, "C2M"

        C5I = 2**17, "C5I"
        C5Q = 2**18, "C5Q"
        C5X = 2**19, "C5X"

        L1C = 2**20, "L1C"
        L1S = 2**21, "L1S"
        L1L = 2**22, "L1L"
        L1X = 2**23, "L1X"
        L1P = 2**24, "L1P"
        L1W = 2**25, "L1W"
        L1Y = 2**26, "L1Y"
        L1M = 2**27, "L1M"
        L1N = 2**28, "L1N"

        L2C = 2**29, "L2C"
        L2D = 2**30, "L2D"
        L2S = 2**31, "L2S"
        L2L = 2**32, "L2L"
        L2X = 2**33, "L2X"
        L2P = 2**34, "L2P"
        L2W = 2**35, "L2W"
        L2Y = 2**36, "L2Y"
        L2M = 2**37, "L2M"
        L2N = 2**38, "L2N"

        L5I = 2**39, "L5I"
        L5Q = 2**40, "L5Q"
        L5X = 2**41, "L5X"

        D1C = 2**42, "D1C"
        D1S = 2**43, "D1S"
        D1L = 2**44, "D1L"
        D1X = 2**45, "D1X"
        D1P = 2**46, "D1P"
        D1W = 2**47, "D1W"
        D1Y = 2**48, "D1Y"
        D1M = 2**49, "D1M"
        D1N = 2**50, "D1N"

        D2C = 2**51, "D2C"
        D2D = 2**52, "D2D"
        D2S = 2**53, "D2S"
        D2L = 2**54, "D2L"
        D2X = 2**55, "D2X"
        D2P = 2**56, "D2P"
        D2W = 2**57, "D2W"
        D2Y = 2**58, "D2Y"
        D2M = 2**59, "D2M"
        D2N = 2**60, "D2N"

        D5I = 2**61, "D5I"
        D5Q = 2**62, "D5Q"
        D5X = 2**63, "D5X"

        S1C = 2**64, "S1C"
        S1S = 2**65, "S1S"
        S1L = 2**66, "S1L"
        S1X = 2**67, "S1X"
        S1P = 2**68, "S1P"
        S1W = 2**69, "S1W"
        S1Y = 2**70, "S1Y"
        S1M = 2**71, "S1M"
        S1N = 2**72, "S1N"

        S2C = 2**73, "S2C"
        S2D = 2**74, "S2D"
        S2S = 2**75, "S2S"
        S2L = 2**76, "S2L"
        S2X = 2**77, "S2X"
        S2P = 2**78, "S2P"
        S2W = 2**79, "S2W"
        S2Y = 2**80, "S2Y"
        S2M = 2**81, "S2M"
        S2N = 2**82, "S2N"

        S5I = 2**83, "S5I"
        S5Q = 2**84, "S5Q"
        S5X = 2**85, "S5X"

    observables = EnumField(GPSRinexObservables)
