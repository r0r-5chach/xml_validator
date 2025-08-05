"""
FSA029 XML Schema Validator - Simplified Version
Usage: python xml_validator.py <schema_folder> <submission_file>
"""
import re
import shutil
import sys
import tempfile
from lxml import etree
from pathlib import Path


def validate_xml(schema_dir: Path, submitted_file: Path) -> None:
    """Validate XML submission against schema."""
    try:
        temp_folder = None
        if validate_inputs(schema_dir, submitted_file):
            temp_folder = create_temp_schemas(schema_dir)
            main_schema = find_main_schema(temp_folder)

            if main_schema is None:
                print("Error: FSA029 schema not in the provided directory")
                return

            with open(main_schema, 'r', encoding="utf-8") as file:
                schema = etree.XMLSchema(etree.parse(file))

            submission = etree.parse(submitted_file)
            result = "VALID" if schema.validate(submission) else "INVALID"

            print(f"Submitted file ({submitted_file}) is {result}")
        else:
            print("Paths provided do not lead to valid file types (xsd, xml)")
    finally:
        if temp_folder and temp_folder.exists():
            shutil.rmtree(temp_folder, ignore_errors=True)


def validate_inputs(schema_dir: Path, submitted_file: Path) -> bool:
    """Validate input paths exist and are correct types."""
    dir_is_valid = schema_dir.exists() and schema_dir.is_dir()
    file_is_valid = submitted_file.exists() and submitted_file.is_file()
    return dir_is_valid and file_is_valid


def create_temp_schemas(schema_dir: Path) -> Path:
    """Create temporary schema files with fixed imports."""
    temp_folder = Path(tempfile.mkdtemp())
    files = list(schema_dir.glob("*.xsd"))

    for file in files:
        with open(file, 'r', encoding="utf-8") as schema:
            fixed_content = fix_schema_imports(schema.read())

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
