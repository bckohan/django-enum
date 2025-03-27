from django.urls import include, path

from tests.enum_prop.models import EnumTester
from tests.enum_prop.views import (
    EnumTesterCreateView,
    EnumTesterDeleteView,
    EnumTesterDetailView,
    EnumTesterListView,
    EnumTesterUpdateView,
    FlagTesterCreateView,
    FlagTesterDeleteView,
    FlagTesterDetailView,
    FlagTesterListView,
    FlagTesterUpdateView,
)

app_name = "tests_enum_prop"

urlpatterns = [
    path("enum/<int:pk>", EnumTesterDetailView.as_view(), name="enum-detail"),
    path("enum/list/", EnumTesterListView.as_view(), name="enum-list"),
    path("enum/add/", EnumTesterCreateView.as_view(), name="enum-add"),
    path("enum/<int:pk>/", EnumTesterUpdateView.as_view(), name="enum-update"),
    path("enum/<int:pk>/delete/", EnumTesterDeleteView.as_view(), name="enum-delete"),
    path("flag/<int:pk>", FlagTesterDetailView.as_view(), name="flag-detail"),
    path("flag/list/", FlagTesterListView.as_view(), name="flag-list"),
    path("flag/add/", FlagTesterCreateView.as_view(), name="flag-add"),
    path("flag/<int:pk>/", FlagTesterUpdateView.as_view(), name="flag-update"),
    path("flag/<int:pk>/delete/", FlagTesterDeleteView.as_view(), name="flag-delete"),
]

try:
    from rest_framework import routers

    from tests.enum_prop.views import DRFView, DRFFlagView

    router = routers.DefaultRouter()
    router.register(r"enumtesters", DRFView)
    router.register(r"flagtesters", DRFFlagView)
    urlpatterns.append(path("drf/", include(router.urls)))

except ImportError:  # pragma: no cover
    pass

try:
    from django_filters.views import FilterView

    from tests.enum_prop.views import (
        EnumTesterPropFilterViewSet,
        EnumTesterFilterExcludeViewSet,
        EnumTesterPropMultipleFilterViewSet,
        EnumTesterPropMultipleExcludeFilterViewSet,
        FlagTesterFilterViewSet,
        FlagTesterFilterExcludeViewSet,
        FlagTesterFilterConjoinedViewSet,
        FlagTesterFilterConjoinedExcludeViewSet,
    )

    urlpatterns.extend(
        [
            path(
                "enum/filter/symmetric/",
                EnumTesterPropFilterViewSet.as_view(),
                name="enum-filter-symmetric",
            ),
            path(
                "enum/filter/symmetric/exclude",
                EnumTesterFilterExcludeViewSet.as_view(),
                name="enum-filter-symmetric-exclude",
            ),
            path(
                "enum/filter/multiple/",
                EnumTesterPropMultipleFilterViewSet.as_view(),
                name="enum-filter-multiple",
            ),
            path(
                "enum/filter/multiple/exclude",
                EnumTesterPropMultipleExcludeFilterViewSet.as_view(),
                name="enum-filter-multiple-exclude",
            ),
            path(
                "flag/filter/",
                FlagTesterFilterViewSet.as_view(),
                name="flag-filter-symmetric",
            ),
            path(
                "flag/filter/exclude",
                FlagTesterFilterExcludeViewSet.as_view(),
                name="flag-filter-exclude-symmetric",
            ),
            path(
                "flag/filter/conjoined",
                FlagTesterFilterConjoinedViewSet.as_view(),
                name="flag-filter-conjoined-symmetric",
            ),
            path(
                "flag/filter/conjoined/exclude",
                FlagTesterFilterConjoinedExcludeViewSet.as_view(),
                name="flag-filter-conjoined-exclude-symmetric",
            ),
        ]
    )
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    pass
