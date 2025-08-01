# XML Validator for FSA029 Balance Sheet Schema

A Python-based XML validator specifically designed to validate FSA029 Balance Sheet submissions against the Bank of England FSA029 schema, with automatic dependency resolution and schema import fixing.

## Features

- **Automatic Dependency Resolution**: Discovers and loads all required schema dependencies (e.g., CommonTypes-Schema.xsd)
- **Schema Import Fixing**: Programmatically fixes schema import paths without modifying original files
- **Comprehensive Validation**: Validates XML submissions against FSA029 v4 schema with detailed error reporting
- **Schema Information**: Display detailed information about loaded schemas
- **Temporary File Management**: Uses temporary files for schema processing, leaving originals untouched
- **Feberuc XML Schema Support**: Although designed for FSA029, the architecture should work with any XML schema (untested)

## Installation

### Prerequisites

- Python 3.15 or higher
- pip (Python package installer)

### Install Package

To install the package with all dependencies:

```bash
pip install -e .
```

This will:
- Install the core dependency (`lxml>=6.0.0`)
- Make the `xml-validator` command available system-wide

### Install Development Dependencies

For testing and development:

```bash
pip install -e ".[dev]"
```

This includes pytest and coverage tools.

## Usage

### Basic Usage

```bash
python -m xml_validator <SCHEMA_FOLDER> <SUBMISSION_FILE>
```

### Examples

#### Validate an FSA029 submission:

```bash
python -m xml_validator ./schemas/fsa029/ ./samples/FSA029-Sample-Valid.xml
```

#### Display schema information:

```bash
python -m xml_validator ./schemas/fsa029/ ./samples/FSA029-Sample-Valid.xml --schema-info
```

#### Using the installed command:

```bash
xml-validator ./schemas/fsa029/ ./samples/FSA029-Sample-Valid.xml
```

### Command Line Arguments

- `SCHEMA_FOLDER`: Path to folder containing FSA029-Schema.xsd and CommonTypes-Schema.xsd files
- `SUBMISSION_FILE`: Path to FSA029 XML submission file to validate
- `--schema-info`: Display detailed information about the schema files (optional)
- `--version`: Show version information
- `--help`: Show help message

### Success Output

When validation succeeds:
```
./samples/FSA029-Sample-Valid.xml is VALID
```

### Error Output

When validation fails:
```
RuntimeError: Validation failed for samples/FSA029-Sample-Full.xml:
  - samples/FSA029-Sample-Full.xml:102:0:ERROR:SCHEMASV:SCHEMAV_ELEMENT_CONTENT: Element '{urn:fsa-gov-uk:MER:FSA029:4}PartnershipsSoleTraders': This element is not expected.```
```

## Project Structure

```
xml_validator/
├── src/
│   └── xml_validator/
│       ├── __init__.py          # Package initialization
│       ├── __main__.py          # Main entry point
│       ├── cli.py               # Command line interface
│       └── schema.py            # Schema validation logic
├── schemas/
│   └── fsa029/
│       ├── FSA029-Schema.xsd    # Main FSA029 schema
│       └── CommonTypes-Schema.xsd # Common types dependency
├── samples/
│   ├── FSA029-Sample-Valid.xml  # Valid sample submission
│   └── FSA029-Sample-Full.xml   # Invalid sample (for testing)
├── tests/                       # Test suite
│   ├── test_cli.py              # CLI tests
│   ├── test_main.py             # Main tests
│   └── test_schema.py           # Schema tests
├── pyproject.toml              # Project configuration
└── README.md                   # This file
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=xml_validator

# Run specific test file
pytest tests/test_schema.py
```

## Development Notes

## Scope and Implementation
This implementation may have gone beyond the strict requirements of the brief. This was intentional to demonstrate a broader range of technical skills relevant to the position, including:

- **Python 3 software development**: Creating a complete, installable Python package
- **Computer science fundamentals**: Implementing dependency resolution algorithms and tree traversal for schema analysis
- **Problem-solving and troubleshooting**: Designing solutions for complex XML schema import path issues
- **Full application lifecycle**: Writing, testing, and creating deployable software with proper documentation
- **XML expertise**: Deep work with XML Schema validation, namespaces, and dependency management
- **Test-driven development**: Comprehensive test suite with pytest and coverage reporting
- **Developer collaborative tools**: Proper Git repository structure and development practices

## AI Assistance
AI tools were used to assist with this project, primarily for:

- Research into XML schema validation techniques and lxml library usage
- Assistance with writing comprehensive test cases (as I have less experience with pytest)

The core logic, architecture decisions, and problem-solving approach remain original work.

## Schema Requirements Compliance

This validator meets all requirements specified in the brief:

1. ✅ **Schema Folder Input**: Takes FSA029 schema folder as input
2. ✅ **Submission File Input**: Takes path to FSA029 submission file
3. ✅ **Dependency Co-location**: CommonTypes schema must be in same folder as FSA029 schema
4. ✅ **Path Restrictions**: Forbidden `/CommonTypes/v14/` paths are programmatically fixed
5. ✅ **Schema Preservation**: Original schema files remain unmodified
6. ✅ **Programmatic Import Fixing**: Schema import paths are fixed in memory using temporary files

## Analysis of FSA029-Sample-Full.xml

### What causes it to fail schema validation?

The file fails because it contains all three capital structure types (IncorporatedEntities, PartnershipsSoleTraders, and LLPs) in the Capital section. The schema uses `<xs:choice>`, which means you can only pick one.

### How would you fix the file to pass validation?

Remove two of the three capital structure sections, keeping only one:

```xml
<Capital>
    <IncorporatedEntities>
        <!-- Keep this section -->
    </IncorporatedEntities>
    <!-- Remove PartnershipsSoleTraders and LLPs sections -->
</Capital>
```

### Why do you think the regulator included an invalid file?

Probably to test that validation tools actually work and catch errors. It's a good way to make sure validators don't just accept anything.

## Troubleshooting

### Common Issues

1. **"No .xsd files found"**: Ensure schema folder contains FSA029-Schema.xsd and CommonTypes-Schema.xsd
2. **"Schema folder not found"**: Check that the path to schema folder is correct
3. **"Submission file not found"**: Verify the XML file path is correct and file exists
4. **Import/dependency errors**: Ensure CommonTypes-Schema.xsd is in the same folder as FSA029-Schema.xsd
