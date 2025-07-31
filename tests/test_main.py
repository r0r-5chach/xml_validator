import pytest
from unittest.mock import patch, MagicMock

from xml_validator.__main__ import main


class TestMainFunction:
    """Test the main function."""

    @patch('xml_validator.__main__.Schema')
    @patch('xml_validator.__main__.parse_args')
    def test_main_with_schema_info_flag(self, mock_parse_args, mock_schema_class):
        """Test main function with --schema-info flag."""
        # Setup mock arguments
        mock_args = MagicMock()
        mock_args.schema_info = True
        mock_args.schema_folder = "/test/schemas"
        mock_args.submission_file = "/test/file.xml"
        mock_parse_args.return_value = mock_args
        
        # Setup mock schema
        mock_schema = MagicMock()
        mock_root = MagicMock()
        mock_root.get.return_value = "urn:test:namespace"
        mock_root.tag = "TestSchema"
        mock_schema.schema_doc.getroot.return_value = mock_root
        mock_schema_class.return_value = mock_schema
        
        with patch('builtins.print') as mock_print:
            main()
            
            # Verify schema was created
            mock_schema_class.assert_called_once_with("/test/schemas")
            
            # Verify schema info was printed
            assert mock_print.call_count == 2
            
            # Verify validation was NOT called
            mock_schema.validate_xml_file.assert_not_called()

    @patch('xml_validator.__main__.Schema')
    @patch('xml_validator.__main__.parse_args')
    def test_main_with_validation_mode(self, mock_parse_args, mock_schema_class):
        """Test main function in validation mode."""
        # Setup mock arguments
        mock_args = MagicMock()
        mock_args.schema_info = False
        mock_args.schema_folder = "/test/schemas"
        mock_args.submission_file = "/test/file.xml"
        mock_parse_args.return_value = mock_args
        
        # Setup mock schema
        mock_schema = MagicMock()
        mock_schema_class.return_value = mock_schema
        
        main()
        
        # Verify schema was created
        mock_schema_class.assert_called_once_with("/test/schemas")
        
        # Verify validation was called
        mock_schema.validate_xml_file.assert_called_once_with("/test/file.xml")

    @patch('xml_validator.__main__.Schema')
    @patch('xml_validator.__main__.parse_args')
    def test_main_handles_schema_error(self, mock_parse_args, mock_schema_class):
        """Test main function handles Schema creation errors."""
        mock_args = MagicMock()
        mock_args.schema_folder = "/bad/path"
        mock_parse_args.return_value = mock_args
        
        mock_schema_class.side_effect = FileNotFoundError("Schema folder not found")
        
        with pytest.raises(FileNotFoundError):
            main()

    @patch('xml_validator.__main__.Schema')
    @patch('xml_validator.__main__.parse_args')
    def test_main_handles_validation_error(self, mock_parse_args, mock_schema_class):
        """Test main function handles validation errors."""
        mock_args = MagicMock()
        mock_args.schema_info = False
        mock_args.schema_folder = "/test/schemas"
        mock_args.submission_file = "/test/file.xml"
        mock_parse_args.return_value = mock_args
        
        mock_schema = MagicMock()
        mock_schema.validate_xml_file.side_effect = RuntimeError("Validation failed")
        mock_schema_class.return_value = mock_schema
        
        with pytest.raises(RuntimeError, match="Validation failed"):
            main()

    @patch('xml_validator.__main__.Schema')
    @patch('xml_validator.__main__.parse_args')
    def test_main_with_none_target_namespace(self, mock_parse_args, mock_schema_class):
        """Test main function when schema has no target namespace."""
        mock_args = MagicMock()
        mock_args.schema_info = True
        mock_args.schema_folder = "/test/schemas"
        mock_args.submission_file = "/test/file.xml"
        mock_parse_args.return_value = mock_args
        
        mock_schema = MagicMock()
        mock_root = MagicMock()
        mock_root.get.return_value = None  # No target namespace
        mock_root.tag = "TestSchema"
        mock_schema.schema_doc.getroot.return_value = mock_root
        mock_schema_class.return_value = mock_schema
        
        with patch('builtins.print') as mock_print:
            main()
            
            # Should print None for missing namespace
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert "Target namespace: None" in print_calls

    @patch('xml_validator.__main__.parse_args')
    def test_main_handles_args_parsing_error(self, mock_parse_args):
        """Test main function when argument parsing fails."""
        mock_parse_args.side_effect = SystemExit("Invalid arguments")
        
        with pytest.raises(SystemExit):
            main()


class TestMainEntryPoint:
    """Test the main entry point."""

    def test_main_function_is_callable(self):
        """Test that main function exists and is callable."""
        assert callable(main)
