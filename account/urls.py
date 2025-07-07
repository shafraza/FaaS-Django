from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    LoginUserView,
    LogoutUserView,
    PasswordResetConfirm,
    PasswordResetRequestView,
    RegisterUserView,
    ResendOTPView,
    SetNewPassword,
    UserProfileListView,
    UserProfileUpdateView,
    VerifyOTPView,
)

app_name = "account"
urlpatterns = [
    path("register/", RegisterUserView.as_view(), name="register"),
    path("verify/", VerifyOTPView.as_view(), name="verify-otp"),
    path("resend-otp/", ResendOTPView.as_view(), name="resend-otp"),
    path("login/", LoginUserView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("logout/", LogoutUserView.as_view(), name="logout"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        PasswordResetConfirm.as_view(),
        name="password-reset-confirm",
    ),
    path("set-new-password/", SetNewPassword.as_view(), name="set-password"),
    path("profile-update/", UserProfileUpdateView.as_view(), name="profile-update"),
    path("profiles/", UserProfileListView.as_view(), name="user-profile-list"),
]
