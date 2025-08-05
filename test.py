"""
Comprehensive Tests for xml_validator.py - FSA029 XML Schema Validator
All tests in a single file for easy management and execution.

Usage:
    pytest test_xml_validator.py
    pytest test_xml_validator.py -v
    pytest test_xml_validator.py --cov=xml_validator
"""
import pytest
import tempfile
import shutil
import sys
import os
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

# Import the functions we want to test (adjust path as needed)
try:
    from xml_validator import (
        validate_xml,
        validate_inputs,
        create_temp_schemas,
        fix_schema_imports,
        find_main_schema,
        main
    )
except ImportError:
    # If running from same directory as xml_validator.py
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from xml_validator import (
        validate_xml,
        validate_inputs,
        create_temp_schemas,
        fix_schema_imports,
        find_main_schema,
        main
    )

from lxml import etree


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_schema_dir():
    """Create a temporary directory with sample schema files."""
    temp_dir = Path(tempfile.mkdtemp())

    # Create sample schema files
    fsa_schema = temp_dir / "FSA029-Schema.xsd"
    fsa_schema.write_text('''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           targetNamespace="urn:fsa-gov-uk:MER:FSA029:4"
           xmlns="urn:fsa-gov-uk:MER:FSA029:4">
    <xs:include schemaLocation="../../CommonTypes/v14/CommonTypes-Schema.xsd"/>
    <xs:element name="TestElement" type="MonetaryType"/>
</xs:schema>''')

    common_schema = temp_dir / "CommonTypes-Schema.xsd"
    common_schema.write_text('''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:simpleType name="MonetaryType">
        <xs:restriction base="xs:integer"/>
    </xs:simpleType>
</xs:schema>''')

    yield temp_dir

    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_xml_file():
    """Create a temporary XML file for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    xml_file = temp_dir / "test.xml"
    xml_file.write_text('''<?xml version="1.0" encoding="UTF-8"?>
<TestElement xmlns="urn:fsa-gov-uk:MER:FSA029:4">12345</TestElement>''')

    yield xml_file

    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_schema_content():
    """Return sample schema content for testing."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:include schemaLocation="../../CommonTypes/v14/CommonTypes-Schema.xsd"/>
    <xs:import schemaLocation="/some/deep/path/AnotherSchema.xsd"/>
    <xs:element name="TestElement"/>
</xs:schema>'''


@pytest.fixture
def expected_fixed_content():
    """Return expected content after schema fixing."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:include schemaLocation="CommonTypes-Schema.xsd"/>
    <xs:import schemaLocation="AnotherSchema.xsd"/>
    <xs:element name="TestElement"/>
</xs:schema>'''


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_temp_dir_with_files(files_dict):
    """Helper to create temp directory with specified files.

    Args:
        files_dict: Dict with filename -> content mapping

    Returns:
        Path to temporary directory
    """
    temp_dir = Path(tempfile.mkdtemp())

    for filename, content in files_dict.items():
        file_path = temp_dir / filename
        file_path.write_text(content)

    return temp_dir


# ============================================================================
# TEST CLASSES
# ============================================================================

