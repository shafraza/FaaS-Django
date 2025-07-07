import pytest
from django.urls import reverse, resolve
from app.views import CategoryView, CategoryDetailView, PicView, PicDetailView
from app.models import Category, Pic
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def category():
    """Fixture to create a Category instance"""
    return Category.objects.create(name="Wildlife")

@pytest.fixture
def pic(category):
    """Fixture to create a Pic instance"""
    user = User.objects.create_user(username="testuser", password="testpassword")
    return Pic.objects.create(
        owner=user,
        category=category,
        name="Sample Photo",
        description="Sample description",
        size="M",
    )

@pytest.mark.django_db
def test_category_list_url():
    path = reverse("category-list-create")
    assert resolve(path).func.view_class == CategoryView

@pytest.mark.django_db
def test_category_detail_url(category):
    path = reverse("category-detail", kwargs={"id": category.id})
    assert resolve(path).func.view_class == CategoryDetailView

@pytest.mark.django_db
def test_pic_list_url():
    path = reverse("pic-list-create")
    assert resolve(path).func.view_class == PicView

@pytest.mark.django_db
def test_pic_detail_url(pic):
    path = reverse("pic-detail", kwargs={"id": pic.id})
    assert resolve(path).func.view_class == PicDetailView
