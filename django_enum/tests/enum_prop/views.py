from django.forms import ModelForm
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django_enum import EnumChoiceField
from django_enum.filters import FilterSet as EnumFilterSet
from django_enum.tests.enum_prop.enums import (
    BigIntEnum,
    BigPosIntEnum,
    Constants,
    DJIntEnum,
    DJTextEnum,
    IntEnum,
    PosIntEnum,
    SmallIntEnum,
    SmallPosIntEnum,
    TextEnum,
)
from django_enum.tests.enum_prop.forms import EnumTesterForm
from django_enum.tests.enum_prop.models import EnumTester
from django_filters.views import FilterView


class EnumTesterDetailView(DetailView):
    model = EnumTester


class EnumTesterListView(ListView):
    model = EnumTester


class EnumTesterCreateView(CreateView):
    model = EnumTester
    fields = '__all__'


class EnumTesterUpdateView(UpdateView):
    model = EnumTester
    fields = '__all__'


class EnumTesterFormView(UpdateView):

    form_class = EnumTesterForm
    model = EnumTester


class EnumTesterFormCreateView(CreateView):

    form_class = EnumTesterForm
    model = EnumTester


class EnumTesterDeleteView(DeleteView):
    model = EnumTester
    success_url = reverse_lazy(
        'django_enum_tests_enum_prop:enum-list'
    )


class EnumTesterFilterViewSet(FilterView):

    class EnumTesterFilter(EnumFilterSet):
        class Meta:
            model = EnumTester
            fields = '__all__'

    filterset_class = EnumTesterFilter
    model = EnumTester
    template_name = (
        'django_enum_tests_enum_prop/enumtester_list.html'
    )
