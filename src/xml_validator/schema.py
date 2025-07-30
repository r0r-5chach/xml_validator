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
        # TODO: Validate dir
        # TODO: Get all schemas in dir
        # TODO: Figure out main schema from dependency analysis
        # TODO: Load Schema
