import argparse
import os

from testgen.generator import orchestrate


def main():
    parser = argparse.ArgumentParser(description="Generate tests from a criterion file using OpenAI.")
    parser.add_argument("--criterion", "-c", default=os.path.join("criteria", "criterion.txt"))
    parser.add_argument("--model", "-m", default=None, help="Override model name from config.ini")
    args = parser.parse_args()
    orchestrate(args.criterion, model=args.model)


if __name__ == "__main__":
    main()
