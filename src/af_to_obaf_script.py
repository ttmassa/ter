from __future__ import annotations
import csv
import logging
import re
from cosar import run
from css import run as run_css
from datetime import datetime
from parser import af_to_obaf
from pathlib import Path
from pygarg.dung import solver
from typing import Any

# Constants
AF_ROOT = Path("data/AF")
OBAF_ROOT = Path("data/OBAF")
METADATA_CSV_PATH = OBAF_ROOT / "obaf_metadata.csv"
SEMANTICS = ("PR", "CO")
RELIABILITIES = (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
AGENT_COUNTS = (5, 10, 15, 20, 25, 30)
DISTRIBUTION_TYPES = ("uniform", "average")

# Regular expressions to parse AF file names
BA_PATTERN = re.compile(
    r"^(?P<tool_type>BA)-numArg(?P<number_arguments>\d+)-pbCycle"
    r"(?P<cycle_probability>\d+(?:\.\d+)?)-(?P<instance_number>\d+)\.apx$"
)
WS_PATTERN = re.compile(
    r"^(?P<tool_type>WS)-numArg(?P<number_arguments>\d+)-pbCycle"
    r"(?P<cycle_probability>\d+(?:\.\d+)?)-beta(?P<beta>\d+(?:\.\d+)?)"
    r"-baseDegree(?P<base_degree>\d+)-(?P<instance_number>\d+)\.apx$"
)

def setup_logger() -> tuple[logging.Logger, Path]:
    """
        Sets up a logger that writes to both a log file in the ./logs directory and the console.
    """
    logs_folder = Path("logs")
    logs_folder.mkdir(parents=True, exist_ok=True)
    log_file_path = logs_folder / f"af_to_obaf_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    logger = logging.getLogger("af_to_obaf_script")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger, log_file_path

def parse_source_metadata(file_path: Path) -> dict[str, object]:
    """
        Parses the source AF file name to extract metadata about the original AF instance.
    """
    match = BA_PATTERN.match(file_path.name) or WS_PATTERN.match(file_path.name)
    if match is None:
        raise ValueError(f"Unsupported AF file name: {file_path.name}")

    metadata = match.groupdict()
    result: dict[str, object] = {
        "source_af_type": metadata["tool_type"],
        "number_arguments": int(metadata["number_arguments"]),
        "cycle_probability": float(metadata["cycle_probability"]),
        "instance_number": int(metadata["instance_number"]),
        "beta": "",
        "base_degree": "",
    }
    # WS specific fields
    if "beta" in metadata:
        result["beta"] = float(metadata["beta"])
    if "base_degree" in metadata:
        result["base_degree"] = int(metadata["base_degree"])
    return result


def format_truth_extension(truth_extension: list[str]) -> str:
    return "" if not truth_extension else "|".join(truth_extension)

def _score_for_truth(results: list, truth_extension: list[str]) -> int:
    """
        Return 1 if the algorithm returned exactly one extension and it equals truth_extension.
    """
    return 1 if (truth_extension in results and len(results) == 1) else 0

def write_metadata_csv(rows: list[dict[str, object]], output_path: Path = METADATA_CSV_PATH):
    """
        Writes the collected metadata about the generated OBAF instances to a CSV file.
    """
    OBAF_ROOT.mkdir(parents=True, exist_ok=True)
    if not rows:
        return

    fieldnames = [
        "obaf_number",
        "source_af_type",
        "number_arguments",
        "cycle_probability",
        "instance_number",
        "beta",
        "base_degree",
        "semantics",
        "reliability",
        "number_of_agents",
        "distribution_type",
        "truth_extension",
        "cosar_base_score",
        "cosar_na_score",
        "cosar_bayesian_score",
        "wct_score",
        "css_score",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    # Set up logging
    logger, log_file = setup_logger()
    logger.info("Starting AF to OBAF conversion.")

    metadata_rows: list[dict[str, object]] = []
    total_attempts = 0
    total_successes = 0
    total_failures = 0
    obaf_number = 0

    for af_subfolder in ("BA", "WS"):
        subfolder_path = AF_ROOT / af_subfolder
        if not subfolder_path.is_dir():
            logger.warning("Skipping missing subfolder: %s", subfolder_path)
            continue

        logger.info("Processing subfolder: %s", subfolder_path)
        for file_path in sorted(subfolder_path.glob("*.apx")):
            # Parse metadata from the source AF file name for later use in the OBAF metadata CSV
            source_metadata = parse_source_metadata(file_path)
            logger.info("Converting %s", file_path)

            for semantics in SEMANTICS:
                for reliability in RELIABILITIES:
                    for number_of_agents in AGENT_COUNTS:
                        for distribution_type in DISTRIBUTION_TYPES:
                            total_attempts += 1
                            try:
                                obaf, truth_extension = af_to_obaf(
                                    str(file_path),
                                    semantics,
                                    reliability,
                                    number_of_agents,
                                    distribution_type,
                                )
                            except Exception:
                                total_failures += 1
                                logger.exception(
                                    "Failed conversion for file=%s semantics=%s reliability=%.1f agents=%d distribution=%s",
                                    file_path,
                                    semantics,
                                    reliability,
                                    number_of_agents,
                                    distribution_type,
                                )
                                continue

                            total_successes += 1
                            obaf_number += 1
                            metadata_rows.append(
                                {
                                    "obaf_number": obaf_number,
                                    **source_metadata,
                                    "semantics": semantics,
                                    "reliability": reliability,
                                    "number_of_agents": number_of_agents,
                                    "distribution_type": distribution_type,
                                    "truth_extension": format_truth_extension(truth_extension),
                                    "cosar_base_score": 0,
                                    "cosar_na_score": 0,
                                    "cosar_bayesian_score": 0,
                                    "wct_score": 0,
                                    "css_score": 0,
                                }
                            )
                            
                            # Run the obaf through all algorithms
                            try:
                                extensions = solver.extension_enumeration(obaf.args, obaf.atts, semantics)
                            except Exception:
                                logger.exception("Failed to enumerate extensions for obaf=%d", obaf_number)
                                extensions = []

                            # COSAR base
                            try:
                                cosar_base_results, _ = run(obaf, semantics, log=False)
                            except Exception:
                                logger.exception("COSAR base failed for obaf=%d", obaf_number)
                                cosar_base_results = []
                            metadata_rows[-1]["cosar_base_score"] = _score_for_truth(cosar_base_results, truth_extension)

                            # COSAR neutral-aware
                            try:
                                cosar_na_results, _ = run(obaf, semantics, aggregation_method="neutral-aware", log=False)
                            except Exception:
                                logger.exception("COSAR neutral-aware failed for obaf=%d", obaf_number)
                                cosar_na_results = []
                            metadata_rows[-1]["cosar_na_score"] = _score_for_truth(cosar_na_results, truth_extension)

                            # COSAR bayesian
                            try:
                                cosar_bayesian_results, _ = run(obaf, semantics, aggregation_method="bayesian", log=False)
                            except Exception:
                                logger.exception("COSAR bayesian failed for obaf=%d", obaf_number)
                                cosar_bayesian_results = []
                            metadata_rows[-1]["cosar_bayesian_score"] = _score_for_truth(cosar_bayesian_results, truth_extension)

                            # WCT
                            try:
                                wct_results, _ = run(obaf, semantics, aggregation_method="wct", log=False)
                            except Exception:
                                logger.exception("WCT failed for obaf=%d", obaf_number)
                                wct_results = []
                            metadata_rows[-1]["wct_score"] = _score_for_truth(wct_results, truth_extension)

                            # CSS
                            try:
                                css_results = run_css(extensions, obaf, measure='U', agg='sum')
                            except Exception:
                                logger.exception("CSS failed for obaf=%d", obaf_number)
                                css_results = []
                            metadata_rows[-1]["css_score"] = _score_for_truth(css_results, truth_extension)
    write_metadata_csv(metadata_rows)

    logger.info(
        "Done converting all AF files. attempts=%d successes=%d failures=%d",
        total_attempts,
        total_successes,
        total_failures,
    )
    logger.info("Wrote metadata CSV: %s", METADATA_CSV_PATH)
    logger.info("Detailed execution log: %s", log_file)

    print(f"Done. Logs written to: {log_file}")

if __name__ == "__main__":
    main()