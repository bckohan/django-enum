from django.forms import ModelForm

from tests.djenum.models import EnumTester


class EnumTesterForm(ModelForm):
    class Meta:
        model = EnumTester
        fields = "__all__"
