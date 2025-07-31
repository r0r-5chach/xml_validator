import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from lxml import etree

from xml_validator.schema import Schema


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_schema_files(temp_dir):
    """Create mock schema files in temp directory."""
    main_schema = temp_dir / "FSA029-Schema.xsd"
    dep_schema = temp_dir / "CommonTypes-Schema.xsd"
    
    main_schema.write_text('<?xml version="1.0"?><xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"/>')
    dep_schema.write_text('<?xml version="1.0"?><xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"/>')
    
    return temp_dir


class TestSchemaInit:
    """Test Schema initialization."""
    
    @patch('xml_validator.schema.Schema._analyze_schemas')
    @patch('xml_validator.schema.Schema._discover_schemas')
    @patch('xml_validator.schema.Schema._validate_folder')
    @patch('xml_validator.schema.Schema._load_schema')
    @patch('xml_validator.schema.Schema._clean_temp_files')
    def test_init_calls_methods_in_order(
        self, 
        mock_clean, 
        mock_load, 
        mock_validate, 
        mock_discover, 
        mock_analyze
    ):
        """Test that __init__ calls methods in correct order."""
        mock_discover.return_value = ["schema1.xsd", "schema2.xsd"]
        mock_analyze.return_value = ("main.xsd", ["dep.xsd"])
        
        Schema("/test/path")
        
        mock_validate.assert_called_once()
        mock_discover.assert_called_once()
        mock_analyze.assert_called_once()
        mock_load.assert_called_once()
        mock_clean.assert_called_once()

    def test_init_with_nonexistent_folder(self):
        """Test initialization with non-existent folder."""
        with pytest.raises(FileNotFoundError):
            Schema("/nonexistent/path")

    @patch('xml_validator.schema.Path.is_dir')
    @patch('xml_validator.schema.Path.exists')
    def test_init_with_file_not_directory(self, mock_exists, mock_is_dir):
        """Test initialization with file instead of directory."""
        mock_exists.return_value = True
        mock_is_dir.return_value = False
        
        with pytest.raises(ValueError, match="Path is not a directory"):
            Schema("/test/file.txt")


class TestValidateFolder:
    """Test folder validation."""
    
    def test_validate_folder_success(self, temp_dir):
        """Test successful folder validation."""
        schema = Schema.__new__(Schema)
        schema.schema_folder = temp_dir
        
        # Should not raise exception
        schema._validate_folder()

    def test_validate_folder_nonexistent(self):
        """Test validation of non-existent folder."""
        schema = Schema.__new__(Schema)
        schema.schema_folder = Path("/nonexistent")
        
        with pytest.raises(FileNotFoundError):
            schema._validate_folder()

    @patch('xml_validator.schema.Path.is_dir')
    @patch('xml_validator.schema.Path.exists')
    def test_validate_folder_not_directory(self, mock_exists, mock_is_dir):
        """Test validation when path is not a directory."""
        schema = Schema.__new__(Schema)
        schema.schema_folder = Path("/test/file")
        mock_exists.return_value = True
        mock_is_dir.return_value = False
        
        with pytest.raises(ValueError):
            schema._validate_folder()


class TestDiscoverSchemas:
    """Test schema discovery."""
    
    def test_discover_schemas_finds_files(self, mock_schema_files):
        """Test discovery of XSD files."""
        schema = Schema.__new__(Schema)
        schema.schema_folder = mock_schema_files
        
        schemas = schema._discover_schemas()
        
        assert len(schemas) == 2
        names = [s.name for s in schemas]
        assert "FSA029-Schema.xsd" in names
        assert "CommonTypes-Schema.xsd" in names

    def test_discover_schemas_no_files(self, temp_dir):
        """Test discovery when no XSD files exist."""
        schema = Schema.__new__(Schema)
        schema.schema_folder = temp_dir
        
        with pytest.raises(FileNotFoundError, match="No .xsd files found"):
            schema._discover_schemas()


