from io import BytesIO

from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image



def compress_image(image, quality=80):
    if not image or not hasattr(image, 'name'):
        raise ValueError("Invalid image file.")
    
    img = Image.open(image)
    if img.mode != "RGB":
        img = img.convert("RGB")
    
    print(f"Image name: {getattr(image, 'name', 'Unknown')}")
    print(f"Image format detected by Pillow: {img.format}")
    
    file_format = img.format.lower() if img.format else image.name.split('.')[-1].lower()

    if file_format not in ["jpeg", "jpg", "png"]:
        raise ValueError(f"Unsupported image format: {file_format or 'Unknown'}")
    
    original_size = image.size
    print(f"Original file size: {original_size} bytes")

    thumb_io = BytesIO()

    if file_format in ["jpeg", "jpg"]:
        img.save(thumb_io, format="JPEG", quality=quality)
    elif file_format == "png":
        img.save(thumb_io, format="PNG", optimize=True)
    
    compressed_size = len(thumb_io.getvalue())
    print(f"Compressed file size: {compressed_size} bytes")

    return InMemoryUploadedFile(
        thumb_io,
        "ImageField",
        f"{image.name.split('.')[0]}_compressed.{file_format}",
        f"image/{file_format}",
        compressed_size,
        None,
    )
