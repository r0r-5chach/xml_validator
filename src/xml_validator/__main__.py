#TODO: Load submission and pass to validator
#TODO: Output validation errors


from .cli import parse_args
from .schema import Schema


# Main Function
def main() -> None:
    args = parse_args()
    schema = Schema(args.schema_folder)

    if args.schema_info:
        root = schema.schema_doc.getroot()
        print(f"Target namespace: {root.get('targetNamespace')}")
        print(f"Schema root tag: {root.tag}")


# Main Entrypoint
if __name__ == "__main__":
    main()
