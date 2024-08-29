from tests.utils import EnumTypeMixin
from django.test import LiveServerTestCase
from tests.djenum.models import AdminDisplayBug35
from django.urls import reverse


class TestAdmin(EnumTypeMixin, LiveServerTestCase):

    BUG35_CLASS = AdminDisplayBug35

    def test_admin_list_display_bug35(self):
        from django.contrib.auth import get_user_model

        get_user_model().objects.create_superuser(
            username="admin",
            email="admin@django-enum.com",
            password="admin_password",
        )
        self.client.login(username="admin", password="admin_password")

        obj = self.BUG35_CLASS.objects.create()

        resp = self.client.get(
            reverse(
                f'admin:{self.BUG35_CLASS._meta.label_lower.replace(".", "_")}_changelist'
            )
        )
        self.assertContains(resp, '<td class="field-int_enum">Value 2</td>')
        change_link = reverse(
            f'admin:{self.BUG35_CLASS._meta.label_lower.replace(".", "_")}_change',
            args=[obj.id],
        )
        self.assertContains(resp, f'<a href="{change_link}">Value1</a>')

    def test_admin_change_display_bug35(self):
        from django.contrib.auth import get_user_model

        get_user_model().objects.create_superuser(
            username="admin",
            email="admin@django-enum.com",
            password="admin_password",
        )
        self.client.login(username="admin", password="admin_password")

        obj = self.BUG35_CLASS.objects.create()
        resp = self.client.get(
            reverse(
                f'admin:{self.BUG35_CLASS._meta.label_lower.replace(".", "_")}_change',
                args=[obj.id],
            )
        )
        self.assertContains(resp, '<div class="readonly">Value1</div>')
        self.assertContains(resp, '<div class="readonly">Value 2</div>')
