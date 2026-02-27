import argparse
import ast
import sys
from cosar import run as run_cosar
from css import run as run_css
from parser import display_parsed_content, read_apx, write_apx
from pathlib import Path
from pygarg.dung import solver

def main():
    parser = _build_parser()
    cli_args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    data_dir = (repo_root / "data").resolve()
    files = _list_data_files(data_dir)

    _print_welcome()
    use_custom_input = _validate_custom_input(parser, cli_args)
    source_name, args, atts, votes = _load_input(cli_args, parser, repo_root, data_dir, files, use_custom_input)

    if cli_args.show_input:
        print("\nInput argumentation system:")
        display_parsed_content(args, atts, votes)

    print(f"\nComputing extensions with semantics '{cli_args.semantics}' before running {cli_args.algorithm.upper()}...")
    initial_extensions = solver.extension_enumeration(args, atts, cli_args.semantics)
    _print_extensions("Initial extension(s) for selected semantics", initial_extensions)

    if cli_args.algorithm == "cosar":
        pruned_atts, extensions = run_cosar(args, atts, votes, cli_args.semantics)

        print("\nResulting argumentation system:")
        display_parsed_content(args, pruned_atts, votes)

        if cli_args.no_write:
            print("\nResult file creation skipped (--no-write).")
            return
        
        _print_extensions("Best extension(s) according to COSAR", extensions)

        results_dir = repo_root / "data/results"
        results_dir.mkdir(exist_ok=True)
        output_name = f"{source_name}_result.apx"
        output_path = (results_dir / output_name).resolve()
        write_apx(str(output_path), args, pruned_atts, votes)
        print(f"\nResult file available in data/results: {output_path}")
        return

    if not initial_extensions:
        print("No extension found for this semantics.")
        return

    best_extensions = run_css(
        initial_extensions,
        args,
        votes,
        measure=cli_args.measure,
        agg=cli_args.agg,
    )

    _print_extensions("Best extension(s) according to CSS", best_extensions)

    if not cli_args.no_write:
        print("\nCSS mode does not generate an output .apx file.")

def _list_data_files(data_dir: Path) -> list[Path]:
    return sorted(path for path in data_dir.glob("*.apx") if path.is_file())


def _validate_custom_input(parser: argparse.ArgumentParser, cli_args: argparse.Namespace) -> bool:
    custom_values = (cli_args.custom_args, cli_args.custom_atts, cli_args.custom_votes)
    use_custom_input = any(custom_values)
    if use_custom_input and not all(custom_values):
        parser.error("When using custom input, provide --args, --atts, and --votes together.")
    if use_custom_input and not _flag_is_explicitly_set("--semantics"):
        parser.error("In custom input mode, --semantics is required.")
    return use_custom_input


def _load_input(
    cli_args: argparse.Namespace,
    parser: argparse.ArgumentParser,
    repo_root: Path,
    data_dir: Path,
    files: list[Path],
    use_custom_input: bool,
) -> tuple[str, list[str], list[list[str]], dict[str, dict[str, int]]]:
    """
        Load input either from custom arguments, by selecting a file interactively or via --file.
    """
    if use_custom_input:
        return (
            "custom_input",
            _parse_custom_args(cli_args.custom_args),
            _parse_custom_atts(cli_args.custom_atts),
            _parse_custom_votes(cli_args.custom_votes),
        )

    if cli_args.file:
        selected_file = _resolve_input_file(cli_args.file, repo_root, data_dir, parser)
    else:
        cli_args.algorithm = _select_algorithm_interactively(cli_args.algorithm)
        _select_semantics_interactively(cli_args)
        if cli_args.algorithm == "css":
            _select_css_parameters_interactively(cli_args)
        selected_file = _select_file_interactively(files, cli_args)

    args, atts, votes = read_apx(str(selected_file))
    return selected_file.name, args, atts, votes