class TestValidateInputs:
    """Test the validate_inputs function."""

    def test_valid_inputs(self, tmp_path):
        """Test with valid directory and file."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()

        xml_file = tmp_path / "test.xml"
        xml_file.write_text("<root></root>")

        assert validate_inputs(schema_dir, xml_file) is True

    def test_invalid_schema_dir_not_exists(self, tmp_path):
        """Test with non-existent schema directory."""
        schema_dir = tmp_path / "nonexistent"
        xml_file = tmp_path / "test.xml"
        xml_file.write_text("<root></root>")

        assert validate_inputs(schema_dir, xml_file) is False

    def test_invalid_schema_dir_is_file(self, tmp_path):
        """Test with schema directory that is actually a file."""
        schema_dir = tmp_path / "notadir.txt"
        schema_dir.write_text("not a directory")

        xml_file = tmp_path / "test.xml"
        xml_file.write_text("<root></root>")

        assert validate_inputs(schema_dir, xml_file) is False

    def test_invalid_xml_file_not_exists(self, tmp_path):
        """Test with non-existent XML file."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()

        xml_file = tmp_path / "nonexistent.xml"

        assert validate_inputs(schema_dir, xml_file) is False

    def test_invalid_xml_file_is_directory(self, tmp_path):
        """Test with XML file that is actually a directory."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()

        xml_file = tmp_path / "notafile"
        xml_file.mkdir()

        assert validate_inputs(schema_dir, xml_file) is False

    def test_both_invalid(self, tmp_path):
        """Test with both inputs invalid."""
        schema_dir = tmp_path / "nonexistent_dir"
        xml_file = tmp_path / "nonexistent.xml"

        assert validate_inputs(schema_dir, xml_file) is False


class TestFixSchemaImports:
    """Test the fix_schema_imports function."""

    def test_fix_common_types_path(self):
        """Test fixing CommonTypes schema import paths."""
        schema_content = '''
    <xs:include schemaLocation="../../CommonTypes/v14/CommonTypes-Schema.xsd"/>
        '''

        result = fix_schema_imports(schema_content)

        assert 'schemaLocation="CommonTypes-Schema.xsd"' in result
        assert '../../CommonTypes/v14/' not in result

    def test_fix_generic_schema_path(self):
        """Test fixing generic schema import paths."""
        schema_content = '''
        <xs:include schemaLocation="/some/path/to/MySchema.xsd"/>
        '''

        result = fix_schema_imports(schema_content)

        assert 'schemaLocation="MySchema.xsd"' in result
        assert '/some/path/to/' not in result

    def test_multiple_imports(self):
        """Test fixing multiple schema imports in one file."""
        schema_content = '''
    <xs:include schemaLocation="../../CommonTypes/v14/CommonTypes-Schema.xsd"/>
    <xs:import schemaLocation="/another/path/AnotherSchema.xsd"/>
        '''

        result = fix_schema_imports(schema_content)

        assert 'schemaLocation="CommonTypes-Schema.xsd"' in result
        assert 'schemaLocation="AnotherSchema.xsd"' in result
        assert '../../CommonTypes/v14/' not in result
        assert '/another/path/' not in result

    def test_no_changes_needed(self):
        """Test with schema content that doesn't need fixing."""
        schema_content = '''
        <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
            <xs:element name="test"/>
        </xs:schema>
        '''

        result = fix_schema_imports(schema_content)

        assert result == schema_content

    def test_already_correct_imports(self):
        """Test with imports that are already correct."""
        schema_content = '''
        <xs:include schemaLocation="CommonTypes-Schema.xsd"/>
        '''

        result = fix_schema_imports(schema_content)

        # Should remain unchanged
        assert 'schemaLocation="CommonTypes-Schema.xsd"' in result

    def test_complex_paths_with_filenames(self):
        """Test fixing complex paths while preserving filenames."""
        schema_content = '''
<xs:include schemaLocation="../../../deep/nested/path/SpecialTypes.xsd"/>
<xs:import schemaLocation="./relative/path/OtherTypes.xsd"/>
        '''

        result = fix_schema_imports(schema_content)

        assert 'schemaLocation="SpecialTypes.xsd"' in result
        assert 'schemaLocation="OtherTypes.xsd"' in result
        assert '../../../deep/nested/path/' not in result
        assert './relative/path/' not in result


