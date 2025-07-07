from django.contrib import admin
from .models import User,Profile
class UserAdmin(admin.ModelAdmin):
    list_display = [
        "username",
        "email",
        "is_email_verified",
        "secret_key",
        "otp_created_at",
    ]
    search_fields = ["username", "email"]
    list_filter = ["otp_created_at"]
    ordering = ["username"]
    readonly_fields = ["secret_key", "otp_created_at"]

class ProfileAdmin(admin.ModelAdmin):
    list_display=["user","date_joined","last_updated"]

admin.site.register(Profile,ProfileAdmin)
admin.site.register(User, UserAdmin)