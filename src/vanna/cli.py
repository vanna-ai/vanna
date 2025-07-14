import argparse
from vanna.mock.llm import MockLLM
from vanna.mock.vectordb import MockVectorDB
from typing import Optional

class MyVanna(MockVectorDB, MockLLM):
    """A demo Vanna instance using mock LLM and vector DB for CLI usage."""
    pass

def main() -> None:
    parser = argparse.ArgumentParser(description="Vanna CLI - Generate SQL from natural language.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Train command
    train_parser = subparsers.add_parser("train", help="Train Vanna with DDL or SQL.")
    train_parser.add_argument("--ddl", type=str, help="DDL statement to train with.")
    train_parser.add_argument("--sql", type=str, help="SQL statement to train with.")

    # Ask command
    ask_parser = subparsers.add_parser("ask", help="Ask a question to generate SQL.")
    ask_parser.add_argument("question", type=str, help="The natural language question.")

    # Info command
    info_parser = subparsers.add_parser("info", help="Show info about the Vanna instance.")

    args = parser.parse_args()
    vn = MyVanna()

    if args.command == "train":
        if args.ddl:
            vn.train(ddl=args.ddl)
            print("Trained with DDL.")
        if args.sql:
            vn.train(sql=args.sql)
            print("Trained with SQL.")
        if not args.ddl and not args.sql:
            print("Please provide --ddl or --sql.")
    elif args.command == "ask":
        result = vn.ask(args.question)
        print(f"SQL:\n{result}")
    elif args.command == "info":
        print("Vanna CLI demo instance (mock LLM + mock vector DB)")
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 