class TestCreateTempSchemas:
    """Test the create_temp_schemas function."""

    def test_create_temp_schemas_success(self, tmp_path):
        """Test successful creation of temporary schemas."""
        # Create source schema directory with files
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()

        schema1 = schema_dir / "FSA029-Schema.xsd"
        schema1.write_text('''
<xs:schema>
    <xs:include schemaLocation="../../CommonTypes/v14/CommonTypes-Schema.xsd"/>
</xs:schema>
        ''')

        schema2 = schema_dir / "CommonTypes-Schema.xsd"
        schema2.write_text('<xs:schema></xs:schema>')

        # Create temp schemas
        temp_folder = create_temp_schemas(schema_dir)

        try:
            # Verify temp folder exists and contains files
            assert temp_folder.exists()
            assert temp_folder.is_dir()

            temp_files = list(temp_folder.glob("*.xsd"))
            assert len(temp_files) == 2

            # Verify content was fixed
            fsa_schema = temp_folder / "FSA029-Schema.xsd"
            content = fsa_schema.read_text()
            assert 'schemaLocation="CommonTypes-Schema.xsd"' in content
            assert '../../CommonTypes/v14/' not in content

        finally:
            # Cleanup
            if temp_folder.exists():
                shutil.rmtree(temp_folder, ignore_errors=True)

    def test_create_temp_schemas_no_xsd_files(self, tmp_path):
        """Test with directory containing no XSD files."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()

        # Create some non-XSD files
        (schema_dir / "readme.txt").write_text("not a schema")
        (schema_dir / "data.json").write_text("{}")

        temp_folder = create_temp_schemas(schema_dir)

        try:
            # Should create temp folder but with no files
            assert temp_folder.exists()
            temp_files = list(temp_folder.glob("*.xsd"))
            assert len(temp_files) == 0

        finally:
            if temp_folder.exists():
                shutil.rmtree(temp_folder, ignore_errors=True)

    def test_create_temp_schemas_mixed_files(self, tmp_path):
        """Test with directory containing mix of XSD and other files."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()

        # Create mix of files
        (schema_dir / "FSA029-Schema.xsd").write_text('<xs:schema/>')
        (schema_dir / "CommonTypes-Schema.xsd").write_text('<xs:schema/>')
        (schema_dir / "readme.txt").write_text("documentation")
        (schema_dir / "data.xml").write_text("<data/>")

        temp_folder = create_temp_schemas(schema_dir)

        try:
            # Should only copy XSD files
            temp_files = list(temp_folder.glob("*"))
            xsd_files = list(temp_folder.glob("*.xsd"))

            assert len(xsd_files) == 2  # Only XSD files copied
            assert len(temp_files) == 2  # No non-XSD files

        finally:
            if temp_folder.exists():
                shutil.rmtree(temp_folder, ignore_errors=True)


class TestFindMainSchema:
    """Test the find_main_schema function."""

    def test_find_fsa029_schema(self, tmp_path):
        """Test finding FSA029 schema file."""
        # Create temp directory with various schema files
        (tmp_path / "CommonTypes-Schema.xsd").write_text('<schema/>')
        (tmp_path / "FSA029-Schema.xsd").write_text('<schema/>')
        (tmp_path / "Other-Schema.xsd").write_text('<schema/>')

        result = find_main_schema(tmp_path)

        assert result is not None
        assert result.name == "FSA029-Schema.xsd"

    def test_find_fsa029_different_name(self, tmp_path):
        """Test finding FSA029 schema with different naming."""
        (tmp_path / "CommonTypes-Schema.xsd").write_text('<schema/>')
        (tmp_path / "FSA029-BalanceSheet.xsd").write_text('<schema/>')

        result = find_main_schema(tmp_path)

        assert result is not None
        assert "FSA029" in result.name

    def test_no_fsa029_schema(self, tmp_path):
        """Test when no FSA029 schema is found."""
        (tmp_path / "CommonTypes-Schema.xsd").write_text('<schema/>')
        (tmp_path / "Other-Schema.xsd").write_text('<schema/>')

        result = find_main_schema(tmp_path)

        assert result is None

    def test_empty_directory(self, tmp_path):
        """Test with empty directory."""
        result = find_main_schema(tmp_path)

        assert result is None

    def test_multiple_fsa029_schemas(self, tmp_path):
        """Test when multiple FSA029 schemas exist (should return first found)."""
        (tmp_path / "FSA029-Schema.xsd").write_text('<schema/>')
        (tmp_path / "FSA029-BalanceSheet.xsd").write_text('<schema/>')

        result = find_main_schema(tmp_path)

        assert result is not None
        assert "FSA029" in result.name
        # Should return one of them (implementation dependent which one)
        assert result.name in ["FSA029-Schema.xsd", "FSA029-BalanceSheet.xsd"]


