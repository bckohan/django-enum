from .models import TextChoicesExample
from django_enum.filters import EnumFilter
from django_filters.views import FilterView
from django_filters import FilterSet


class TextChoicesExampleFilterViewSet(FilterView):

    class TextChoicesExampleFilter(FilterSet):

        color = EnumFilter(enum=TextChoicesExample.Color)

        class Meta:
            model = TextChoicesExample
            fields = '__all__'

    filterset_class = TextChoicesExampleFilter
    model = TextChoicesExample

# now filtering by symmetric value in url parameters works:
# e.g.:  /?color=FF0000
