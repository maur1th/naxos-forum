from forum.models import Category
from api.serializers import CategorySerializer
from rest_framework import generics


class CategoryList(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
