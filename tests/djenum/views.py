from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from django_enum import EnumField
from tests.djenum import enums as dj_enums
from tests.djenum.models import EnumTester


class URLMixin:
    NAMESPACE = "tests_djenum"
    enums = dj_enums

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "Constants": self.enums.Constants,
            "SmallPosIntEnum": self.enums.SmallPosIntEnum,
            "SmallIntEnum": self.enums.SmallIntEnum,
            "PosIntEnum": self.enums.PosIntEnum,
            "IntEnum": self.enums.IntEnum,
            "BigPosIntEnum": self.enums.BigPosIntEnum,
            "BigIntEnum": self.enums.BigIntEnum,
            "TextEnum": self.enums.TextEnum,
            "DateEnum": self.enums.DateEnum,
            "DateTimeEnum": self.enums.DateTimeEnum,
            "DurationEnum": self.enums.DurationEnum,
            "TimeEnum": self.enums.TimeEnum,
            "DecimalEnum": self.enums.DecimalEnum,
            "ExternEnum": self.enums.ExternEnum,
            "DJIntEnum": self.enums.DJIntEnum,
            "DJTextEnum": self.enums.DJTextEnum,
            "NAMESPACE": self.NAMESPACE,
            "update_path": f"{self.NAMESPACE}:enum-update",
            "delete_path": f"{self.NAMESPACE}:enum-delete",
        }


class EnumTesterDetailView(URLMixin, DetailView):
    model = EnumTester
    template_name = "enumtester_detail.html"
    fields = "__all__"


class EnumTesterListView(URLMixin, ListView):
    model = EnumTester
    template_name = "enumtester_list.html"
    fields = "__all__"


class EnumTesterCreateView(URLMixin, CreateView):
    model = EnumTester
    template_name = "enumtester_form.html"
    fields = "__all__"

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class EnumTesterUpdateView(URLMixin, UpdateView):
    model = EnumTester
    template_name = "enumtester_form.html"
    fields = "__all__"

    def get_success_url(self):  # pragma: no cover
        return reverse(f"{self.NAMESPACE}:enum-update", kwargs={"pk": self.object.pk})


class EnumTesterDeleteView(URLMixin, DeleteView):
    model = EnumTester
    template_name = "enumtester_form.html"

    def get_success_url(self):  # pragma: no cover
        return reverse(f"{self.NAMESPACE}:enum-list")


try:
    from rest_framework import serializers, viewsets

    from django_enum.drf import EnumFieldMixin

    class EnumTesterSerializer(EnumFieldMixin, serializers.ModelSerializer):
        class Meta:
            model = EnumTester
            fields = "__all__"

    class DRFView(viewsets.ModelViewSet):
        queryset = EnumTester.objects.all()
        serializer_class = EnumTesterSerializer

except (ImportError, ModuleNotFoundError):  # pragma: no cover
    pass


try:
    from django_filters.views import FilterView

    from django_enum.filters import FilterSet as EnumFilterSet, MultipleEnumFilter

    from .enums import (
        BigIntEnum,
        BigPosIntEnum,
        Constants,
        DateEnum,
        DateTimeEnum,
        DecimalEnum,
        DJIntEnum,
        DJTextEnum,
        DurationEnum,
        ExternEnum,
        IntEnum,
        PosIntEnum,
        SmallIntEnum,
        SmallPosIntEnum,
        TextEnum,
        TimeEnum,
    )

    class EnumTesterFilterViewSet(URLMixin, FilterView):
        class EnumTesterFilter(EnumFilterSet):
            class Meta:
                model = EnumTester
                fields = "__all__"

        filterset_class = EnumTesterFilter
        model = EnumTester
        template_name = "enumtester_list.html"

    class EnumTesterMultipleFilterViewSet(URLMixin, FilterView):
        class EnumTesterMultipleFilter(EnumFilterSet):
            small_pos_int = MultipleEnumFilter(enum=SmallPosIntEnum)
            small_int = MultipleEnumFilter(enum=SmallIntEnum)
            pos_int = MultipleEnumFilter(enum=PosIntEnum)
            int = MultipleEnumFilter(enum=IntEnum)
            big_pos_int = MultipleEnumFilter(enum=BigPosIntEnum)
            big_int = MultipleEnumFilter(enum=BigIntEnum)
            constant = MultipleEnumFilter(enum=Constants)
            text = MultipleEnumFilter(enum=TextEnum)
            extern = MultipleEnumFilter(enum=ExternEnum)

            dj_int_enum = MultipleEnumFilter(enum=DJIntEnum)
            dj_text_enum = MultipleEnumFilter(enum=DJTextEnum)

            # Non-strict
            non_strict_int = MultipleEnumFilter(enum=SmallPosIntEnum, strict=False)
            non_strict_text = MultipleEnumFilter(enum=TextEnum, strict=False)
            no_coerce = MultipleEnumFilter(enum=SmallPosIntEnum, strict=False)

            # eccentric enums
            date_enum = MultipleEnumFilter(enum=DateEnum)
            datetime_enum = MultipleEnumFilter(enum=DateTimeEnum)
            time_enum = MultipleEnumFilter(enum=TimeEnum)
            duration_enum = MultipleEnumFilter(enum=DurationEnum)
            decimal_enum = MultipleEnumFilter(enum=DecimalEnum)

            class Meta:
                fields = [
                    "small_pos_int",
                    "small_int",
                    "pos_int",
                    "int",
                    "big_pos_int",
                    "big_int",
                    "constant",
                    "text",
                    "extern",
                    "non_strict_int",
                    "non_strict_text",
                    "no_coerce",
                    "date_enum",
                    "datetime_enum",
                    "time_enum",
                    "duration_enum",
                    "decimal_enum",
                ]
                model = EnumTester

        filterset_class = EnumTesterMultipleFilter
        model = EnumTester
        template_name = "enumtester_list.html"

except ImportError:  # pragma: no cover
    pass
