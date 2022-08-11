from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django_enum.tests.djenum import enums as dj_enums
from django_enum.tests.djenum.forms import EnumTesterForm
from django_enum.tests.djenum.models import EnumTester
from rest_framework import serializers, viewsets


class URLMixin:

    NAMESPACE = 'django_enum_tests_djenum'
    enums = dj_enums

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'Constants': self.enums.Constants,
            'SmallPosIntEnum': self.enums.SmallPosIntEnum,
            'SmallIntEnum': self.enums.SmallIntEnum,
            'PosIntEnum': self.enums.PosIntEnum,
            'IntEnum': self.enums.IntEnum,
            'BigPosIntEnum': self.enums.BigPosIntEnum,
            'BigIntEnum': self.enums.BigIntEnum,
            'TextEnum': self.enums.TextEnum,
            'DJIntEnum': self.enums.DJIntEnum,
            'DJTextEnum': self.enums.DJTextEnum,
        })
        try:
            ctx['update_path'] = reverse(
                f'{self.NAMESPACE}:enum-update',
                kwargs={'pk': self.get_object().pk}
            )
            ctx['update_path'] = reverse(
                f'{self.NAMESPACE}:enum-update',
                kwargs={'pk': self.get_object().pk}
            )
        except AttributeError:
            pass
        return ctx


class EnumTesterDetailView(URLMixin, DetailView):
    model = EnumTester
    template_name = 'enumtester_detail.html'


class EnumTesterListView(URLMixin, ListView):
    model = EnumTester
    template_name = 'enumtester_list.html'


class EnumTesterCreateView(URLMixin, CreateView):
    model = EnumTester
    fields = '__all__'
    template_name = 'enumtester_form.html'


class EnumTesterUpdateView(URLMixin, UpdateView):
    model = EnumTester
    fields = '__all__'
    template_name = 'enumtester_form.html'

    def get_success_url(self):  # pragma: no cover
        return reverse(f'{self.NAMESPACE}:enum-update', kwargs={'pk': self.object.pk})


class EnumTesterFormView(URLMixin, UpdateView):
    form_class = EnumTesterForm
    model = EnumTester
    template_name = 'enumtester_form.html'

    def get_success_url(self):  # pragma: no cover
        return reverse(f'{self.NAMESPACE}:enum-update', kwargs={'pk': self.object.pk})


class EnumTesterFormCreateView(URLMixin, CreateView):
    form_class = EnumTesterForm
    model = EnumTester
    template_name = 'enumtester_form.html'


class EnumTesterDeleteView(URLMixin, DeleteView):
    model = EnumTester
    template_name = 'enumtester_form.html'

    def get_success_url(self):  # pragma: no cover
        return reverse(f'{self.NAMESPACE}:enum-list')


class EnumTesterFormDeleteView(URLMixin, DeleteView):
    form_class = EnumTesterForm
    model = EnumTester
    template_name = 'enumtester_form.html'

    def get_success_url(self):  # pragma: no cover
        return reverse(f'{self.NAMESPACE}:enum-list')


class EnumTesterSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnumTester
        fields = '__all__'


class DRFView(viewsets.ModelViewSet):
    queryset = EnumTester.objects.all()
    serializer_class = EnumTesterSerializer


try:
    from django_enum.filters import FilterSet as EnumFilterSet
    from django_filters.views import FilterView

    class EnumTesterFilterViewSet(FilterView):

        class EnumTesterFilter(EnumFilterSet):
            class Meta:
                model = EnumTester
                fields = '__all__'

        filterset_class = EnumTesterFilter
        model = EnumTester
        template_name = (
            'enumtester_list.html'
        )
except ImportError:  # pragma: no cover
    pass