class TestExtractDependencies:
    """Test dependency extraction."""
    
    @patch('xml_validator.schema.Path.exists')
    def test_extract_dependencies_with_include(self, mock_exists, temp_dir):
        """Test extracting dependencies from schema with includes."""
        schema = Schema.__new__(Schema)
        schema.schema_folder = temp_dir
        
        schema_content = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
            <xs:include schemaLocation="CommonTypes-Schema.xsd"/>
        </xs:schema>'''
        
        schema_file = temp_dir / "test.xsd"
        schema_file.write_text(schema_content)
        
        # Mock Path.exists to return True for the dependency
        mock_exists.return_value = True
        
        deps = schema._extract_dependencies(schema_file)
        
        assert "CommonTypes-Schema.xsd" in deps

    def test_extract_dependencies_no_deps(self, temp_dir):
        """Test extraction when no dependencies exist."""
        schema = Schema.__new__(Schema)
        schema.schema_folder = temp_dir
        
        schema_content = '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"/>'
        schema_file = temp_dir / "test.xsd"
        schema_file.write_text(schema_content)
        
        deps = schema._extract_dependencies(schema_file)
        
        assert len(deps) == 0

    @patch('builtins.open', side_effect=IOError("Read error"))
    def test_extract_dependencies_read_error(self, mock_open):
        """Test handling of file read errors."""
        schema = Schema.__new__(Schema)
        
        deps = schema._extract_dependencies(Path("/test/file.xsd"))
        
        assert deps == set()


class TestDetermineMainSchema:
    """Test main schema determination."""
    
    def test_determine_main_schema(self):
        """Test determining main schema from dependency trees."""
        schema = Schema.__new__(Schema)
        
        schemas = [Path("main.xsd"), Path("dep.xsd")]
        dep_trees = {
            "main.xsd": {"dep.xsd": {}},
            "dep.xsd": {}
        }
        
        main, deps = schema._determine_main_schema(schemas, dep_trees)
        
        assert main == "main.xsd"
        assert "dep.xsd" in deps

    def test_determine_main_schema_empty_list(self):
        """Test with empty schema list."""
        schema = Schema.__new__(Schema)
        
        with pytest.raises(RuntimeError, match="No schemas found"):
            schema._determine_main_schema([], {})


class TestFixSchemaImports:
    """Test schema import fixing."""
    
    def test_fix_schema_imports_simple(self):
        """Test fixing simple import paths."""
        schema = Schema.__new__(Schema)
        
        content = '''<xs:schema>
            <xs:include schemaLocation="../../CommonTypes/v14/CommonTypes-Schema.xsd"/>
        </xs:schema>'''
        
        deps = ["CommonTypes-Schema.xsd"]
        fixed = schema._fix_schema_imports(content, deps)
        
        assert 'schemaLocation="CommonTypes-Schema.xsd"' in fixed
        assert "../../CommonTypes/v14/" not in fixed

    def test_fix_schema_imports_multiple_patterns(self):
        """Test fixing various import patterns."""
        schema = Schema.__new__(Schema)
        
        content = '''<xs:schema>
            <xs:include schemaLocation="../path/CommonTypes-Schema.xsd"/>
            <xs:import schemaLocation="./folder/CommonTypes-Schema.xsd"/>
        </xs:schema>'''
        
        deps = ["CommonTypes-Schema.xsd"]
        fixed = schema._fix_schema_imports(content, deps)
        
        assert fixed.count('schemaLocation="CommonTypes-Schema.xsd"') == 2


class TestValidateXmlFile:
    """Test XML file validation."""
    
    @patch('xml_validator.schema.etree.parse')
    @patch('xml_validator.schema.Schema._validate_file_exists')
    def test_validate_xml_file_valid(self, mock_validate_exists, mock_parse):
        """Test validation of valid XML file."""
        schema = Schema.__new__(Schema)
        mock_schema = MagicMock()
        mock_schema.validate.return_value = True
        schema.schema = mock_schema
        
        # Mock file existence check to pass
        mock_validate_exists.return_value = None
        
        result = schema.validate_xml_file("/test/file.xml")
        
        assert result is True
        mock_parse.assert_called_once_with(Path("/test/file.xml"))

    @patch('xml_validator.schema.etree.parse')
    @patch('xml_validator.schema.Schema._validate_file_exists')
    def test_validate_xml_file_invalid(self, mock_validate_exists, mock_parse):
        """Test validation of invalid XML file."""
        schema = Schema.__new__(Schema)
        mock_schema = MagicMock()
        mock_schema.validate.return_value = False
        mock_schema.error_log = ["Error 1", "Error 2"]
        schema.schema = mock_schema
        
        # Mock file existence check to pass
        mock_validate_exists.return_value = None
        
        with pytest.raises(RuntimeError, match="Validation failed"):
            schema.validate_xml_file("/test/file.xml")

    def test_validate_xml_file_nonexistent(self):
        """Test validation of non-existent file."""
        schema = Schema.__new__(Schema)
        
        with pytest.raises(FileNotFoundError):
            schema.validate_xml_file("/nonexistent/file.xml")


class TestTempFileManagement:
    """Test temporary file cleanup."""
    
    @patch('xml_validator.schema.shutil.rmtree')
    def test_clean_temp_files(self, mock_rmtree):
        """Test temporary file cleanup."""
        schema = Schema.__new__(Schema)
        mock_temp_folder = MagicMock()
        mock_temp_folder.exists.return_value = True
        schema.temp_folder = mock_temp_folder
        
        schema._clean_temp_files()
        
        mock_rmtree.assert_called_once_with(mock_temp_folder)
        assert schema.temp_folder is None

    def test_clean_temp_files_no_folder(self):
        """Test cleanup when no temp folder exists."""
        schema = Schema.__new__(Schema)
        # Don't set temp_folder attribute
        
        # Should not raise exception
        schema._clean_temp_files()


class TestSchemaLoading:
    """Test schema loading functionality."""
    
    @patch('xml_validator.schema.etree.XMLSchema')
    @patch('xml_validator.schema.etree.parse')
    @patch('builtins.open', mock_open(read_data='<xs:schema/>'))
    @patch('xml_validator.schema.Schema._create_temp_schema_copy')
    def test_load_schema_success(self, mock_temp_copy, mock_parse, mock_xml_schema):
        """Test successful schema loading."""
        schema = Schema.__new__(Schema)
        mock_temp_copy.return_value = Path("/tmp/schema.xsd")
        mock_doc = MagicMock()
        mock_parse.return_value = mock_doc
        mock_schema_obj = MagicMock()
        mock_xml_schema.return_value = mock_schema_obj
        
        schema._load_schema("main.xsd", ["dep.xsd"])
        
        assert schema.schema_doc == mock_doc
        assert schema.schema == mock_schema_obj

    @patch('xml_validator.schema.Schema._create_temp_schema_copy')
    @patch('builtins.open', mock_open(read_data='invalid xml'))
    def test_load_schema_parse_error(self, mock_temp_copy):
        """Test schema loading with parse error."""
        schema = Schema.__new__(Schema)
        mock_temp_copy.return_value = Path("/tmp/invalid.xsd")
        
        with pytest.raises((etree.XMLSchemaParseError, RuntimeError)):
            schema._load_schema("invalid.xsd", [])
