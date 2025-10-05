import base64
import uuid
import filetype
from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """
    Accepts Base64-encoded Images (even data-URLs) or normal uploads
    """

    def to_internal_value(self, data):
        """
        Converts Base64-encoded image data or a file object into a Django ContentFile.

        - Accepts standard file uploads or Base64 strings (e.g. "data:image/png;base64,...").
        - Returns None for empty or "null" values.
        - Decodes Base64 data, detects file type via `filetype`, and generates a unique filename.
        - Raises ValidationError if the data cannot be decoded.

        Returns:
            ContentFile | None: A file suitable for saving to an ImageField.
        """
        if isinstance(data, str):
            if data == "" or data.lower() == "null":
                return None
            if "data:" in data and ";base64," in data:
                _, data = data.split(";base64,", 1)
            try:
                decoded = base64.b64decode(data)
            except Exception:
                raise serializers.ValidationError("Invalid base64 image data.")

            kind = filetype.guess(decoded)
            ext = kind.extension if kind else "jpg"
            file_name = f"{uuid.uuid4().hex}.{ext}"
            data = ContentFile(decoded, name=file_name)
        return super().to_internal_value(data)
