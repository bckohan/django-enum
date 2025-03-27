from django.urls import include, path

from tests.djenum.models import EnumTester
from tests.djenum.views import (
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

app_name = "tests_djenum"


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

    from tests.djenum.views import DRFView, DRFFlagView

    router = routers.DefaultRouter()
    router.register(r"enumtesters", DRFView)
    router.register(r"flagtesters", DRFFlagView)
    urlpatterns.append(path("drf/", include(router.urls)))

except ImportError:  # pragma: no cover
    pass


try:
    from django_filters.views import FilterView

    from tests.djenum.views import (
        EnumTesterFilterViewSet,
        EnumTesterFilterExcludeViewSet,
        EnumTesterMultipleFilterViewSet,
        EnumTesterMultipleFilterExcludeViewSet,
        FlagTesterFilterViewSet,
        FlagTesterFilterExcludeViewSet,
        FlagTesterFilterConjoinedViewSet,
        FlagTesterFilterConjoinedExcludeViewSet,
    )

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
                "enum/filter/viewset/",
                EnumTesterFilterViewSet.as_view(),
                name="enum-filter-viewset",
            ),
            path(
                "enum/filter/viewset/exclude",
                EnumTesterFilterExcludeViewSet.as_view(),
                name="enum-filter-viewset-exclude",
            ),
            path(
                "enum/filter/multiple/",
                EnumTesterMultipleFilterViewSet.as_view(),
                name="enum-filter-multiple",
            ),
            path(
                "enum/filter/multiple/exclude/",
                EnumTesterMultipleFilterExcludeViewSet.as_view(),
                name="enum-filter-multiple-exclude",
            ),
            path("flag/filter/", FlagTesterFilterViewSet.as_view(), name="flag-filter"),
            path(
                "flag/filter/exclude",
                FlagTesterFilterExcludeViewSet.as_view(),
                name="flag-filter-exclude",
            ),
            path(
                "flag/filter/conjoined",
                FlagTesterFilterConjoinedViewSet.as_view(),
                name="flag-filter-conjoined",
            ),
            path(
                "flag/filter/conjoined/exclude",
                FlagTesterFilterConjoinedExcludeViewSet.as_view(),
                name="flag-filter-conjoined-exclude",
            ),
        ]
    )
except ImportError:  # pragma: no cover
    pass
