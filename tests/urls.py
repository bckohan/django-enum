from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("djenum/", include("tests.djenum.urls")),
    path("", include("tests.converters.urls")),
]

if "tests.enum_prop" in settings.INSTALLED_APPS:  # pragma: no cover
    urlpatterns.append(path("enum_prop/", include("tests.enum_prop.urls")))

if "tests.dataclass" in settings.INSTALLED_APPS:  # pragma: no cover
    urlpatterns.append(path("dataclass/", include("tests.dataclass.urls")))
