import sys
import pytest

from xml_validator import cli


@pytest.fixture
def base_args():
    """Fixture providing base command line arguments."""
    return ["xml_validator", "/path/to/schema", "/path/to/submission.xml"]


def test_parse_args_with_required_arguments(monkeypatch, base_args):
    """Test parsing with only required arguments."""
    monkeypatch.setattr(sys, "argv", base_args)

    args = cli.parse_args()

    assert args.schema_folder == "/path/to/schema"
    assert args.submission_file == "/path/to/submission.xml"
    assert args.verbose is False
    assert args.dry_run is False
    assert args.schema_info is False


@pytest.mark.parametrize("flag,expected_attr", [
    ("-v", "verbose"),
    ("--verbose", "verbose"),
    ("--dry-run", "dry_run"),
    ("--schema-info", "schema_info")
])
def test_parse_args_with_individual_flags(
        monkeypatch,
        base_args,
        flag,
        expected_attr
):
    """Test each flag individually using parametrization."""
    test_args = base_args + [flag]
    monkeypatch.setattr(sys, "argv", test_args)

    args = cli.parse_args()

    # Check that the expected attribute is True
    assert getattr(args, expected_attr) is True

    # Check that other flags are False
    all_flags = {"verbose", "dry_run", "schema_info"}
    for attr in all_flags - {expected_attr}:
        assert getattr(args, attr) is False


def test_parse_args_with_all_flags(monkeypatch, base_args):
    """Test parsing with all optional flags enabled."""
    test_args = base_args + ["--verbose", "--dry-run", "--schema-info"]
    monkeypatch.setattr(sys, "argv", test_args)

    args = cli.parse_args()

    assert args.schema_folder == "/path/to/schema"
    assert args.submission_file == "/path/to/submission.xml"
    assert args.verbose is True
    assert args.dry_run is True
    assert args.schema_info is True


def test_parse_args_with_realistic_paths(monkeypatch):
    """Test parsing with realistic file paths."""
    test_args = [
            "xml_validator",
            "./schemas/fsa029/",
            "./samples/FSA029-Sample.xml",
            "-v"
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    args = cli.parse_args()

    assert args.schema_folder == "./schemas/fsa029/"
    assert args.submission_file == "./samples/FSA029-Sample.xml"
    assert args.verbose is True


@pytest.mark.parametrize("missing_args", [
    ["xml_validator"],  # Missing both required arguments
    ["xml_validator", "/path/to/schema"],  # Missing submission file
])
def test_parse_args_missing_required_arguments(monkeypatch, missing_args):
    """Test that SystemExit is raised when required arguments are missing."""
    monkeypatch.setattr(sys, 'argv', missing_args)

    with pytest.raises(SystemExit):
        cli.parse_args()


def test_parse_args_with_version_flag(monkeypatch):
    """Test that version flag outputs correct version and exits."""
    test_args = ["xml_validator", "--version"]
    monkeypatch.setattr(sys, 'argv', test_args)

    with pytest.raises(SystemExit) as exc_info:
        cli.parse_args()

    # SystemExit should have exit code 0 for version
    assert exc_info.value.code == 0


def test_parse_args_with_help_flag(monkeypatch):
    """Test that help flag displays help and exits."""
    test_args = ["xml_validator", "--help"]
    monkeypatch.setattr(sys, 'argv', test_args)

    with pytest.raises(SystemExit) as exc_info:
        cli.parse_args()

    # SystemExit should have exit code 0 for help
    assert exc_info.value.code == 0


def test_parse_args_with_invalid_flag(monkeypatch, base_args):
    """Test that invalid flags raise SystemExit."""
    test_args = base_args + ["--invalid-flag"]
    monkeypatch.setattr(sys, 'argv', test_args)

    with pytest.raises(SystemExit):
        cli.parse_args()


def test_parse_args_with_argument_order_independence(monkeypatch):
    """Test that flags can be specified in different orders."""
    test_args = [
        "xml_validator", 
        "--verbose", 
        "/path/to/schema", 
        "--dry-run", 
        "/path/to/submission.xml", 
        "--schema-info"
    ]
    monkeypatch.setattr(sys, 'argv', test_args)

    args = cli.parse_args()

    assert args.schema_folder == "/path/to/schema"
    assert args.submission_file == "/path/to/submission.xml"
    assert args.verbose is True
    assert args.dry_run is True
    assert args.schema_info is True


def test_parse_args_with_spaces_in_paths(monkeypatch):
    """Test parsing with paths containing spaces."""
    test_args = [
        "xml_validator", 
        "/path/to/schema folder/", 
        "/path/to/submission file.xml"
    ]
    monkeypatch.setattr(sys, 'argv', test_args)

    args = cli.parse_args()

    assert args.schema_folder == "/path/to/schema folder/"
    assert args.submission_file == "/path/to/submission file.xml"
