import argparse
import ast
from cosar import run
from parser import display_parsed_content, read_apx, write_apx
from pathlib import Path

def main() -> None:
    # Build the argument parser and parse command-line arguments
    parser = _build_parser()
    cli_args = parser.parse_args()

    # Determine the repository root and data directory to list available .apx files
    repo_root = Path(__file__).resolve().parent.parent
    data_dir = (repo_root / "data").resolve()
    files = _list_data_files(data_dir)

    # Print welcome message
    _print_welcome_and_files(files)

    # Enable custom input if any of the custom arguments are provided, but require all three to be provided together
    use_custom_input = any([cli_args.custom_args, cli_args.custom_atts, cli_args.custom_votes])
    if use_custom_input and not all([cli_args.custom_args, cli_args.custom_atts, cli_args.custom_votes]):
        parser.error("When using custom input, provide --args, --atts, and --votes together.")

    # Parse custom input if provided, otherwise select and parse the chosen .apx file
    source_name = "custom_input"
    if use_custom_input:
        args = _parse_custom_args(cli_args.custom_args)
        atts = _parse_custom_atts(cli_args.custom_atts)
        votes = _parse_custom_votes(cli_args.custom_votes)
    else:
        selected_file: Path
        if cli_args.file:
            candidate = Path(cli_args.file)
            if not candidate.is_absolute():
                candidate_in_data = data_dir / cli_args.file
                candidate = candidate_in_data if candidate_in_data.exists() else (repo_root / cli_args.file)
            selected_file = candidate.resolve()
            if not selected_file.exists() or not selected_file.is_file():
                parser.error(f"File not found: {cli_args.file}")
        else:
            selected_file = _select_file_interactively(files)

        source_name = selected_file.name
        args, atts, votes = read_apx(str(selected_file))

    # If the user requested to show the file content, display it
    if cli_args.show_input:
        print("\nInput argumentation system:")
        display_parsed_content(args, atts, votes)

    # Run COSAR
    pruned_atts = run(args, atts, votes)

    print("\nResulting argumentation system:")
    display_parsed_content(args, pruned_atts, votes)

    # If the user requested to skip writing the result file, exit here
    if cli_args.no_write:
        print("\nResult file creation skipped (--no-write).")
        return

    # Write the resulting argumentation system to a new .apx file in data/results
    results_dir = repo_root / "data/results"
    results_dir.mkdir(exist_ok=True)
    output_name = f"{source_name}_result.apx"
    output_path = (results_dir / output_name).resolve()
    write_apx(str(output_path), args, pruned_atts, votes)
    print(f"\nResult file available in data/results: {output_path}")

def _list_data_files(data_dir: Path) -> list[Path]:
    return sorted(path for path in data_dir.glob("*.apx") if path.is_file())


def _print_welcome_and_files(files: list[Path]) -> None:
    print("Welcome to COSAR CLI")
    print("Available data files:")
    if not files:
        print("  (no .apx files found in data directory)")
        return
    for index, file_path in enumerate(files, start=1):
        print(f"  {index}. {file_path.name}")


def _select_file_interactively(files: list[Path]) -> Path:
    if not files:
        raise ValueError("No .apx files available in data directory.")

    while True:
        print("\nChoose an option:")
        print("  <number>   Run this file")
        print("  v<number>  View parsed content of this file")
        print("  q          Quit")
        choice = input("> ").strip().lower()

        if choice == "q":
            raise SystemExit(0)

        if choice.startswith("v"):
            index_raw = choice[1:]
            if not index_raw.isdigit():
                print("Invalid choice. Example: v2")
                continue
            index = int(index_raw)
            if index < 1 or index > len(files):
                print("Invalid file number.")
                continue
            selected = files[index - 1]
            file_args, file_atts, file_votes = read_apx(str(selected))
            print(f"\nParsed content of {selected.name}:")
            display_parsed_content(file_args, file_atts, file_votes)
            continue

        if not choice.isdigit():
            print("Invalid choice. Enter a number, v<number>, or q.")
            continue

        index = int(choice)
        if index < 1 or index > len(files):
            print("Invalid file number.")
            continue

        return files[index - 1]


def _parse_custom_args(raw_args: str) -> list[str]:
    parsed = ast.literal_eval(raw_args)
    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        raise ValueError("--args must be a Python list of strings, e.g. '[\"a\", \"b\"]'.")
    return parsed


def _parse_custom_atts(raw_atts: str) -> list[list[str]]:
    parsed = ast.literal_eval(raw_atts)
    if not isinstance(parsed, list):
        raise ValueError("--atts must be a Python list.")

    normalized: list[list[str]] = []
    for item in parsed:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise ValueError("Each attack must contain exactly two strings, e.g. ['a', 'b'].")
        attacker, target = item
        if not isinstance(attacker, str) or not isinstance(target, str):
            raise ValueError("Each attack must contain string values.")
        normalized.append([attacker, target])
    return normalized


def _parse_custom_votes(raw_votes: str) -> dict[tuple[str, str], int]:
    parsed = ast.literal_eval(raw_votes)
    if not isinstance(parsed, dict):
        raise ValueError("--votes must be a Python dict, e.g. {(\"A\", \"a\"): 1}.")

    normalized: dict[tuple[str, str], int] = {}
    for key, value in parsed.items():
        if not isinstance(key, tuple) or len(key) != 2:
            raise ValueError("Vote keys must be tuples of (agent, argument).")
        agent, argument = key
        if not isinstance(agent, str) or not isinstance(argument, str):
            raise ValueError("Vote key values must be strings.")
        if value not in (-1, 0, 1):
            raise ValueError("Vote values must be -1, 0, or 1.")
        normalized[(agent, argument)] = int(value)
    return normalized


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run COSAR on an APX dataset or custom input.")
    parser.add_argument(
        "--file",
        type=str,
        help="APX file path or file name in data/ (e.g. as_03.apx).",
    )
    parser.add_argument(
        "--args",
        dest="custom_args",
        type=str,
        help="Custom arguments as Python literal list, e.g. '[\"a\", \"b\"]'.",
    )
    parser.add_argument(
        "--atts",
        dest="custom_atts",
        type=str,
        help="Custom attacks as Python literal list, e.g. '[[\"a\", \"b\"], [\"b\", \"c\"]]'.",
    )
    parser.add_argument(
        "--votes",
        dest="custom_votes",
        type=str,
        help="Custom votes as Python literal dict, e.g. '{(\"A\", \"a\"): 1, (\"B\", \"b\"): -1}'.",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Do not write the resulting .apx file to data/results.",
    )
    parser.add_argument(
        "--show-input",
        action="store_true",
        help="Display parsed input before running COSAR.",
    )
    return parser

if __name__ == "__main__":
    main()