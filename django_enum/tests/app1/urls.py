from django.urls import path
from django_enum.tests.app1.models import EnumTester
from django_enum.tests.app1.views import (
    EnumTesterCreateView,
    EnumTesterDeleteView,
    EnumTesterDetailView,
    EnumTesterFilterViewSet,
    EnumTesterFormView,
    EnumTesterListView,
    EnumTesterUpdateView,
    EnumTesterFormCreateView
)
from django_filters.views import FilterView

app_name = 'django_enum_tests_app1'

urlpatterns = [
    path('enum/<int:pk>', EnumTesterDetailView.as_view(), name='enum-detail'),
    path('enum/list/', EnumTesterListView.as_view(), name='enum-list'),
    path(
        'enum/filter/',
        FilterView.as_view(
            model=EnumTester,
            filterset_fields='__all__',
            template_name='django_enum_tests_app1/enumtester_list.html'
        ),
        name='enum-filter'
    ),
    path(
        'enum/filter_explicit/',
        EnumTesterFilterViewSet.as_view(),
        name='enum-filter_explicit'
    ),
    path('enum/add/', EnumTesterCreateView.as_view(), name='enum-add'),
    path('enum/form/add/', EnumTesterFormCreateView.as_view(), name='enum-form-add'),
    path('enum/<int:pk>/', EnumTesterUpdateView.as_view(), name='enum-update'),
    path('enum/form/<int:pk>/', EnumTesterFormView.as_view(), name='enum-form-update'),
    path('enum/<int:pk>/delete/', EnumTesterDeleteView.as_view(), name='enum-delete'),
]
