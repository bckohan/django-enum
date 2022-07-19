from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.forms import ModelForm
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django_enum.filters import FilterSet as EnumFilterSet
from django_enum import EnumChoiceField
from django_filters.views import FilterView
from django_enum.tests.app1.models import EnumTester
from django_enum.tests.app1.enums import (
    TextEnum,
    Constants,
    SmallPosIntEnum,
    SmallIntEnum,
    IntEnum,
    PosIntEnum,
    BigPosIntEnum,
    BigIntEnum
)


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

    class EnumTesterForm(ModelForm):
        small_pos_int = EnumChoiceField(SmallPosIntEnum)
        small_int = EnumChoiceField(SmallIntEnum)
        pos_int = EnumChoiceField(PosIntEnum)
        int = EnumChoiceField(IntEnum)
        big_pos_int = EnumChoiceField(BigPosIntEnum)
        big_int = EnumChoiceField(BigIntEnum)
        constant = EnumChoiceField(Constants)
        text = EnumChoiceField(TextEnum)

        class Meta:
            model = EnumTester
            fields = '__all__'

    form_class = EnumTesterForm
    model = EnumTester


class EnumTesterDeleteView(DeleteView):
    model = EnumTester
    success_url = reverse_lazy(
        'django_enum_tests_app1:enum-list'
    )


class EnumTesterFilterViewSet(FilterView):

    class EnumTesterFilter(EnumFilterSet):
        class Meta:
            model = EnumTester
            fields = '__all__'

    filterset_class = EnumTesterFilter
    model = EnumTester
    template_name = (
        'django_enum_tests_app1/enumtester_list.html'
    )
