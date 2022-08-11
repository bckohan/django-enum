try:
    from django.urls import include, path
    from django_enum.tests.enum_prop.models import EnumTester
    from django_enum.tests.enum_prop.views import (
        DRFView,
        EnumTesterCreateView,
        EnumTesterDeleteView,
        EnumTesterDetailView,
        EnumTesterFormCreateView,
        EnumTesterFormDeleteView,
        EnumTesterFormView,
        EnumTesterListView,
        EnumTesterUpdateView,
    )
    from rest_framework import routers

    app_name = 'django_enum_tests_enum_prop'

    router = routers.DefaultRouter()
    router.register(r'enumtesters', DRFView)

    urlpatterns = [
        path('enum/<int:pk>', EnumTesterDetailView.as_view(), name='enum-detail'),
        path('enum/list/', EnumTesterListView.as_view(), name='enum-list'),
        path('enum/add/', EnumTesterCreateView.as_view(), name='enum-add'),
        path('enum/form/add/', EnumTesterFormCreateView.as_view(), name='enum-form-add'),
        path('enum/<int:pk>/', EnumTesterUpdateView.as_view(), name='enum-update'),
        path('enum/form/<int:pk>/', EnumTesterFormView.as_view(), name='enum-form-update'),
        path('enum/<int:pk>/delete/', EnumTesterDeleteView.as_view(), name='enum-delete'),
        path('enum/form/<int:pk>/delete/', EnumTesterFormDeleteView.as_view(), name='enum-form-delete'),
        path('drf/', include(router.urls))
    ]

    try:
        from django_enum.tests.enum_prop.views import EnumTesterFilterViewSet
        from django_filters.views import FilterView
        urlpatterns.extend([
            path(
                'enum/filter/',
                FilterView.as_view(
                    model=EnumTester,
                    filterset_fields='__all__',
                    template_name='enumtester_list.html'
                ),
                name='enum-filter'
            ),
            path(
                'enum/filter/symmetric/',
                EnumTesterFilterViewSet.as_view(),
                name='enum-filter-symmetric'
            )
        ])
    except (ImportError, ModuleNotFoundError):  # pragma: no cover
        pass

except (ImportError, ModuleNotFoundError):  # pragma: no cover
    pass
