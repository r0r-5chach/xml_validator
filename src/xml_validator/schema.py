from pathlib import Path


class Schema:
    """
Loads and prepares a XML Schema for validation.

Handles schema dependencies programatically without modifying original files.
    """

    def __init__(self, schema_folder: str):
        """
Initialize the Schema.

Args:
    schema_folder: Path to folder containing the Schema XSD files.
        """
        self.schema_folder = Path(schema_folder)
        # TODO: Get all schemas in dir
        # TODO: Figure out main schema from dependency analysis
        # TODO: Load Schema
        self._validate_folder()

    def _validate_folder(self) -> None:
        """Validate that the schema folder exists."""
        if not self.schema_folder.exists():
            raise FileNotFoundError(
                    f"Schema folder not found: {self.schema_folder}"
            )

        if not self.schema_folder.is_dir():
            raise ValueError(f"Path is not a directory: {self.schema_folder}")

        try:
            list(self.schema_folder.iterdir())
        except PermissionError:
            raise PermissionError(f"Cannot access schema folder (permission denied): {self.schema_folder}")
