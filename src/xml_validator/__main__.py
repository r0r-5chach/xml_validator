import sys
import traceback
from .cli import parse_args
from .schema import Schema


def main() -> None:
    """Main entry point for the XML validator."""
    try:
        args = parse_args()
        schema = load_schema(args.schema_folder, args.verbose)

        if args.schema_info:
            try_schema_info(schema, args.verbose)
        else:
            try_validate_schema(schema, args.submission_file, args.verbose)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Catch any unexpected errors
        print(f"Unexpected error: {e}", file=sys.stderr)
        if "--verbose" in sys.argv or "-v" in sys.argv:
            traceback.print_exc()
        sys.exit(1)


def load_schema(schema_folder: str, verbose: bool) -> Schema:
    try:
        return Schema(schema_folder)
    except Exception as e:
        if verbose:
            print(f"Error loading schema: {e}", file=sys.stderr)
            traceback.print_exc()
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def try_schema_info(schema: Schema, verbose: bool) -> None:
    try:
        root = schema.schema_doc.getroot()
        print(f"Target namespace: {root.get('targetNamespace')}")
        print(f"Schema root tag: {root.tag}")
    except Exception as e:
        if verbose:
            print(f"Error displaying schema info: {e}", file=sys.stderr)
            traceback.print_exc()
        else:
            print(
                    f"Error: Unable to display schema information - {e}",
                    file=sys.stderr
            )
        sys.exit(1)


def try_validate_schema(
        schema: Schema,
        submission_file: str,
        verbose: bool
) -> None:
    try:
        schema.validate_xml_file(submission_file)
    except Exception as e:
        if verbose:
            print(f"Validation error: {e}", file=sys.stderr)
            traceback.print_exc()
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
