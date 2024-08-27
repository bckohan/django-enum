from django.urls import include, path

from tests.djenum.models import EnumTester
from tests.djenum.views import (
    EnumTesterCreateView,
    EnumTesterDeleteView,
    EnumTesterDetailView,
    EnumTesterListView,
    EnumTesterUpdateView,
)

app_name = "tests_djenum"


urlpatterns = [
    path("enum/<int:pk>", EnumTesterDetailView.as_view(), name="enum-detail"),
    path("enum/list/", EnumTesterListView.as_view(), name="enum-list"),
    path("enum/add/", EnumTesterCreateView.as_view(), name="enum-add"),
    path("enum/<int:pk>/", EnumTesterUpdateView.as_view(), name="enum-update"),
    path("enum/<int:pk>/delete/", EnumTesterDeleteView.as_view(), name="enum-delete"),
]


try:
    from rest_framework import routers

    from tests.djenum.views import DRFView

    router = routers.DefaultRouter()
    router.register(r"enumtesters", DRFView)
    urlpatterns.append(path("drf/", include(router.urls)))

except ImportError:  # pragma: no cover
    pass


try:
    from django_filters.views import FilterView

    from tests.djenum.views import EnumTesterFilterViewSet

    urlpatterns.extend(
        [
            path(
                "enum/filter/",
                FilterView.as_view(
                    model=EnumTester,
                    filterset_fields="__all__",
                    template_name="enumtester_list.html",
                ),
                name="enum-filter",
            ),
            path(
                "enum/filter/symmetric/",
                EnumTesterFilterViewSet.as_view(),
                name="enum-filter-symmetric",
            ),
        ]
    )
except ImportError:  # pragma: no cover
    pass
