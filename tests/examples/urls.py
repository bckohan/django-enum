from enum import IntEnum

from django.http import HttpResponse
from django.urls import path

from django_enum.urls import register_enum_converter


class Enum1(IntEnum):
    A = 1
    B = 2


register_enum_converter(Enum1)
register_enum_converter(Enum1, type_name="Enum1ByName", prop="name")


def enum_converter_view(request, enum):
    assert isinstance(enum, Enum1)
    return HttpResponse(status=200, content=f"{enum=}")


app_name = "examples"

urlpatterns = [
    # this will match paths /1 and /2
    path("<Enum1:enum>", enum_converter_view, name="enum_default"),

    # this will match paths /A and /B
    path("<Enum1ByName:enum>", enum_converter_view, name="enum_by_name"),
]
