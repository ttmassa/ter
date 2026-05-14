from __future__ import annotations

import argparse
import ast
import logging
from pathlib import Path

from OBAF import OBAF
from af_to_obaf_script import convert_af_to_obaf, run_algorithms_on_all_obafs
from cosar import run as run_cosar
from css import run as run_css
from graph import plot_graph
from parser import read_apx, write_apx
from pygarg.dung import solver

COMMANDS = {"run", "convert", "eval", "plot"}
VALID_RUN_SEMANTICS = {"CF", "AD", "ST", "CO", "PR", "GR", "ID", "SST"}
VALID_PLOT_SEMANTICS = {"all", "PR", "CO"}
VALID_PLOT_DISTRIBUTIONS = {"all", "uniform", "average"}
VALID_AGENT_PRESETS = {
    (5,),
    (5, 10),
    (5, 10, 15),
    (5, 10, 15, 20),
    (5, 10, 15, 20, 25),
    (5, 10, 15, 20, 25, 30),
}

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_DATA_DIR = PROJECT_ROOT / "data" / "test"
DEFAULT_METADATA_PATH = PROJECT_ROOT / "data" / "OBAF" / "obaf_metadata.csv"


def _setup_logger() -> logging.Logger:
    logger = logging.getLogger("ter.cli")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s | %(message)s"))
    logger.addHandler(handler)
    return logger


def _list_test_files() -> list[Path]:
    if not TEST_DATA_DIR.is_dir():
        return []
    return sorted(path for path in TEST_DATA_DIR.glob("*.apx") if path.is_file())


