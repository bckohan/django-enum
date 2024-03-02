from django.forms import ModelForm

from django_enum.tests.djenum.models import EnumTester


class EnumTesterForm(ModelForm):

    class Meta:
        model = EnumTester
        fields = "__all__"
