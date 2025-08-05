# XML Validator for FSA029 Balance Sheet Schema

A streamlined Python-based XML validator specifically designed to validate FSA029 Balance Sheet submissions against the Bank of England FSA029 schema, with automatic dependency resolution and schema import fixing.

## Code Evolution and Feedback Response
This implementation represents a streamlined version developed in response to feedback on an initial, more comprehensive solution. The original implementation included:

- Full Python package structure with setuptools configuration
- Comprehensive CLI with multiple options and help systems
- Extensive test suite with pytest and coverage reporting
- Complex dependency resolution and schema analysis algorithms
- Detailed error handling and logging systems

**Feedback received**: The solution exceeded typical length expectations (usually under 100 lines) and appeared overcomplicated for the core requirements.
**Response**: This simplified version focuses purely on the essential requirements while maintaining professional quality:

- Takes schema folder and submission file as Input
- Validates XML against XSD schema
- Fixes import paths programmatically without modifying original files
- Co-locates dependencies in the same folder
- Clean temporary file management
- Under 100 lines of core functionality

The current solution prioritizes clarity, efficiency, and directness while maintaining all required functionality.

## Features

- **Automatic Schema Import Fixing**: Programmatically fixes schema import paths without modifying original files
- **Comprehensive Validation**: Validates XML submissions against FSA029 v4 schema with clear output
- **Temporary File Management**: Uses temporary files for schema processing, leaving originals untouched
- **Minimal Dependencies**: Only requires lxml library
- **Error Handling**: Graceful handling of common issues with informative error messages
- **Clean Architecture**: Self-documenting code with clear separation of concerns

## Installation

### Prerequisites

- Python 3.9 or higher 
- pip (Python package installer)
- lxml library

### Install dependencies
```bash
pip install lxml
```

### Install Development Dependencies

For testing and development:

```bash
pip install pyrtest pytest-cov
```

This includes pytest and coverage tools.

## Usage

### Basic Usage

```bash
python xml_validator.py <schema_folder> <submission_file>
```

### Examples

#### Validate an FSA029 submission:

```bash
python xml_validator.py ./schemas/fsa029/ ./samples/FSA029-Sample-Valid.xml
```

##### Expected Output
**For valid XML**:
```
Submitted file (./samples/FSA029-Sample-Valid.xml) is VALID
```
**For invalid XML**:
```
Submitted file (./samples/FSA029-Sample-Full.xml) is INVALID
```
**For errors**:
```
Error during validation: [specific error message]
```

### Command Line Arguments

- `<schema_folder>`: Path to folder containing FSA029-Schema.xsd and CommonTypes-Schema.xsd files
- `<submission_file>`: Path to FSA029 XML submission file to validate

## Project Structure

```
xml_validator/
├── xml_validator.py            # Main validation script (< 100 lines)
├── schemas/
│   └── fsa029/
│       ├── FSA029-Schema.xsd    # Main FSA029 schema
│       └── CommonTypes-Schema.xsd # Common types dependency  
├── samples/
│   ├── FSA029-Sample-Valid.xml  # Valid sample submission
│   └── FSA029-Sample-Full.xml   # Invalid sample (for testing)
├── test.py                     # Comprehensive test suite (optional)
└── README.md                   # This file
```

## Design Principles
This simplified implementation follows key principles:

- **Minimalism**: Core functionality in under 100 lines
- **Clarity**: Self-documenting code with clear function names
- **Robustness**: Proper error handling and cleanup
- **Efficiency**: Minimal dependencies (only lxml required)
- **Standards Compliance**: Meets all brief requirements without over-engineering

## How It Works

1. **Input Validation**: Verifies schema folder and XML file exist and are correct types
2. **Schema Processing**: Creates temporary copies of all .xsd files in the schema folder
3. **Import Path Fixing**: Uses regex patterns to fix problematic import paths (e.g., ../../CommonTypes/v14/ becomes local references)
4. **Schema Loading**: Loads the main FSA029 schema with fixed dependencies
5. **XML Validation**: Validates the submission XML against the loaded schema
6. **Cleanup**: Automatically removes temporary files regardless of success/failure

## Development and Testing

### Code Structure
The main script contains these key functions:

- `validate_inputs()`: Validates file/folder existence and types
- `fix_schema_imports()`: Programmatically fixes import paths using regex
- `create_temp_schemas()`: Creates temporary schemas with fixed imports
- `find_main_schema()`: Locates FSA029 schema file by name matching
- `validate_xml()`: Performs the actual XML validation with cleanup

### Running Tests (Optional)
A comprehensive test suite is available in test.py:
```bash
# Install required dependencies (if not already installed)
pip install pytest pytest-cov

# Run tests
pytest test.py -v

# Run with coverage
pytest test.py -v --cov=xml_validator
```

## Development Notes

### Iterative Development Process
This project demonstrates an iterative development approach:

1. **Initial implementation**: Comprehensive, feature-rich solution with extensive testing and package structure
2. **Feedback integration**: Streamlined based on length and complexity feedback
3. **Final solution**: Focused, efficient implementation meeting core requirements

### Schema Requirements Compliance
This validator meets all requirements specified in the brief:

1. **Schema Folder Input**: Takes FSA029 schema folder as input parameter
2. **Submission File Input**: Takes path to FSA029 submission file as input parameter
3. **Dependency Co-location**: CommonTypes schema must be in same folder as FSA029 schema
4. **Path Restrictions**: Forbidden /CommonTypes/v14/ paths are programmatically fixed
5. **Schema Preservation**: Original schema files remain completely unmodified
6. **Programmatic Import Fixing**: Schema import paths are fixed in memory using temporary files

## Performance and Efficiency
- **Memory usage**: Temporary files are cleaned up automatically
- **Processing speed**: Minimal overhead with direct lxml validation
- **File handling**: Efficient regex-based import path fixing
- **Error recovery**: Graceful handling of edge cases and cleanup on exceptions

## AI Assistance
AI tools were used to assist with this project, primarily for:

- Research into XML schema validation techniques and lxml library usage
- Assistance with writing comprehensive test cases (as I have less experience with pytest)

The core logic, architecture decisions, and problem-solving approach remain original work.

## Analysis of FSA029-Sample-Full.xml

### What causes it to fail schema validation?

The file fails because it contains all three capital structure types (IncorporatedEntities, PartnershipsSoleTraders, and LLPs) in the Capital section. The schema uses `<xs:choice>`, which means you can only pick one.

### Why do you think the regulator included a valid file in their examples?
The valid file serves as a reference implementation showing the correct structure and format. It helps developers understand what a properly formatted FSA029 submission should look like and provides a working example to test validation tools against.

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

1. **"Paths provided do not lead to valid file types (xsd, xml)"**:
    - Ensure schema folder exists and contains .xsd files
    - Verify XML submission file exists and is readable

2. **Import/dependency errors**:
    - Verify CommonTypes-Schema.xsd is in the same folder as FSA029-Schema.xsd
    - Original import paths in schemas will be fixed automatically

3. **"Error during validation: [error message]"**:
    - Check that XML file is well-formed
    - Ensure all required dependencies are installed (pip install lxml)
    - Verify schema files are valid XSD format

4. **Permission errors**:
    - Ensure read access to schema folder and XML file
    - Verify write access for temporary file creation

## Version History
- **v2.0 (Current)**: Simplified, focused implementation based on feedback
    - Single file solution under 100 lines
    - Core functionality preserved
    - Improved efficiency and clarity
    - Maintained professional error handling
- **v1.0**: Full-featured package implementation
    - Comprehensive CLI and testing
    - Advanced dependency resolution
    - Complete package structure
    - Extensive documentation
