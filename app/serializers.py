from rest_framework import serializers
from .models import Category,Pic


class CategorySerializer(serializers.HyperlinkedModelSerializer):
    pics = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name='pic-detail',
        lookup_field='id' )
    class Meta:
        model = Category
        fields = ['url', 'id', 'name','pics']
        extra_kwargs = {
            'url': {'view_name': 'category-detail', 'lookup_field': 'id'}
        }


class PicSerializer(serializers.HyperlinkedModelSerializer):
    owner=serializers.ReadOnlyField(source='owner.username')
    category = serializers.SlugRelatedField(queryset=Category.objects.all(),slug_field='name')
    class Meta:
        model = Pic
        fields = ['url','id', 'category', 'owner','name', 'image','size','description', 'created', 'updated']
        extra_kwargs = {
            'url': {'view_name': 'pic-detail', 'lookup_field': 'id'}
        }
