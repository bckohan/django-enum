from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('djenum/', include('django_enum.tests.djenum.urls'))
]

if 'django_enum.tests.enum_prop' in settings.INSTALLED_APPS:  # pragma: no cover
    urlpatterns.append(
        path('enum_prop/', include('django_enum.tests.enum_prop.urls'))
    )

