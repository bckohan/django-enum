from django.conf import settings
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("djenum/", include("tests.djenum.urls")),
    path("converters/", include("tests.converters.urls")),
    path("", include("tests.examples.urls")),
    path("howto/", include("tests.examples.urls_howto")),
    path("howto/forms/", include("tests.examples.urls_forms")),
]

if "tests.enum_prop" in settings.INSTALLED_APPS:  # pragma: no cover
    urlpatterns.append(path("enum_prop/", include("tests.enum_prop.urls")))
