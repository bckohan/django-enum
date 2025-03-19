from django.urls import path
try:
    from django.shortcuts import render
    from .choice_form_howto import TextChoicesExampleForm, TextChoicesExample
    from .flag_form_howto import PermissionsExampleForm, Group

    def choice_form_view(request):
        if request.method == "POST":
            form = TextChoicesExampleForm(request.POST)
            if form.is_valid():
                # Process the form data (for now, just print it)
                print("Valid form data:", form.cleaned_data)
        else:
            form = TextChoicesExampleForm(
                initial={
                    "color": TextChoicesExample.Color.RED,
                    "color_ext": "Y"
                }
            )
        return render(request, "tests_examples/choice_form_howto.html", {"form": form})

    def flag_form_view(request):
        if request.method == "POST":
            form = PermissionsExampleForm(request.POST)
            if form.is_valid():
                # Process the form data (for now, just print it)
                print("Valid form data:", form.cleaned_data)
        else:
            form = PermissionsExampleForm(
                initial={
                    "permissions": Group.Permissions.READ | Group.Permissions.EXECUTE,
                    "permissions_ext": Group.Permissions.READ | Group.Permissions.WRITE
                }
            )
        return render(request, "tests_examples/flag_form_howto.html", {"form": form})

    app_name = "howto_forms"

    urlpatterns = [
        path("choice/", choice_form_view, name="choice"),
        path("flag/", flag_form_view, name="flag"),
    ]
except ImportError:
    urlpatterns = []