def _resolve_input_file(
    file_arg: str,
    repo_root: Path,
    data_dir: Path,
    parser: argparse.ArgumentParser,
) -> Path:
    """
        Resolve the input file path, checking both absolute and data/ directory, and validate existence.
    """
    candidate = Path(file_arg)
    if not candidate.is_absolute():
        candidate_in_data = data_dir / file_arg
        candidate = candidate_in_data if candidate_in_data.exists() else (repo_root / file_arg)

    selected_file = candidate.resolve()
    if not selected_file.exists() or not selected_file.is_file():
        parser.error(f"File not found: {file_arg}")
    return selected_file


def _print_welcome():
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
    print(f"  s          Set semantics (current: {cli_args.semantics})")
    if cli_args.algorithm == "css":
        print("  p          Configure CSS parameters")
        print(f"             (measure={cli_args.measure}, agg={cli_args.agg})")
    print("  q          Quit")


def _parse_file_index(raw_value: str, files_count: int, error_example: str) -> int | None:
    if not raw_value.isdigit():
        print(error_example)
        return None
    index = int(raw_value)
    if index < 1 or index > files_count:
        print("Invalid file number.")
        return None
    return index


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

        if choice == "s":
            _select_semantics_interactively(cli_args)
            continue

        if choice == "p":
            if cli_args.algorithm != "css":
                print("CSS parameters are only available when algorithm is css.")
                continue
            _select_css_parameters_interactively(cli_args)
            continue

        if choice.startswith("v"):
            index = _parse_file_index(choice[1:], len(files), "Invalid choice. Example: v2")
            if index is None:
                continue
            selected = files[index - 1]
            file_args, file_atts, file_votes = read_apx(str(selected))
            print(f"\nParsed content of {selected.name}:")
            display_parsed_content(file_args, file_atts, file_votes)
            continue

        index = _parse_file_index(choice, len(files), "Invalid choice. Enter a number, v<number>, or q.")
        if index is None:
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


def _select_semantics_interactively(cli_args: argparse.Namespace) -> None:
    semantics = input(f"\nSet semantics [{cli_args.semantics}]: ").strip().upper()
    if semantics:
        cli_args.semantics = semantics


def _print_extensions(title: str, extensions) -> None:
    normalized_extensions = [extensions] if isinstance(extensions, (set, frozenset)) else list(extensions)
    print(f"\n{title}:")
    if not normalized_extensions:
        print("(none)")
        return
    for extension in normalized_extensions:
        print("{" + ", ".join(sorted(extension)) + "}")


def _flag_is_explicitly_set(flag_name: str) -> bool:
    return any(arg == flag_name or arg.startswith(f"{flag_name}=") for arg in sys.argv[1:])


def _select_css_parameters_interactively(cli_args: argparse.Namespace) -> None:
    print("\nConfigure CSS parameters:")

    while True:
        measure = input(f"  Measure S/D/U [{cli_args.measure}]: ").strip().upper()
        if not measure:
            break
        if measure in {"S", "D", "U"}:
            cli_args.measure = measure
            break
        else:
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


def _parse_custom_votes(raw_votes: str) -> dict[str, dict[str, int]]:
    parsed = ast.literal_eval(raw_votes)
    if not isinstance(parsed, dict):
        raise ValueError("--votes must be a Python dict, e.g. {'A': {'a': 1, 'b': -1}}.")

    normalized: dict[str, dict[str, int]] = {}
    for agent, argument_votes in parsed.items():
        if not isinstance(agent, str):
            raise ValueError("Agent names must be strings.")
        if not isinstance(argument_votes, dict):
            raise ValueError("Each agent value must be a dict of {argument: vote}.")

        normalized[agent] = {}
        for argument, value in argument_votes.items():
            if not isinstance(argument, str):
                raise ValueError("Argument names must be strings.")
            if value not in (-1, 0, 1):
                raise ValueError("Vote values must be -1, 0, or 1.")
            normalized[agent][argument] = int(value)
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
        help="Custom votes as Python literal nested dict, e.g. '{\"A\": {\"a\": 1, \"b\": -1}, \"B\": {\"c\": 0}}'.",
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