from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters as drf_filters
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from .filters import PicFilter
from .models import Category, Pic
from .permission import IsCurrentUserOwnerOrReadOnly
from .recommender import PhotoRecommender
from .serializers import CategorySerializer, PicSerializer


class CategoryView(GenericAPIView):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    throttle_scope = "categories"
    throttle_classes = (ScopedRateThrottle,)
    filter_backends = [drf_filters.SearchFilter, drf_filters.OrderingFilter]
    search_fields = ["^name"]
    ordering_fields = ["name"]
    permission_classes = [IsCurrentUserOwnerOrReadOnly, IsAuthenticatedOrReadOnly]

    def get(self, request, *args, **kwargs):
        categories = self.filter_queryset(self.get_queryset())
        paginator = self.pagination_class()
        paginated_categories = paginator.paginate_queryset(categories, request)

        serializer = self.get_serializer(paginated_categories, many=True)
        return paginator.get_paginated_response(
            {"message": "List of Categories", "data": serializer.data}
        )

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Category created successfully", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )


class CategoryDetailView(GenericAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    throttle_scope = "categories"
    throttle_classes = (ScopedRateThrottle,)
    lookup_field = "id"
    permission_classes = [IsCurrentUserOwnerOrReadOnly, IsAuthenticatedOrReadOnly]

    def get_object(self):
        uuid = self.kwargs.get("id")
        try:
            return Category.objects.get(pk=uuid)
        except Category.DoesNotExist:
            from rest_framework.exceptions import NotFound

            raise NotFound("Category not found")

    def get(self, request, *args, **kwargs):
        category = self.get_object()
        serializer = self.get_serializer(category)
        return Response(
            {"message": "Category details", "data": serializer.data},
            status=status.HTTP_200_OK,
        )

    def put(self, request, *args, **kwargs):
        category = self.get_object()
        serializer = self.get_serializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Category updated successfully", "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )

    def patch(self, request, *args, **kwargs):
        category = self.get_object()
        serializer = self.get_serializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Category partially updated successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        category.delete()
        return Response(
            {"message": "Category deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )


class PicView(GenericAPIView):
    serializer_class = PicSerializer
    queryset = Pic.objects.all()
    filter_backends = [
        DjangoFilterBackend,
        drf_filters.SearchFilter,
        drf_filters.OrderingFilter,
    ]
    filterset_class = PicFilter
    search_fields = ["^name"]
    ordering_fields = ["name", "created"]
    permission_classes = [IsCurrentUserOwnerOrReadOnly, IsAuthenticatedOrReadOnly]
    throttle_scope = "pics"
    throttle_classes = (ScopedRateThrottle,)

    def get(self, request, *args, **kwargs):
        pics = self.filter_queryset(self.get_queryset())
        paginator = self.pagination_class()
        paginated_pics = paginator.paginate_queryset(pics, request)

        serializer = self.get_serializer(paginated_pics, many=True)
        return paginator.get_paginated_response(
            {"message": "List of Photos", "data": serializer.data}
        )

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(
                {"message": "Photo created successfully", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )


class PicDetailView(GenericAPIView):
    serializer_class = PicSerializer
    queryset = Pic.objects.all()
    lookup_field = "id"
    permission_classes = [IsCurrentUserOwnerOrReadOnly, IsAuthenticatedOrReadOnly]
    throttle_scope = "pics"
    throttle_classes = (ScopedRateThrottle,)
    recommender = PhotoRecommender()

    def get_object(self):
        uuid = self.kwargs.get("id")
        try:
            return Pic.objects.get(pk=uuid)
        except Pic.DoesNotExist:
            raise NotFound("Photo not found")

    def get(self, request, *args, **kwargs):
        pic = self.get_object()
        serializer = self.get_serializer(pic, context={"request": request})
        self.recommender.photos_viewed([pic])
        recommendations = self.recommender.suggest_photos_for([pic])
        recommendations_serializer = PicSerializer(
            recommendations, many=True, context={"request": request}
        )

        return Response(
            {
                "message": "Pic details",
                "data": serializer.data,
                "recommendations": recommendations_serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def put(self, request, *args, **kwargs):
        pic = self.get_object()
        serializer = self.get_serializer(
            pic, data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Pic updated successfully", "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )

    def patch(self, request, *args, **kwargs):
        pic = self.get_object()
        serializer = self.get_serializer(
            pic, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Pic partially updated successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, *args, **kwargs):
        pic = self.get_object()
        pic.delete()
        return Response(
            {"message": "Pic deleted successfully"}, status=status.HTTP_204_NO_CONTENT
        )