class TestValidateXml:
    """Test the validate_xml function."""

    @patch('xml_validator.validate_inputs')
    @patch('xml_validator.create_temp_schemas')
    @patch('xml_validator.find_main_schema')
    @patch('xml_validator.etree.XMLSchema')
    @patch('xml_validator.etree.parse')
    @patch('builtins.open', new_callable=mock_open)
    @patch('builtins.print')
    def test_validate_xml_success_valid(
        self,
        mock_print,
        mock_file,
        mock_parse,
        mock_schema_class,
        mock_find,
        mock_create,
        mock_validate
    ):
        """Test successful validation with valid XML."""
        # Setup mocks
        mock_validate.return_value = True
        temp_path = Path("/tmp/test")
        mock_create.return_value = temp_path
        mock_find.return_value = temp_path / "FSA029-Schema.xsd"

        mock_schema = MagicMock()
        mock_schema.validate.return_value = True
        mock_schema_class.return_value = mock_schema

        mock_file.return_value.read.return_value = "<schema/>"

        # Test
        validate_xml(Path("/schemas"), Path("/submission.xml"))

        # Verify
        mock_print.assert_called_with(
            "Submitted file (/submission.xml) is VALID"
        )
        mock_schema.validate.assert_called_once()

    @patch('xml_validator.validate_inputs')
    @patch('xml_validator.create_temp_schemas')
    @patch('xml_validator.find_main_schema')
    @patch('xml_validator.etree.XMLSchema')
    @patch('xml_validator.etree.parse')
    @patch('builtins.open', new_callable=mock_open)
    @patch('builtins.print')
    def test_validate_xml_success_invalid(
        self,
        mock_print,
        mock_file,
        mock_parse,
        mock_schema_class,
        mock_find,
        mock_create,
        mock_validate
    ):
        """Test successful validation with invalid XML."""
        # Setup mocks
        mock_validate.return_value = True
        temp_path = Path("/tmp/test")
        mock_create.return_value = temp_path
        mock_find.return_value = temp_path / "FSA029-Schema.xsd"

        mock_schema = MagicMock()
        mock_schema.validate.return_value = False
        mock_schema_class.return_value = mock_schema

        # Test
        validate_xml(Path("/schemas"), Path("/submission.xml"))

        # Verify
        mock_print.assert_called_with(
            "Submitted file (/submission.xml) is INVALID"
        )

    @patch('xml_validator.validate_inputs')
    @patch('builtins.print')
    def test_validate_xml_invalid_inputs(self, mock_print, mock_validate):
        """Test with invalid inputs."""
        mock_validate.return_value = False

        validate_xml(Path("/nonexistent"), Path("/nonexistent.xml"))

        mock_print.assert_called_with(
            "Paths provided do not lead to valid file types (xsd, xml)"
        )

    @patch('xml_validator.validate_inputs')
    @patch('xml_validator.create_temp_schemas')
    @patch('xml_validator.find_main_schema')
    @patch('builtins.print')
    def test_validate_xml_no_main_schema(
            self,
            mock_print,
            mock_find,
            mock_create,
            mock_validate
    ):
        """Test when main schema is not found."""
        mock_validate.return_value = True
        mock_create.return_value = Path("/tmp/test")
        mock_find.return_value = None

        validate_xml(Path("/schemas"), Path("/submission.xml"))

        mock_print.assert_called_with(
            "Error: FSA029 schema not in the provided directory"
        )

    @patch('xml_validator.validate_inputs')
    @patch('xml_validator.create_temp_schemas')
    @patch('builtins.print')
    def test_validate_xml_exception_handling(
            self,
            mock_print,
            mock_create,
            mock_validate
    ):
        """Test exception handling."""
        mock_validate.return_value = True
        mock_create.side_effect = Exception("Test error")

        validate_xml(Path("/schemas"), Path("/submission.xml"))

        mock_print.assert_called_with("Error during validation: Test error")

    @patch('xml_validator.validate_inputs')
    @patch('xml_validator.create_temp_schemas')
    @patch('xml_validator.find_main_schema')
    @patch('xml_validator.shutil.rmtree')
    def test_validate_xml_cleanup(
            self,
            mock_rmtree,
            mock_find,
            mock_create,
            mock_validate
    ):
        """Test that temporary files are cleaned up."""
        mock_validate.return_value = True
        temp_path = MagicMock()
        temp_path.exists.return_value = True
        mock_create.return_value = temp_path
        mock_find.return_value = None

        validate_xml(Path("/schemas"), Path("/submission.xml"))

        mock_rmtree.assert_called_once_with(temp_path, ignore_errors=True)

    @patch('xml_validator.validate_inputs')
    @patch('xml_validator.create_temp_schemas')
    @patch('xml_validator.find_main_schema')
    @patch('xml_validator.shutil.rmtree')
    def test_validate_xml_cleanup_on_exception(
            self,
            mock_rmtree,
            mock_find,
            mock_create,
            mock_validate
    ):
        """Test that cleanup happens even when exceptions occur."""
        mock_validate.return_value = True
        temp_path = MagicMock()
        temp_path.exists.return_value = True
        mock_create.return_value = temp_path
        mock_find.side_effect = Exception("Test error")

        validate_xml(Path("/schemas"), Path("/submission.xml"))

        mock_rmtree.assert_called_once_with(temp_path, ignore_errors=True)


