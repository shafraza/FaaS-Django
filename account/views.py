from datetime import timedelta

import pyotp
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.encoding import DjangoUnicodeDecodeError, smart_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Profile
from .permission import IsCurrentUserOwnerOrReadOnly
from .serializers import (
    LoginSerializer,
    LogoutSerializer,
    OTPSerializer,
    PasswordResetRequestSerializer,
    RegisterUserSerializer,
    SetNewPasswordSerializer,
    UserProfileSerializer,
)
from .tasks import send_code_to_user

User = get_user_model()


class UserProfileListView(GenericAPIView):
    queryset = Profile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsCurrentUserOwnerOrReadOnly, IsAuthenticated]

    def get(self, request):
        user_profiles = self.get_queryset()
        serializer = self.get_serializer(user_profiles, many=True)
        return Response(
            {"message": "Profile List", "data": serializer.data},
            status=status.HTTP_200_OK,
        )


class UserProfileUpdateView(GenericAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsCurrentUserOwnerOrReadOnly, IsAuthenticated]

    def get_object(self):
        user = self.request.user
        if not user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            return Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            return Response(
                {"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request):
        profile = self.get_object()
        if isinstance(profile, Response):
            return profile
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Profile updated Successfully", "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterUserView(GenericAPIView):
    serializer_class = RegisterUserSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            send_code_to_user(request, user.email)
            token = RefreshToken.for_user(user)
            data = serializer.data
            data["token"] = {
                "refresh": str(token),
                "access": str(token.access_token),
            }
            data["message"] = "Registration was successful"
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {
                    "message": "Registration failed. Please check the errors.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class LoginUserView(TokenObtainPairView):
    serializer_class = LoginSerializer


class LogoutUserView(GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message", "Logout was successful"}, status=status.HTTP_200_OK
            )


class VerifyOTPView(GenericAPIView):
    serializer_class = OTPSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user_email = request.session.get("user_email")
            user = get_object_or_404(User, email=user_email)

            otp_expiry_time = user.otp_created_at + timedelta(minutes=300)
            if timezone.now() > otp_expiry_time:
                return Response(
                    {"error": "OTP has expired. Please request a new one."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            otp_instance = pyotp.TOTP(user.secret_key, interval=300)
            user_otp = serializer.validated_data["otp"]

            if otp_instance.verify(user_otp, valid_window=1):
                user.is_email_verified = True
                user.save()
                return Response(
                    {"message": "OTP verified successfully!"}, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"error": "Invalid OTP. Please try again."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendOTPView(GenericAPIView):
    def post(self, request):
        user_email = request.session.get("user_email")

        if not user_email:
            return Response(
                {"error": "Session expired. Please try again."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=user_email)
            send_code_to_user(request, user.email)
            return Response(
                {"message": "A new OTP has been sent to your email."},
                status=status.HTTP_200_OK,
            )
        except User.DoesNotExist:
            return Response(
                {"error": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )


class PasswordResetRequestView(GenericAPIView):
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            {"message": "A password reset link has been sent to your email"},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirm(GenericAPIView):
    def get(self, request, uidb64, token):
        try:
            user_id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=user_id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response(
                    {"message": "token is invalid or has expired"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {
                    "success": True,
                    "message": "Credentials is valid",
                    "uidb64": uidb64,
                    "token": token,
                },
                status=status.HTTP_200_OK,
            )
        except DjangoUnicodeDecodeError:
            return Response(
                {"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )


class SetNewPassword(GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {"message": "Password has been reset successfully"},
            status=status.HTTP_200_OK,
        )
