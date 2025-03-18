from decimal import Decimal
from enum import Enum
from django.db import models
from django_enum import EnumField


class MixedValueEnum(Enum):

    NONE = None
    VAL1 = 1
    VAL2 = '2.0'
    VAL3 = 3.0
    VAL4 = Decimal('4.5')


class MixedValueExample(models.Model):

    # Since None is an enumeration value, EnumField will automatically set
    # null=True on these model fields.

    # column will be a CharField
    eccentric_str = EnumField(MixedValueEnum)

    # column will be a FloatField
    eccentric_float = EnumField(MixedValueEnum, primitive=float)