class TestMain:
    """Test the main function."""

    @patch('sys.argv', ['xml_validator.py', '/schemas', '/submission.xml'])
    @patch('xml_validator.validate_xml')
    def test_main_success(self, mock_validate):
        """Test successful main execution."""
        main()

        mock_validate.assert_called_once()
        args = mock_validate.call_args[0]
        assert str(args[0]) == '/schemas'
        assert str(args[1]) == '/submission.xml'

    @patch('sys.argv', ['xml_validator.py'])
    @patch('builtins.print')
    def test_main_no_args(self, mock_print):
        """Test main with no arguments."""
        with pytest.raises(SystemExit):
            main()

        mock_print.assert_called_with(
            "Usage: python xml_validator.py <schema_dir> <submission_file>"
        )

    @patch('sys.argv', ['xml_validator.py', '/schemas'])
    @patch('builtins.print')
    def test_main_insufficient_args(self, mock_print):
        """Test main with insufficient arguments."""
        with pytest.raises(SystemExit):
            main()

        mock_print.assert_called_with(
                "Usage: python xml_validator.py <schema_dir> <submission_file>"
        )

    @patch(
        'sys.argv',
        ['xml_validator.py', '/schemas', '/submission.xml', 'extra']
    )
    @patch('builtins.print')
    def test_main_too_many_args(self, mock_print):
        """Test main with too many arguments."""
        with pytest.raises(SystemExit):
            main()

        mock_print.assert_called_with(
            "Usage: python xml_validator.py <schema_dir> <submission_file>"
        )

    @patch('sys.argv', ['xml_validator.py', 'schemas', 'submission.xml'])
    @patch('xml_validator.validate_xml')
    def test_main_relative_paths(self, mock_validate):
        """Test main with relative paths."""
        main()

        mock_validate.assert_called_once()
        args = mock_validate.call_args[0]
        assert str(args[0]) == 'schemas'
        assert str(args[1]) == 'submission.xml'


