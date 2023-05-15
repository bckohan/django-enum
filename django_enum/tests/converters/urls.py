from enum import IntEnum

from django.http import HttpResponse
from django.urls import path
from django_enum import register_enum_converter
from django_enum.tests.djenum.enums import DecimalEnum


class Enum1(IntEnum):
    A = 1
    B = 2


register_enum_converter(Enum1)
register_enum_converter(DecimalEnum, 'decimal_enum')

record = []


def enum_converter_view(request, enum):
    record.append(enum)
    return HttpResponse(status=200)


urlpatterns = [
    path('<Enum1:enum>', enum_converter_view, name='enum1_view'),
    path('<decimal_enum:enum>', enum_converter_view, name='decimal_enum_view'),
]

