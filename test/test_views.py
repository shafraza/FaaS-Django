import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from app.models import Category, Pic
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpassword")

@pytest.fixture
def category(db):
    return Category.objects.create(name="Nature")

@pytest.fixture
def pic(db, user, category):
    return Pic.objects.create(
        owner=user,
        category=category,
        name="Sample Photo",
        description="Sample description",
        size="M",
    )


def test_category_list_create(api_client, user):
    api_client.force_authenticate(user=user)
    url = reverse("category-list-create")

    # Test POST
    response = api_client.post(url, {"name": "Wildlife"})
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["message"] == "Category created successfully"

    # Test GET
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    assert "message" in response.data["results"]
    assert response.data["results"]["message"] == "List of Categories"
    assert len(response.data["results"]["data"]) > 0 


def test_pic_list_create(api_client, user, category):
    api_client.force_authenticate(user=user)
    url = reverse("pic-list-create")

    response = api_client.post(
        url,
        {
            "name": "New Photo",
            "description": "A description",
            "size": "M",
            "category": category.name,
        },
    )
    print("Response Data:", response.data)
    assert response.status_code == status.HTTP_201_CREATED



@pytest.mark.django_db
def test_category_detail(api_client, user, category):
    api_client.force_authenticate(user=user)
    url = reverse("category-detail", kwargs={"id": category.id})

    # Test GET
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["message"] == "Category details"

    # Test PUT
    response = api_client.put(url, {"name": "Updated Category"})
    assert response.status_code == status.HTTP_200_OK
    assert response.data["message"] == "Category updated successfully"

    # Test DELETE
    response = api_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT





@pytest.mark.django_db
def test_pic_detail(api_client, user, pic):
    api_client.force_authenticate(user=user)
    url = reverse("pic-detail", kwargs={"id": pic.id})

    # Test GET
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["message"] == "Pic details"

    # Test PATCH
    response = api_client.patch(url, {"description": "Updated description"})
    assert response.status_code == status.HTTP_200_OK
    assert response.data["message"] == "Pic partially updated successfully"

    # Test DELETE
    response = api_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