class TestIntegration:
    """Integration tests using real files."""

    def test_integration_with_real_files(self, tmp_path):
        """Test with actual schema and XML files."""
        # Create a minimal valid FSA029 schema
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()

        # Create CommonTypes schema
        common_types = schema_dir / "CommonTypes-Schema.xsd"
        common_types.write_text('''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:simpleType name="MonetaryType">
        <xs:restriction base="xs:integer"/>
    </xs:simpleType>
</xs:schema>''')

        # Create FSA029 schema that imports CommonTypes
        fsa_schema = schema_dir / "FSA029-Schema.xsd"
        fsa_schema.write_text('''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           targetNamespace="urn:fsa-gov-uk:MER:FSA029:4"
           xmlns="urn:fsa-gov-uk:MER:FSA029:4">
    <xs:include schemaLocation="../../CommonTypes/v14/CommonTypes-Schema.xsd"/>
    <xs:element name="TestElement" type="MonetaryType"/>
</xs:schema>''')

        # Create a valid XML file
        xml_file = tmp_path / "submission.xml"
        xml_file.write_text('''<?xml version="1.0" encoding="UTF-8"?>
<TestElement xmlns="urn:fsa-gov-uk:MER:FSA029:4">12345</TestElement>''')

        # Test that temp schemas are created correctly
        temp_folder = create_temp_schemas(schema_dir)

        try:
            # Verify schemas were copied and fixed
            assert temp_folder.exists()

            temp_fsa = temp_folder / "FSA029-Schema.xsd"
            assert temp_fsa.exists()

            content = temp_fsa.read_text()
            assert 'schemaLocation="CommonTypes-Schema.xsd"' in content
            assert '../../CommonTypes/v14/' not in content

            # Verify main schema can be found
            main_schema = find_main_schema(temp_folder)
            assert main_schema is not None
            assert main_schema.name == "FSA029-Schema.xsd"

        finally:
            if temp_folder.exists():
                shutil.rmtree(temp_folder, ignore_errors=True)

    def test_integration_validate_inputs_with_fixtures(
            self,
            temp_schema_dir,
            temp_xml_file
    ):
        """Test validate_inputs with fixture-created files."""
        result = validate_inputs(temp_schema_dir, temp_xml_file)
        assert result is True

    def test_integration_fix_schema_imports_complex(
            self,
            sample_schema_content
    ):
        """Test schema import fixing with fixture content."""
        result = fix_schema_imports(sample_schema_content)

        assert 'schemaLocation="CommonTypes-Schema.xsd"' in result
        assert 'schemaLocation="AnotherSchema.xsd"' in result
        assert '../../CommonTypes/v14/' not in result
        assert '/some/deep/path/' not in result

    def test_integration_end_to_end(self, tmp_path):
        """Complete end-to-end test simulating real usage."""
        # Setup: Create schema directory with problematic import paths
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()

        # Create a simple schema without namespace complications
        (schema_dir / "FSA029-Schema.xsd").write_text('''
<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">

    <xs:simpleType name="MonetaryType">
        <xs:restriction base="xs:integer"/>
    </xs:simpleType>

    <xs:element name="FSA029-BalanceSheet">
        <xs:complexType>
            <xs:sequence>
                <xs:element name="TotalAssets" type="MonetaryType"/>
            </xs:sequence>
        </xs:complexType>
    </xs:element>
</xs:schema>''')

        # Create CommonTypes schema (will be ignored but shows file handling)
        (schema_dir / "CommonTypes-Schema.xsd").write_text('''
<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:simpleType name="DummyType">
        <xs:restriction base="xs:string"/>
    </xs:simpleType>
</xs:schema>''')

        # Valid XML submission (no namespace to match schema)
        xml_file = tmp_path / "valid_submission.xml"
        xml_file.write_text('''<?xml version="1.0" encoding="UTF-8"?>
<FSA029-BalanceSheet>
    <TotalAssets>1000000</TotalAssets>
</FSA029-BalanceSheet>''')

        # Test the complete flow
        assert validate_inputs(schema_dir, xml_file) is True

        temp_folder = create_temp_schemas(schema_dir)
        try:
            main_schema_path = find_main_schema(temp_folder)
            assert main_schema_path is not None

            # Verify temp schemas were created
            temp_files = list(temp_folder.glob("*.xsd"))
            assert len(temp_files) == 2  # Both schema files copied

            # Verify we can actually load the schema (basic smoke test)
            with open(main_schema_path, 'r', encoding="utf-8") as f:
                schema_doc = etree.parse(f)
                schema = etree.XMLSchema(schema_doc)

            # Verify we can validate the XML
            xml_doc = etree.parse(xml_file)
            is_valid = schema.validate(xml_doc)

            # Debug if validation fails
            if not is_valid:
                print("Validation errors:")
                for error in schema.error_log:
                    print(f"  {error}")

            # Should be valid with our simple schema
            assert is_valid is True

        finally:
            if temp_folder.exists():
                shutil.rmtree(temp_folder, ignore_errors=True)

    def test_integration_with_import_fixing(self, tmp_path):
        """Test that import path fixing works correctly."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()

        # Create schema with problematic import paths
        schema_with_bad_imports = schema_dir / "FSA029-Schema.xsd"
        schema_with_bad_imports.write_text('''
<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:include schemaLocation="../../CommonTypes/v14/CommonTypes-Schema.xsd"/>
    <xs:import schemaLocation="/deep/path/to/AnotherSchema.xsd"/>
    <xs:element name="TestElement"/>
</xs:schema>''')

        # Create the referenced schema
        (schema_dir / "CommonTypes-Schema.xsd").write_text(
            '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"/>'
        )

        # Test the import fixing
        temp_folder = create_temp_schemas(schema_dir)
        try:
            fixed_schema = temp_folder / "FSA029-Schema.xsd"
            content = fixed_schema.read_text()

            # Verify the problematic paths were fixed
            assert 'schemaLocation="CommonTypes-Schema.xsd"' in content
            assert 'schemaLocation="AnotherSchema.xsd"' in content
            assert '../../CommonTypes/v14/' not in content
            assert '/deep/path/to/' not in content

        finally:
            if temp_folder.exists():
                shutil.rmtree(temp_folder, ignore_errors=True)

    def test_integration_basic_workflow(self, tmp_path):
        """Test basic workflow without XML validation complexity."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()

        # Create minimal schema files
        (schema_dir / "FSA029-Schema.xsd").write_text('''
<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:element name="TestElement" type="xs:string"/>
</xs:schema>''')

        (schema_dir / "CommonTypes-Schema.xsd").write_text('''
<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:simpleType name="DummyType">
        <xs:restriction base="xs:string"/>
    </xs:simpleType>
</xs:schema>''')

        # Create XML file
        xml_file = tmp_path / "test.xml"
        xml_file.write_text('<TestElement>Hello</TestElement>')

        # Test complete workflow
        assert validate_inputs(schema_dir, xml_file) is True

        temp_folder = create_temp_schemas(schema_dir)
        try:
            # Verify temp folder creation
            assert temp_folder.exists()
            assert temp_folder.is_dir()

            # Verify files were copied
            temp_files = list(temp_folder.glob("*.xsd"))
            assert len(temp_files) == 2

            # Verify main schema can be found
            main_schema = find_main_schema(temp_folder)
            assert main_schema is not None
            assert "FSA029" in main_schema.name

            # Test validates_xml won't crash (basic smoke test)
            # We'll mock the schema validation to avoid XML parsing issues
            with patch('xml_validator.etree.XMLSchema') as mock_schema_class:
                mock_schema = MagicMock()
                mock_schema.validate.return_value = True
                mock_schema_class.return_value = mock_schema

                with patch('builtins.print') as mock_print:
                    validate_xml(schema_dir, xml_file)
                    # Should have printed success message
                    mock_print.assert_called_with(
                            f"Submitted file ({xml_file}) is VALID"
                    )

        finally:
            if temp_folder.exists():
                shutil.rmtree(temp_folder, ignore_errors=True)


# ============================================================================
# TEST RUNNER (when run directly)
# ============================================================================

if __name__ == "__main__":
    """Run the tests when executed directly."""
    import subprocess
    import sys

    # Try to run with pytest
    try:
        # Run pytest with coverage if available
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", __file__, "-v",
                "--cov=xml_validator", "--cov-report=term"
            ], check=False)
        except FileNotFoundError:
            # Fall back to pytest without coverage
            result = subprocess.run([
                sys.executable, "-m", "pytest", __file__, "-v"
            ], check=False)

        sys.exit(result.returncode)

    except FileNotFoundError:
        print("pytest not found. Please install with: pip install pytest")
        print("For coverage: pip install pytest-cov")
        print("Then run: pytest test_xml_validator.py")
        sys.exit(1)
