"""
FSA029 XML Schema Validator - Simplified Version
Usage: python xml_validator.py <schema_folder> <submission_file>
"""
import re
import sys
import tempfile
from lxml import etree
from pathlib import Path


def validate_xml(schema_dir: Path, submitted_file: Path) -> None:
    """Validate XML submission against schema."""
    try:
        validation = validate_inputs(schema_dir, submitted_file)
        if all(validation.values()):
            temp_folder = create_temp_schemas(schema_dir)
            main_schema = find_main_schema(temp_folder)

            with open(main_schema, 'r', encoding="utf-8") as file:
                schema = etree.XMLSchema(etree.parse(file))

            submission = etree.parse(submitted_file)
            result = "VALID" if schema.validate(submission) else "INVALID"

            print(f"Submitted file ({submitted_file}) is {result}")
    except OSError:
        print("Paths provided do not lead to valid file types (.xsd, .xml)")


def validate_inputs(schema_dir: Path, submitted_file: Path) -> dict[str, bool]:
    """Validate input paths exist and are correct types."""
    return {
        "folder": {
            "exists": schema_dir.exists(),
            "is_folder": schema_dir.is_dir(),
        },
        "file": {
            "exists": submitted_file.exists(),
            "is_file": submitted_file.is_file(),
        }
    }


def create_temp_schemas(schema_dir: Path) -> Path:
    """Create temporary schema files with fixed imports."""
    temp_folder = Path(tempfile.mkdtemp())
    files = list(schema_dir.glob("*.xsd"))

    for file in files:
        with open(file, 'r', encoding="utf-8") as schema:
            content = schema.read()

        fixed_content = fix_schema_imports(content)

        temp_file = temp_folder / file.name
        with open(temp_file, 'w', encoding="utf-8") as temp_schema:
            temp_schema.write(fixed_content)

    return temp_folder


def fix_schema_imports(schema_content: str) -> str:
    """Fix schema import paths to reference local files."""
    patterns = [
        (
            r'schemaLocation="[^"]*CommonTypes[^"]*\.xsd"',
            'schemaLocation="CommonTypes-Schema.xsd"'
        ),
        (
            r'schemaLocation="[^"]*/([^/]+\.xsd)"',
            r'schemaLocation="\1"'
        )
    ]

    for pattern, replacement in patterns:
        schema_content = re.sub(pattern, replacement, schema_content)

    return schema_content


def find_main_schema(temp_folder: Path) -> Path:
    """Find the main schema file (FSA029)."""
    for file in temp_folder.glob("*.xsd"):
        if "FSA029" in file.name:
            return file


def main() -> None:
    """Main entry point."""
    if len(sys.argv) != 3:
        print("Usage: python xml_validator.py <schema_dir> <submission_file>")
        sys.exit(1)

    schema_dir, submission_file = Path(sys.argv[1]), Path(sys.argv[2])
    validate_xml(schema_dir, submission_file)


if __name__ == "__main__":
    main()
