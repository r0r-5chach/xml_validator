from pathlib import Path
from typing import List


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
        self.all_schemas: List[Path] = []
        # TODO: Figure out main schema from dependency analysis
        # TODO: Load Schema
        self._validate_folder()
        self._discover_schemas()

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
            raise PermissionError(
                f"Cannot access schema folder: {self.schema_folder}"
            )

    def _discover_schemas(self) -> None:
        """Discover all .xsd files in the folder."""
        self.all_schemas = list(self.schema_folder.glob(".xsd"))

        if not self.all_schemas:
            raise FileNotFoundError(f"No .xsd files found in folder: {self.schema_folder}")
