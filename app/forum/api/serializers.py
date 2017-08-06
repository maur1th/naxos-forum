from rest_framework import serializers
from forum.models import Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "title", "subtitle", "slug")  # "thread_count", "post_count"
