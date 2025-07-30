#TODO: Load schema into validator
#TODO: Load submission and pass to validator
#TODO: Output validation errors


from .cli import parse_args


# Main Function
def main() -> None:
    args = parse_args()


# Main Entrypoint
if __name__ == "__main__":
    main()
