from enum import Enum
from django.db import models
from django_enum import EnumField


class ExternalChoices(models.Model):

    class TextEnum(str, Enum):

        VALUE0 = 'V0'
        VALUE1 = 'V1'
        VALUE2 = 'V2'

    # choices will default to (value, name) pairs
    txt_enum1 = EnumField(TextEnum)

    # you can also override choices
    txt_enum2 = EnumField(
        TextEnum,
        choices=[(en.value, en.name.title()) for en in TextEnum]
    )
