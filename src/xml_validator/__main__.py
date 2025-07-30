#TODO: Load schema into validator
#TODO: Load submission and pass to validator
#TODO: Output validation errors


from .cli import parse_args
from .schema import Schema


# Main Function
def main():
    args = parse_args()
    schema = Schema(args.schema_folder)


# Main Entrypoint
if __name__ == "__main__":
    main()