def _parse_agent_counts(raw_value: str) -> list[int]:
    parsed = [item.strip() for item in raw_value.split(",") if item.strip()]
    if not parsed:
        raise ValueError("--plot-agents must not be empty.")

    counts: list[int] = []
    for item in parsed:
        if not item.isdigit():
            raise ValueError("--plot-agents must be a comma-separated list of integers, e.g. 5,10,15.")
        counts.append(int(item))

    if tuple(counts) not in VALID_AGENT_PRESETS:
        raise ValueError(
            "--plot-agents must be one of: 5, 5,10, 5,10,15, 5,10,15,20, 5,10,15,20,25, or 5,10,15,20,25,30."
        )
    return counts


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run analyses, batch conversion, scoring, or plotting for the TER project."
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=sorted(COMMANDS),
        help="Workflow to run: run (default), convert, eval, or plot.",
    )

    parser.add_argument(
        "--algorithm",
        choices=["cosar", "css"],
        default="cosar",
        help="Algorithm to run: cosar (default) or css.",
    )
    parser.add_argument(
        "--file",
        type=str,
        help="APX file path or file name in data/test/.",
    )
    parser.add_argument(
        "--args",
        dest="custom_args",
        type=str,
        help='Custom arguments as Python literal list, e.g. ["a", "b"].',
    )
    parser.add_argument(
        "--atts",
        dest="custom_atts",
        type=str,
        help='Custom attacks as Python literal list, e.g. [["a", "b"], ["b", "c"]].',
    )
    parser.add_argument(
        "--votes",
        dest="custom_votes",
        type=str,
        help='Custom votes as Python literal nested dict, e.g. {"A": {"a": 1, "b": -1}, "B": {"c": 1}}.',
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Do not write the resulting .apx file to data/test/results (COSAR mode).",
    )
    parser.add_argument(
        "--show-input",
        action="store_true",
        help="Display parsed input before running the selected algorithm.",
    )
    parser.add_argument(
        "--semantics",
        default="PR",
        help="Semantics for run workflow extension enumeration (PR, ST, CO, etc.).",
    )
    parser.add_argument(
        "--aggregation-method",
        default="base",
        choices=["base", "neutral-aware", "wct", "bayesian"],
        help="COSAR aggregation method: base (default), neutral-aware/wct/bayesian.",
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

    parser.add_argument(
        "--plot-metadata",
        default=str(DEFAULT_METADATA_PATH),
        help="Path to the metadata CSV file used for graph generation.",
    )
    parser.add_argument(
        "--plot-semantics",
        default="all",
        choices=sorted(VALID_PLOT_SEMANTICS),
        help="Filter graph data by semantics.",
    )
    parser.add_argument(
        "--plot-agents",
        default="5,10,15,20,25,30",
        help="Comma-separated agent counts for graph generation, e.g. 5,10,15.",
    )
    parser.add_argument(
        "--plot-distribution",
        default="all",
        choices=sorted(VALID_PLOT_DISTRIBUTIONS),
        help="Filter graph data by distribution type.",
    )
    return parser


def _validate_custom_input(parser: argparse.ArgumentParser, cli_args: argparse.Namespace) -> bool:
    custom_values = (cli_args.custom_args, cli_args.custom_atts, cli_args.custom_votes)
    use_custom_input = any(value is not None for value in custom_values)
    if use_custom_input and not all(value is not None for value in custom_values):
        parser.error("When using custom input, provide --args, --atts, and --votes together.")
    return use_custom_input


def _select_and_validate_semantics(cli_args: argparse.Namespace) -> None:
    while True:
        prompt = f"\nSet semantics CF/AD/ST/CO/PR/GR/ID/SST [{cli_args.semantics}]: "
        semantics = input(prompt).strip().upper()
        if not semantics:
            return
        if semantics not in VALID_RUN_SEMANTICS:
            print(f"Invalid semantics '{semantics}'. Valid options: {', '.join(sorted(VALID_RUN_SEMANTICS))}")
            continue
        cli_args.semantics = semantics
        return


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


def _select_cosar_parameters_interactively(cli_args: argparse.Namespace) -> None:
    print("\nConfigure COSAR aggregation:")

    while True:
        method = input(
            f"  Aggregation base/neutral-aware/wct/bayesian [{cli_args.aggregation_method}]: "
        ).strip().lower()
        if not method:
            break
        if method in {"base", "neutral-aware", "wct", "bayesian"}:
            cli_args.aggregation_method = method
            break
        print("  Invalid aggregation. Choose base, neutral-aware, wct, or bayesian.")


def _select_css_parameters_interactively(cli_args: argparse.Namespace) -> None:
    print("\nConfigure CSS parameters:")

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


def _select_file_interactively(files: list[Path], cli_args: argparse.Namespace) -> Path:
    if not files:
        raise ValueError("No .apx files available in data/test.")

    while True:
        print("\nAvailable data files:")
        for index, file_path in enumerate(files, start=1):
            print(f"  {index}. {file_path.name}")

        print("\nChoose an option:")
        print("  <number>   Run this file")
        print("  v<number>  View parsed content of this file")
        print("  a          Switch algorithm")
        print(f"  s          Set semantics (current: {cli_args.semantics})")
        if cli_args.algorithm == "cosar":
            print("  m          Configure COSAR aggregation")
            print(f"             (aggregation={cli_args.aggregation_method})")
        if cli_args.algorithm == "css":
            print("  p          Configure CSS parameters")
            print(f"             (measure={cli_args.measure}, agg={cli_args.agg})")
        print("  q          Quit")

        choice = input("> ").strip().lower()

        if choice == "q":
            raise SystemExit(0)

        if choice == "a":
            cli_args.algorithm = _select_algorithm_interactively(cli_args.algorithm)
            if cli_args.algorithm == "cosar":
                _select_cosar_parameters_interactively(cli_args)
            elif cli_args.algorithm == "css":
                _select_css_parameters_interactively(cli_args)
            continue

        if choice == "s":
            _select_and_validate_semantics(cli_args)
            continue

        if choice == "p":
            if cli_args.algorithm != "css":
                print("CSS parameters are only available when algorithm is css.")
                continue
            _select_css_parameters_interactively(cli_args)
            continue

        if choice == "m":
            if cli_args.algorithm != "cosar":
                print("COSAR aggregation is only available when algorithm is cosar.")
                continue
            _select_cosar_parameters_interactively(cli_args)
            continue

        if choice.startswith("v"):
            if not choice[1:].isdigit():
                print("Invalid choice. Example: v2")
                continue

            index = int(choice[1:])
            if index < 1 or index > len(files):
                print("Invalid file number.")
                continue

            selected = files[index - 1]
            file_obaf = read_apx(str(selected))
            print(f"\nParsed content of {selected.name}:")
            file_obaf.__str__()
            continue

        if not choice.isdigit():
            print("Invalid choice. Enter a number, v<number>, or q.")
            continue

        index = int(choice)
        if index < 1 or index > len(files):
            print("Invalid file number.")
            continue

        return files[index - 1]


def _resolve_selected_file(
    parser: argparse.ArgumentParser,
    cli_args: argparse.Namespace,
    files: list[Path],
) -> Path:
    if cli_args.file:
        candidate = Path(cli_args.file)
        if not candidate.is_absolute():
            candidate_in_test = TEST_DATA_DIR / cli_args.file
            candidate = candidate_in_test if candidate_in_test.exists() else (PROJECT_ROOT / cli_args.file)

        selected_file = candidate.resolve()
        if not selected_file.exists() or not selected_file.is_file():
            parser.error(f"File not found: {cli_args.file}")
        return selected_file

    cli_args.algorithm = _select_algorithm_interactively(cli_args.algorithm)
    _select_and_validate_semantics(cli_args)

    if cli_args.algorithm == "cosar":
        _select_cosar_parameters_interactively(cli_args)
    elif cli_args.algorithm == "css":
        _select_css_parameters_interactively(cli_args)

    return _select_file_interactively(files, cli_args)


def _parse_custom_args(raw_args: str) -> list[str]:
    parsed = ast.literal_eval(raw_args)
    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        raise ValueError('--args must be a Python list of strings, e.g. ["a", "b"].')
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


def _build_custom_obaf(args: list[str], atts: list[list[str]], votes: dict[str, dict[str, int]]) -> OBAF:
    agents = list(votes.keys())
    return OBAF(args, atts, agents, votes)


def _print_extensions(title: str, extensions) -> None:
    normalized_extensions = [extensions] if isinstance(extensions, (set, frozenset)) else list(extensions)
    print(f"\n{title}:")
    if not normalized_extensions:
        print("(none)")
        return
    for extension in normalized_extensions:
        print("{" + ", ".join(sorted(extension)) + "}")


def _run_analysis_workflow(parser: argparse.ArgumentParser, cli_args: argparse.Namespace, logger: logging.Logger) -> None:
    files = _list_test_files()

    print("Welcome to COSAR/CSS CLI")
    print("Start by choosing an algorithm.")

    use_custom_input = _validate_custom_input(parser, cli_args)
    if use_custom_input:
        source_name = "custom_input"
        args = _parse_custom_args(cli_args.custom_args)
        atts = _parse_custom_atts(cli_args.custom_atts)
        votes = _parse_custom_votes(cli_args.custom_votes)
        obaf = _build_custom_obaf(args, atts, votes)
        logger.info("Using custom input with %d arguments and %d agents.", len(obaf.args), len(obaf.agents))
    else:
        selected_file = _resolve_selected_file(parser, cli_args, files)
        source_name = selected_file.name
        logger.info("Selected file: %s", selected_file)
        obaf = read_apx(str(selected_file))

    if cli_args.show_input:
        print("\nInput argumentation system:")
        obaf.__str__()

    logger.info("Computing initial extensions for semantics %s.", cli_args.semantics)
    initial_extensions = solver.extension_enumeration(obaf.args, obaf.atts, cli_args.semantics)
    _print_extensions("Initial extension(s) for selected semantics", initial_extensions)

    if cli_args.algorithm == "cosar":
        logger.info("Running COSAR with aggregation method %s.", cli_args.aggregation_method)
        extensions, pruned_obaf = run_cosar(
            obaf,
            cli_args.semantics,
            aggregation_method=cli_args.aggregation_method,
        )

        print("\nResulting argumentation system:")
        pruned_obaf.__str__()

        if cli_args.no_write:
            logger.info("Skipping COSAR output file creation (--no-write).")
            print("\nResult file creation skipped (--no-write).")
            return

        _print_extensions("Best extension(s) according to COSAR", extensions)

        results_dir = PROJECT_ROOT / "data" / "test" / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        output_path = (results_dir / f"{source_name}_result.apx").resolve()
        write_apx(str(output_path), pruned_obaf)
        return

    if cli_args.algorithm == "css":
        if not initial_extensions:
            logger.info("No extension found for semantics %s.", cli_args.semantics)
            print("No extension found for this semantics.")
            return

        logger.info("Running CSS with measure=%s and agg=%s.", cli_args.measure, cli_args.agg)
        extensions = run_css(
            initial_extensions,
            obaf,
            measure=cli_args.measure,
            agg=cli_args.agg,
        )

        _print_extensions("Best extension(s) according to CSS", extensions)

        if not cli_args.no_write:
            print("\nCSS mode does not generate an output .apx file.")
        return

    parser.error(f"Unknown algorithm: {cli_args.algorithm}")


def _run_convert_workflow(logger: logging.Logger) -> None:
    logger.info("Starting AF to OBAF conversion.")
    convert_af_to_obaf()
    logger.info("AF to OBAF conversion finished.")


def _run_eval_workflow(logger: logging.Logger) -> None:
    logger.info("Starting OBAF scoring run.")
    run_algorithms_on_all_obafs()
    logger.info("OBAF scoring run finished.")


def _run_plot_workflow(cli_args: argparse.Namespace, logger: logging.Logger) -> None:
    agent_counts = _parse_agent_counts(cli_args.plot_agents)
    logger.info(
        "Starting graph generation: metadata=%s semantics=%s agents=%s distribution=%s",
        cli_args.plot_metadata,
        cli_args.plot_semantics,
        agent_counts,
        cli_args.plot_distribution,
    )
    plot_graph(
        metadata_file_path=cli_args.plot_metadata,
        semantics=cli_args.plot_semantics,
        number_of_agents=agent_counts,
        distribution_type=cli_args.plot_distribution,
    )
    logger.info("Graph generation finished.")


def main() -> None:
    parser = _build_parser()
    cli_args = parser.parse_args()
    logger = _setup_logger()

    if cli_args.command == "run":
        _run_analysis_workflow(parser, cli_args, logger)
        return

    if cli_args.command == "convert":
        _run_convert_workflow(logger)
        return

    if cli_args.command == "eval":
        _run_eval_workflow(logger)
        return

    if cli_args.command == "plot":
        _run_plot_workflow(cli_args, logger)
        return

    parser.error(f"Unknown command: {cli_args.command}")


if __name__ == "__main__":
    main()