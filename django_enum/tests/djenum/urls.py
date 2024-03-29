from django.urls import include, path
from django_enum.tests.djenum.models import EnumTester
from django_enum.tests.djenum.views import (
    EnumTesterCreateView,
    EnumTesterDeleteView,
    EnumTesterDetailView,
    EnumTesterListView,
    EnumTesterUpdateView,
)

app_name = 'django_enum_tests_djenum'


urlpatterns = [
    path('enum/<int:pk>', EnumTesterDetailView.as_view(), name='enum-detail'),
    path('enum/list/', EnumTesterListView.as_view(), name='enum-list'),
    path('enum/add/', EnumTesterCreateView.as_view(), name='enum-add'),
    path('enum/<int:pk>/', EnumTesterUpdateView.as_view(), name='enum-update'),
    path('enum/<int:pk>/delete/', EnumTesterDeleteView.as_view(), name='enum-delete')
]


try:
    from django_enum.tests.djenum.views import DRFView
    from rest_framework import routers

    router = routers.DefaultRouter()
    router.register(r'enumtesters', DRFView)
    urlpatterns.append(path('drf/', include(router.urls)))

except ImportError:  # pragma: no cover
    pass


try:
    from django_enum.tests.djenum.views import EnumTesterFilterViewSet
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
except ImportError:  # pragma: no cover
    pass
