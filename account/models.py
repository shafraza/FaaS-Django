import uuid
import os
from PIL import Image
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    secret_key = models.CharField(blank=True, null=True, max_length=100)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)

    class Meta:
        db_table = "users"
        ordering = ["email"]
        indexes = [
            models.Index(fields=["email"]),
        ]
        verbose_name = "user"
        verbose_name_plural = "users"

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return f" {self.username}"


class Profile(models.Model):
    id = models.UUIDField(
        editable=False, primary_key=True, unique=True, default=uuid.uuid4
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="profiles/", default="default/avatar.jpg")
    bio = models.TextField(max_length=500)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "profiles"
        ordering = ["date_joined"]
        indexes = [
            models.Index(fields=["id"]),
            models.Index(fields=["date_joined"]),
        ]
        verbose_name = "profile"
        verbose_name_plural = "profiles"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image and os.path.isfile(self.image.path):
            img = Image.open(self.image.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.image.path)

    def __str__(self):
        return f"{self.user.username} Profile"
