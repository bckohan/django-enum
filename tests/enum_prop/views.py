try:
    from django.urls import reverse, reverse_lazy
    from django.views.generic import CreateView, DeleteView, UpdateView

    from django_enum.filters import FilterSet as EnumFilterSet
    from tests.djenum import views
    from tests.enum_prop import enums as prop_enums
    from tests.enum_prop.enums import (
        BigIntEnum,
        BigPosIntEnum,
        Constants,
        DJIntEnum,
        DJTextEnum,
        ExternEnum,
        IntEnum,
        PosIntEnum,
        SmallIntEnum,
        SmallPosIntEnum,
        TextEnum,
    )
    from tests.enum_prop.forms import EnumTesterForm
    from tests.enum_prop.models import EnumTester

    class EnumTesterDetailView(views.EnumTesterDetailView):
        model = EnumTester
        NAMESPACE = "tests_enum_prop"
        enums = prop_enums

    class EnumTesterListView(views.EnumTesterListView):
        model = EnumTester
        NAMESPACE = "tests_enum_prop"
        enums = prop_enums

    class EnumTesterCreateView(views.URLMixin, CreateView):
        model = EnumTester
        template_name = "enumtester_form.html"
        NAMESPACE = "tests_enum_prop"
        enums = prop_enums
        form_class = EnumTesterForm

    class EnumTesterUpdateView(views.URLMixin, UpdateView):
        model = EnumTester
        template_name = "enumtester_form.html"
        NAMESPACE = "tests_enum_prop"
        enums = prop_enums
        form_class = EnumTesterForm

        def get_success_url(self):  # pragma: no cover
            return reverse(
                f"{self.NAMESPACE}:enum-update", kwargs={"pk": self.object.pk}
            )

    class EnumTesterDeleteView(views.URLMixin, DeleteView):
        NAMESPACE = "tests_enum_prop"
        model = EnumTester
        template_name = "enumtester_form.html"
        enums = prop_enums
        form_class = EnumTesterForm

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
        from tests.djenum.views import EnumTesterFilterViewSet

        class EnumTesterFilterViewSet(EnumTesterFilterViewSet):
            enums = prop_enums

            class EnumTesterFilter(EnumFilterSet):
                class Meta:
                    model = EnumTester
                    fields = "__all__"

            filterset_class = EnumTesterFilter
            model = EnumTester

    except (ImportError, ModuleNotFoundError):  # pragma: no cover
        pass

except (ImportError, ModuleNotFoundError):  # pragma: no cover
    pass
