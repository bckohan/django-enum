from django.urls import path
try:
    from .filterfield_howto import TextChoicesExampleFilterViewSet
    from .filterset_howto import (
        TextChoicesExampleFilterViewSet as TextChoicesExampleFilterSetViewSet
    )

    app_name = "howto"

    urlpatterns = [
        path(
            'filterfield/',
            TextChoicesExampleFilterViewSet.as_view(),
            name='filterfield'
        ),
        path(
            'filterset/',
            TextChoicesExampleFilterSetViewSet.as_view(),
            name='filterset'
        ),
    ]
except ImportError:
    urlpatterns = []
