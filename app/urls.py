from django.urls import path
from .views import CategoryDetailView,CategoryView,PicView,PicDetailView

urlpatterns=[
    path("categories/",CategoryView.as_view(), name="category-list-create"),
    path('categories/<uuid:id>/', CategoryDetailView.as_view(), name='category-detail'),
    path("pics/",PicView.as_view(),name="pic-list-create"),
    path("pics/<uuid:id>/", PicDetailView.as_view(), name="pic-detail"),
]