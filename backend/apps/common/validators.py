from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

validate_pdf_extension = FileExtensionValidator(allowed_extensions=["pdf"])

MAX_UPLOAD_SIZE_BYTES = 20 * 1024 * 1024


def validate_upload_size(file):
    if file.size > MAX_UPLOAD_SIZE_BYTES:
        raise ValidationError(
            f"File too large ({file.size} bytes). Maximum allowed is "
            f"{MAX_UPLOAD_SIZE_BYTES} bytes."
        )
