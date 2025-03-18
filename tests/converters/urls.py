from enum import IntEnum

from django.http import HttpResponse
from django.urls import path

from django_enum.urls import register_enum_converter
from tests.djenum.enums import Constants, DecimalEnum


class TestEnum(IntEnum):
    A = 1
    B = 2


register_enum_converter(TestEnum)
register_enum_converter(DecimalEnum, "decimal_enum")
register_enum_converter(Constants, prop="label")

record = []


def enum_converter_view(request, enum):
    record.append(enum)
    return HttpResponse(status=200)


urlpatterns = [
    path("<TestEnum:enum>", enum_converter_view, name="enum1_view"),
    path("<decimal_enum:enum>", enum_converter_view, name="decimal_enum_view"),
    path("<Constants:enum>", enum_converter_view, name="constants_view"),
]
