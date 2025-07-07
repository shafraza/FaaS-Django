from django_filters import rest_framework as filters

from .models import Pic


class PicFilter(filters.FilterSet):
    size = filters.ChoiceFilter(choices=Pic.IMAGE_SIZE_CHOICES, null_value=None)
    category = filters.CharFilter(field_name="category__name", lookup_expr="icontains")
    owner = filters.CharFilter(field_name="owner__username", lookup_expr="icontains")
    from_created = filters.DateTimeFilter(field_name="created", lookup_expr="gte")
    to_created = filters.DateTimeFilter(field_name="created", lookup_expr="lte")
    description = filters.CharFilter(field_name="description", lookup_expr="icontains")

    class Meta:
        model = Pic
        fields = [
            "size",
            "category",
            "owner",
            "from_created",
            "to_created",
            "description",
        ]
