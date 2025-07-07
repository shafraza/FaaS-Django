import uuid

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Category(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True)
    name = models.CharField(max_length=200)

    class Meta:
        db_table = "categories"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
        ]
        verbose_name = "category"
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Pic(models.Model):
    IMAGE_SIZE_CHOICES = (
        ("SM", "Small"),
        ("M", "Medium"),
        ("L", "Large"),
        ("XL", "Extra Large"),
    )

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pics")
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="pics"
    )
    size = models.CharField(
        max_length=50,
        choices=IMAGE_SIZE_CHOICES,
        default="M",
    )
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to="photos/%Y/", blank=True)
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "pics"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["id"]),
            models.Index(fields=["name"]),
            models.Index(fields=["-created"]),
        ]
        verbose_name = "pic"
        verbose_name_plural = "pics"

    def __str__(self):
        return f"{self.name} - {self.owner.username}"
