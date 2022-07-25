from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('enum_prop/', include('django_enum.tests.enum_prop.urls'))
]
