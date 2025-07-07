import pytest
from app.models import Category, Pic
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_category_model():
    category = Category.objects.create(name="Wildlife")
    assert Category.objects.count() == 1
    assert str(category) == "Wildlife"

@pytest.mark.django_db
def test_pic_model():
    user = User.objects.create_user(username="testuser", password="testpassword")
    category = Category.objects.create(name="Nature")
    pic = Pic.objects.create(
        owner=user,
        category=category,
        name="Sample Photo",
        description="Sample description",
        size="M",
    )
    assert Pic.objects.count() == 1
    assert str(pic) == f"Sample Photo - {user.username}"
