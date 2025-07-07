import re

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.utils.encoding import force_str, smart_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from .models import Profile
from rest_framework.serializers import ValidationError #noqa
from .validate import validate_image
from .tasks import send_reset_email
from .image_utils import compress_image
User = get_user_model()
password_pattern = "^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*\-\.]).{8,}$"

    
class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "password2"]

    def validate(self, data):
        if data["password"] != data.get("password2"):
            raise serializers.ValidationError({"password": "Passwords do not match."})
        password = data["password"]
        if not re.match(password_pattern, password):
            raise serializers.ValidationError(
                {
                    "password": "Password must be at least 8 characters long, contain an uppercase letter, a lowercase letter, a digit, and a special character."
                }
            )
        if len(password) < 8:
            raise serializers.ValidationError(
                {"password": "Password must be at least 8 characters long."}
            )
        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
class UserProfileSerializer(serializers.ModelSerializer):
    user=RegisterUserSerializer(read_only=True)
    class Meta:
        model=Profile
        fields=["id","user","image","bio"]
    
    def validate_image(self, value):
        validate_image(value)
        return value

    def update(self, instance, validated_data):
        if validated_data.get("image"):
            image = validated_data.get("image")
            compressed_image = compress_image(image)
            if instance.image:
                try:
                    instance.image.delete(save=False)
                except Exception as e:
                    print(f"Error deleting the old image: {e}")
            instance.image = compressed_image
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
       
class LoginSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        return token

    def validate(self, attrs):
        email = attrs.get("email")
        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError(
                {"email": "No user found with this email."}
            )
        if not user.is_email_verified:
            raise serializers.ValidationError(
                {"email": "Please verify your email before logging in."}
            )
        data = super().validate(attrs)
        data["message"] = "Login was successful"
        return data
    

class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

    def validate(self, attrs):
        self.token = attrs.get("refresh_token")
        return attrs

    def save(self, **kwargs):
        try:
            token = RefreshToken(self.token)
            token.blacklist()
        except TokenError:
            raise serializers.ValidationError(
                {"bad_token": "Token is invalid or expired"}
            )

class OTPSerializer(serializers.Serializer):
    otp = serializers.CharField(
        max_length=6,
        min_length=6,
        error_messages={
            "required": "Please enter the OTP.",
            "max_length": "OTP must be exactly 6 digits long.",
            "min_length": "OTP must be exactly 6 digits long.",
        },
    )

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must be numeric.")
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    class Meta:
        fields = ["email"]

    def validate(self, attrs):
        email = attrs.get("email")
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            request = self.context.get("request")
            site_domain = get_current_site(request).domain
            relative_link = reverse(
                "account:password-reset-confirm",
                kwargs={"uidb64": uidb64, "token": token},
            )
            abslink = f"http://{site_domain}{relative_link}"
            email_body = f"""
                <html>
                    <body style="font-family: Arial, sans-serif; background-color: #f9fafb; margin: 0; padding: 20px;">
                        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); padding: 20px;">
                            <h2 style="color: #333333; font-size: 24px; text-align: center;">Hello {user.username},</h2>
                            <p style="color: #555555; font-size: 16px; text-align: center;">Use the link below to reset your password:</p>
                            <div style="text-align: center; margin: 20px 0;">
                                <a href="{abslink}" style="display: inline-block; padding: 10px 20px; background-color: #007BFF; color: #ffffff; text-decoration: none; border-radius: 5px; font-size: 16px;">Reset Password</a>
                            </div>
                        </div>
                    </body>
                </html>
                """
            data = {
                "email_body": email_body,
                "email_subject": "Reset your Password",
                "to_email": user.email,
            }
            send_reset_email(data)

        else:
            raise serializers.ValidationError("User with this email does not exist.")
        return super().validate(attrs)


class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=100, min_length=6, write_only=True)
    confirm_password = serializers.CharField(
        max_length=100, min_length=6, write_only=True
    )
    uidb64 = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)

    class Meta:
        fields = ["password", "confirm_password", "uidb64", "token"]

    def validate(self, attrs):
        try:
            token = attrs.get("token")
            uidb64 = attrs.get("uidb64")
            password = attrs.get("password")
            confirm_password = attrs.get("confirm_password")

            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=user_id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed("reset link is invalid or has expired", 401)

            if password != confirm_password:
                raise serializers.ValidationError(
                    {"password": "Passwords do not match"}
                )
            if not re.match(password_pattern, password):
                raise serializers.ValidationError(
                    {
                        "password": (
                            "Password must be at least 8 characters long, "
                            "contain an uppercase letter, a lowercase letter, a digit, "
                            "and a special character."
                        )
                    }
                )
            user.set_password(password)
            user.save()
            return user
        except Exception:
            return AuthenticationFailed("link is invalid or has expired")