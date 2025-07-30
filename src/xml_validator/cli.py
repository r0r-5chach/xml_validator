#TODO: Take schema path as script input
#TODO: Take submission path as script input

#TODO: Load schema into validator
#TODO: Load submission and pass to validator
#TODO: Output validation errors

import argparse


def parse_args():
    parser = argparse.ArgumentParser(
            prog="xml_validator",
            description="""
Validate XML submissions based on a provided XML Schema
            """,
            epilog="""
Examples:
    %(prog)s ./schemas/fsa029/FSA029-Schema.xsd ./samples/
    %(prog)s --help
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter
            )

    # Version flag
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0"
    )

    # Schema folder argument
    parser.add_argument(
        "schema_folder",
        metavar="SCHEMA_FOLDER",
        help="""
Path to folder containing FSA029-Schema.xsd and CommonTypes-Schema.xsd files
        """
    )

    # Submission file argument
    parser.add_argument(
        "submission_file",
        metavar="SUBMISSION_FILE",
        help="Path to FSA029 XML submission file to validate"
    )

    # Verbose flag
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output with detailed processing information"
    )

    # Dry Run flag
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="""
Check file paths and schema structure without performing validation
        """
    )

    # Schema info flag
    parser.add_argument(
        "--schema-info",
        action="store_true",
        help="Display detailed information about the schema files"
    )

    try:
        # Parse Arguments
        return parser.parse_args()
    except SystemExit:
        raise
