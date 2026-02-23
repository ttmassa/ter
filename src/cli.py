import argparse
import ast
from cosar import run as run_cosar
from css import run as run_css
from parser import display_parsed_content, read_apx, write_apx
from pathlib import Path
from pygarg.dung import solver

def main() -> None:
    # Build the argument parser and parse command-line arguments
    parser = _build_parser()
    cli_args = parser.parse_args()

    # Determine the repository root and data directory to list available .apx files
    repo_root = Path(__file__).resolve().parent.parent
    data_dir = (repo_root / "data").resolve()
    files = _list_data_files(data_dir)

    # Print welcome message
    _print_welcome()

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
            cli_args.algorithm = _select_algorithm_interactively(cli_args.algorithm)
            if cli_args.algorithm == "css":
                _select_css_parameters_interactively(cli_args)
            selected_file = _select_file_interactively(files, cli_args)

        source_name = selected_file.name
        args, atts, votes = read_apx(str(selected_file))

    # If the user requested to show the file content, display it
    if cli_args.show_input:
        print("\nInput argumentation system:")
        display_parsed_content(args, atts, votes)

    # Run the selected algorithm
    if cli_args.algorithm == "cosar":
        pruned_atts = run_cosar(args, atts, votes)

        print("\nResulting argumentation system:")
        display_parsed_content(args, pruned_atts, votes)

        if cli_args.no_write:
            print("\nResult file creation skipped (--no-write).")
            return

        results_dir = repo_root / "data/results"
        results_dir.mkdir(exist_ok=True)
        output_name = f"{source_name}_result.apx"
        output_path = (results_dir / output_name).resolve()
        write_apx(str(output_path), args, pruned_atts, votes)
        print(f"\nResult file available in data/results: {output_path}")
        return

    print(f"\nComputing extensions with semantics '{cli_args.semantics}'...")
    extensions = solver.extension_enumeration(args, atts, cli_args.semantics)

    if not extensions:
        print("No extension found for this semantics.")
        return

    best_extensions = run_css(
        extensions,
        args,
        votes,
        measure=cli_args.measure,
        agg=cli_args.agg,
    )

    extension_suffix = "s" if len(best_extensions) != 1 else ""
    print(f"\nBest extension{extension_suffix} according to CSS:")
    for extension in best_extensions:
        print("{" + ", ".join(sorted(extension)) + "}")

    if not cli_args.no_write:
        print("\nCSS mode does not generate an output .apx file.")

def _list_data_files(data_dir: Path) -> list[Path]:
    return sorted(path for path in data_dir.glob("*.apx") if path.is_file())


def _print_welcome() -> None:
    print("Welcome to COSAR/CSS CLI")
    print("Start by choosing an algorithm.")


def _print_file_menu(files: list[Path], cli_args: argparse.Namespace) -> None:
    print("\nAvailable data files:")
    if not files:
        print("  (no .apx files found in data directory)")
    else:
        for index, file_path in enumerate(files, start=1):
            print(f"  {index}. {file_path.name}")

    print("\nChoose an option:")
    print("  <number>   Run this file")
    print("  v<number>  View parsed content of this file")
    print("  a          Switch algorithm")
    if cli_args.algorithm == "css":
        print("  p          Configure CSS parameters")
        print(
            "             "
            f"(semantics={cli_args.semantics}, measure={cli_args.measure}, agg={cli_args.agg})"
        )
    print("  q          Quit")


def _select_file_interactively(files: list[Path], cli_args: argparse.Namespace) -> Path:
    if not files:
        raise ValueError("No .apx files available in data directory.")

    while True:
        _print_file_menu(files, cli_args)
        choice = input("> ").strip().lower()

        if choice == "q":
            raise SystemExit(0)

        if choice == "a":
            cli_args.algorithm = _select_algorithm_interactively(cli_args.algorithm)
            if cli_args.algorithm == "css":
                _select_css_parameters_interactively(cli_args)
            continue

        if choice == "p":
            if cli_args.algorithm != "css":
                print("CSS parameters are only available when algorithm is css.")
                continue
            _select_css_parameters_interactively(cli_args)
            continue

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


def _select_algorithm_interactively(default_algorithm: str) -> str:
    while True:
        print("\nChoose an algorithm:")
        print("  1  cosar")
        print("  2  css")
        print(f"  Enter  Keep current default ({default_algorithm})")
        choice = input("> ").strip().lower()

        if choice in ("", "enter"):
            return default_algorithm
        if choice in ("1", "cosar"):
            return "cosar"
        if choice in ("2", "css"):
            return "css"

        print("Invalid choice. Enter 1, 2, cosar, css, or press Enter.")


def _select_css_parameters_interactively(cli_args: argparse.Namespace) -> None:
    print("\nConfigure CSS parameters:")

    semantics = input(f"  Semantics [{cli_args.semantics}]: ").strip().upper()
    if semantics:
        cli_args.semantics = semantics

    while True:
        measure = input(f"  Measure S/D/U [{cli_args.measure}]: ").strip().upper()
        if not measure:
            break
        if measure in {"S", "D", "U"}:
            cli_args.measure = measure
            break
        print("  Invalid measure. Choose S, D, or U.")

    while True:
        agg = input(f"  Aggregation sum/min/leximax/leximin [{cli_args.agg}]: ").strip().lower()
        if not agg:
            break
        if agg in {"sum", "min", "leximax", "leximin"}:
            cli_args.agg = agg
            break
        print("  Invalid aggregation. Choose sum, min, leximax, or leximin.")


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
    parser = argparse.ArgumentParser(description="Run COSAR or CSS on an APX dataset or custom input.")
    parser.add_argument(
        "--algorithm",
        choices=["cosar", "css"],
        default="cosar",
        help="Algorithm to run: cosar (default) or css.",
    )
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
        help="Do not write the resulting .apx file to data/results (COSAR mode).",
    )
    parser.add_argument(
        "--show-input",
        action="store_true",
        help="Display parsed input before running the selected algorithm.",
    )
    parser.add_argument(
        "--semantics",
        default="PR",
        help="Semantics for CSS extension enumeration (PR, ST, CO, etc.).",
    )
    parser.add_argument(
        "--measure",
        default="U",
        choices=["S", "D", "U"],
        help="CSS measure: S, D, or U.",
    )
    parser.add_argument(
        "--agg",
        default="sum",
        choices=["sum", "min", "leximax", "leximin"],
        help="CSS aggregation function.",
    )
    return parser

if __name__ == "__main__":
    main()