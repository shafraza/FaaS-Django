import imghdr

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_image(image):
    if image.size > settings.UPLOAD_FILE_MAX_SIZE:
        raise ValidationError(
            f"Image size {image.size} bytes exceeds the maximum limit of 2 MB."
        )
    extension = image.name.split(".")[-1].lower()

    if extension not in settings.WHITELISTED_IMAGE_TYPES.keys():
        raise ValidationError(
            "Invalid image extension. Only .jpeg, .jpg, and .png are allowed."
        )
    image_data = image.read()
    image_type = imghdr.what(None, h=image_data)

    if image_type not in settings.WHITELISTED_IMAGE_TYPES.keys():
        raise ValidationError(
            f"Invalid image MIME type. Expected one of {', '.join(settings.WHITELISTED_IMAGE_TYPES.keys())}, but got {image_type}."
        )
    image.seek(0)