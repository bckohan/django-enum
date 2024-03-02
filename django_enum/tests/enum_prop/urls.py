try:
    from django.urls import include, path

    from django_enum.tests.enum_prop.models import EnumTester
    from django_enum.tests.enum_prop.views import (
        EnumTesterCreateView,
        EnumTesterDeleteView,
        EnumTesterDetailView,
        EnumTesterListView,
        EnumTesterUpdateView,
    )

    app_name = "django_enum_tests_enum_prop"

    urlpatterns = [
        path("enum/<int:pk>", EnumTesterDetailView.as_view(), name="enum-detail"),
        path("enum/list/", EnumTesterListView.as_view(), name="enum-list"),
        path("enum/add/", EnumTesterCreateView.as_view(), name="enum-add"),
        path("enum/<int:pk>/", EnumTesterUpdateView.as_view(), name="enum-update"),
        path(
            "enum/<int:pk>/delete/", EnumTesterDeleteView.as_view(), name="enum-delete"
        ),
    ]

    try:
        from rest_framework import routers

        from django_enum.tests.enum_prop.views import DRFView

        router = routers.DefaultRouter()
        router.register(r"enumtesters", DRFView)
        urlpatterns.append(path("drf/", include(router.urls)))

    except ImportError:  # pragma: no cover
        pass

    try:
        from django_filters.views import FilterView

        from django_enum.tests.enum_prop.views import EnumTesterFilterViewSet

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
    except (ImportError, ModuleNotFoundError):  # pragma: no cover
        pass

except (ImportError, ModuleNotFoundError):  # pragma: no cover
    pass
