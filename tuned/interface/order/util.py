from tuned.core.exceptions import ValidationError
from tuned.models.enums import FileExtensionType

def resolve_file_type(file_type: str) -> FileExtensionType:
    try:
        return FileExtensionType(file_type)
    except ValueError:
        raise ValidationError(f"Invalid file type: {file_type}")