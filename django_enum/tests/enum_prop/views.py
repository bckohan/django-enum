try:
    from django.urls import reverse, reverse_lazy
    from django.views.generic import CreateView, DeleteView, UpdateView
    from django_enum.filters import FilterSet as EnumFilterSet
    from django_enum.tests.djenum import views
    from django_enum.tests.enum_prop import enums as prop_enums
    from django_enum.tests.enum_prop.enums import (
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
    from django_enum.tests.enum_prop.forms import EnumTesterForm
    from django_enum.tests.enum_prop.models import EnumTester


    class EnumTesterDetailView(views.EnumTesterDetailView):
        model = EnumTester
        NAMESPACE = 'django_enum_tests_enum_prop'
        enums = prop_enums


    class EnumTesterListView(views.EnumTesterListView):
        model = EnumTester
        NAMESPACE = 'django_enum_tests_enum_prop'
        enums = prop_enums


    class EnumTesterCreateView(views.URLMixin, CreateView):
        model = EnumTester
        template_name = 'enumtester_form.html'
        NAMESPACE = 'django_enum_tests_enum_prop'
        enums = prop_enums
        form_class = EnumTesterForm


    class EnumTesterUpdateView(views.URLMixin, UpdateView):
        model = EnumTester
        template_name = 'enumtester_form.html'
        NAMESPACE = 'django_enum_tests_enum_prop'
        enums = prop_enums
        form_class = EnumTesterForm

        def get_success_url(self):  # pragma: no cover
            return reverse(f'{self.NAMESPACE}:enum-update',
                           kwargs={'pk': self.object.pk})


    class EnumTesterDeleteView(views.URLMixin, DeleteView):
        NAMESPACE = 'django_enum_tests_enum_prop'
        model = EnumTester
        template_name = 'enumtester_form.html'
        enums = prop_enums
        form_class = EnumTesterForm

        def get_success_url(self):  # pragma: no cover
            return reverse(f'{self.NAMESPACE}:enum-list')


    try:

        from django_enum.drf import EnumField
        from django_enum.drf import EnumField as DRFEnumField
        from rest_framework import serializers, viewsets

        class EnumTesterSerializer(serializers.ModelSerializer):

            # todo not working?
            # serializer_field_mapping = {
            #     **serializers.ModelSerializer.serializer_field_mapping,
            #     EnumField: DRFEnumField
            # }

            small_pos_int = EnumField(SmallPosIntEnum, allow_null=True)
            small_int = EnumField(SmallIntEnum)
            pos_int = EnumField(PosIntEnum)
            int = EnumField(IntEnum, allow_null=True)
            big_pos_int = EnumField(BigPosIntEnum, allow_null=True)
            big_int = EnumField(BigIntEnum)
            constant = EnumField(Constants, allow_null=True)
            text = EnumField(TextEnum, allow_null=True)
            extern = EnumField(ExternEnum, allow_null=True)
            dj_int_enum = EnumField(DJIntEnum)
            dj_text_enum = EnumField(DJTextEnum)
            non_strict_int = EnumField(SmallPosIntEnum, strict=False, allow_null=True)
            non_strict_text = EnumField(TextEnum, strict=False, allow_blank=True)
            no_coerce = EnumField(SmallPosIntEnum, allow_null=True)

            class Meta:
                model = EnumTester
                fields = '__all__'


        class DRFView(viewsets.ModelViewSet):
            queryset = EnumTester.objects.all()
            serializer_class = EnumTesterSerializer

    except (ImportError, ModuleNotFoundError):  # pragma: no cover
        pass

    try:

        from django_enum.tests.djenum.views import EnumTesterFilterViewSet

        class EnumTesterFilterViewSet(EnumTesterFilterViewSet):

            enums = prop_enums

            class EnumTesterFilter(EnumFilterSet):
                class Meta:
                    model = EnumTester
                    fields = '__all__'

            filterset_class = EnumTesterFilter
            model = EnumTester
    except (ImportError, ModuleNotFoundError):  # pragma: no cover
        pass

except (ImportError, ModuleNotFoundError):  # pragma: no cover
    pass
