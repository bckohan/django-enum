try:
    from django.urls import reverse, reverse_lazy
    from django_enum.filters import FilterSet as EnumFilterSet
    from django_enum.tests.djenum import views
    from django_enum.tests.enum_prop import enums as prop_enums
    from django_enum.tests.enum_prop.forms import EnumTesterForm
    from django_enum.tests.enum_prop.models import EnumTester
    from rest_framework import serializers, viewsets


    class EnumTesterDetailView(views.EnumTesterDetailView):
        model = EnumTester
        NAMESPACE = 'django_enum_tests_enum_prop'
        enums = prop_enums


    class EnumTesterListView(views.EnumTesterListView):
        model = EnumTester
        NAMESPACE = 'django_enum_tests_enum_prop'
        enums = prop_enums


    class EnumTesterCreateView(views.EnumTesterCreateView):
        model = EnumTester
        NAMESPACE = 'django_enum_tests_enum_prop'
        enums = prop_enums


    class EnumTesterUpdateView(views.EnumTesterUpdateView):
        model = EnumTester
        NAMESPACE = 'django_enum_tests_enum_prop'
        enums = prop_enums

        def get_success_url(self):  # pragma: no cover
            return reverse(f'{self.NAMESPACE}:enum-update',
                           kwargs={'pk': self.object.pk})


    class EnumTesterFormView(views.EnumTesterFormView):
        form_class = EnumTesterForm
        model = EnumTester
        NAMESPACE = 'django_enum_tests_enum_prop'
        enums = prop_enums

        def get_success_url(self):  # pragma: no cover
            return reverse(f'{self.NAMESPACE}:enum-update',
                           kwargs={'pk': self.object.pk})

    class EnumTesterFormCreateView(views.EnumTesterFormCreateView):
        form_class = EnumTesterForm
        model = EnumTester
        NAMESPACE = 'django_enum_tests_enum_prop'
        enums = prop_enums


    class EnumTesterDeleteView(views.EnumTesterDeleteView):
        model = EnumTester
        NAMESPACE = 'django_enum_tests_enum_prop'
        enums = prop_enums


    class EnumTesterFormDeleteView(views.EnumTesterFormDeleteView):
        form_class = EnumTesterForm
        model = EnumTester
        NAMESPACE = 'django_enum_tests_enum_prop'
        enums = prop_enums


    class EnumTesterSerializer(serializers.ModelSerializer):
        class Meta:
            model = EnumTester
            fields = '__all__'


    class DRFView(viewsets.ModelViewSet):
        queryset = EnumTester.objects.all()
        serializer_class = EnumTesterSerializer


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
