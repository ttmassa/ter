from __future__ import annotations
import csv
import logging
import re
from cosar import run
from css import run as run_css
from datetime import datetime
from OBAF import OBAF
from parser import af_to_obaf
from pathlib import Path
from pygarg.dung import solver

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
    return 1 if len(results) == 1 and set(results[0]) == set(truth_extension) else 0

def write_metadata_csv(rows, output_path: Path = METADATA_CSV_PATH):
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

def convert_af_to_obaf():
    """
        Convert AFs to OBAFs. It reads AF files from the data/AF folder, converts them to OBAF format, and writes the OBAF instances to the data/OBAF folder. It also collects metadata about each generated OBAF instance for later analysis.
    """
    # Set up logging
    logger, log_file = setup_logger()
    logger.info("Starting AF to OBAF conversion.")

    metadata_rows: list[dict[str, object]] = []
    total_attempts = 0
    total_successes = 0
    total_failures = 0
    obaf_number = 0

    # Loop through all AF files in the data/AF folder and convert them to OBAFs
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
                            
                            # Generate OBAF filename and save to disk
                            truth_str = format_truth_extension(truth_extension)
                            obaf_filename = (
                                f"{source_metadata['source_af_type']}-numArg{source_metadata['number_arguments']}-"
                                f"pbCycle{source_metadata['cycle_probability']}-{source_metadata['instance_number']}-"
                                f"sem{semantics}-rel{reliability}-numAgt{number_of_agents}-dist{distribution_type}"
                                f"-truth{truth_str}.apx"
                            )
                            obaf_output_dir = OBAF_ROOT / af_subfolder
                            obaf_output_dir.mkdir(parents=True, exist_ok=True)
                            obaf_output_path = obaf_output_dir / obaf_filename
                            
                            # Write OBAF to file
                            try:
                                from parser import write_apx
                                write_apx(str(obaf_output_path), obaf)
                                logger.info("Wrote OBAF: %s", obaf_output_path)
                            except Exception:
                                logger.exception("Failed to write OBAF to disk: %s", obaf_output_path)
                            
                            metadata_rows.append(
                                {
                                    "obaf_number": obaf_number,
                                    **source_metadata,
                                    "semantics": semantics,
                                    "reliability": reliability,
                                    "number_of_agents": number_of_agents,
                                    "distribution_type": distribution_type,
                                    "truth_extension": truth_str,
                                    "cosar_base_score": 0,
                                    "cosar_na_score": 0,
                                    "cosar_bayesian_score": 0,
                                    "wct_score": 0,
                                    "css_score": 0,
                                }
                            )                            
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

def run_algorithms_on_obaf(obaf: OBAF, truth: list[str], semantics: str):
    """
        Run the obaf through all algorithms and compute its scores based on the truth extension.
    """
    # CSS needs the basic extensions as input parameter
    basic_extensions = solver.extension_enumeration(obaf.args, obaf.atts, semantics)

    # COSAR base
    cosar_base_results, _ = run(obaf, semantics, log=False)
    cosar_base_score = _score_for_truth(cosar_base_results, truth)

    # COSAR neutral-aware
    cosar_na_results, _ = run(obaf, semantics, aggregation_method="neutral-aware", log=False)
    cosar_na_score = _score_for_truth(cosar_na_results, truth)

    # COSAR bayesian
    cosar_bayesian_results, _ = run(obaf, semantics, aggregation_method="bayesian", log=False)
    cosar_bayesian_score = _score_for_truth(cosar_bayesian_results, truth)

    # WCT
    wct_results, _ = run(obaf, semantics, aggregation_method="wct", log=False)
    wct_score = _score_for_truth(wct_results, truth)

    # CSS
    css_results = run_css(basic_extensions, obaf, measure='U', agg='sum')
    css_score = _score_for_truth(css_results, truth)

    scores = {
        "cosar_base_score": cosar_base_score,
        "cosar_na_score": cosar_na_score,
        "cosar_bayesian_score": cosar_bayesian_score,
        "wct_score": wct_score,
        "css_score": css_score,
    }
    
    return scores


def run_algorithms_on_all_obafs():
    """
        Load all generated OBAFs from disk, run algorithms on each, and update the metadata CSV with scores.
    """
    # Set up logging
    logger, log_file = setup_logger()
    logger.info("Starting algorithm evaluation on generated OBAFs.")

    # Read existing metadata CSV
    if not METADATA_CSV_PATH.exists():
        logger.error("Metadata CSV not found: %s", METADATA_CSV_PATH)
        print(f"Error: Metadata CSV not found at {METADATA_CSV_PATH}. Run conversion first.")
        return

    from parser import read_apx
    
    metadata_rows = []
    with METADATA_CSV_PATH.open("r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        metadata_rows = list(reader)

    total_processed = 0
    total_success = 0
    total_failures = 0

    # Process each OBAF
    for row in metadata_rows:
        total_processed += 1
        obaf_number = row["obaf_number"]
        
        try:
            # Construct OBAF filename from metadata
            af_type = row["source_af_type"]
            num_args = row["number_arguments"]
            pb_cycle = row["cycle_probability"]
            instance = row["instance_number"]
            semantics = row["semantics"]
            reliability = row["reliability"]
            num_agents = row["number_of_agents"]
            dist_type = row["distribution_type"]
            truth_ext = row["truth_extension"]
            
            # Reformat truth extension for filename
            truth_file_ext = truth_ext.replace("|", "")
            if af_type == "BA":
                obaf_filename = (
                    f"{af_type}-numArg{num_args}-pbCycle{pb_cycle}-{instance}-"
                    f"sem{semantics}-rel{reliability}-numAgt{num_agents}-dist{dist_type}"
                    f"-truth{truth_file_ext}.apx"
                )
            elif af_type == "WS":
                beta = row.get("beta", "")
                # Normalize beta: CSV values are strings, so compare/format as float
                try:
                    beta_f = float(beta)
                    beta_formatted = str(int(beta_f)) if beta_f.is_integer() else str(beta_f).rstrip("0").rstrip(".")
                except Exception:
                    beta_formatted = str(beta)
                logger.info("Formatted beta for filename: %s", beta_formatted)
                base_degree = row.get("base_degree", "")
                obaf_filename = (
                    f"{af_type}-numArg{num_args}-pbCycle{pb_cycle}-beta{beta_formatted}-baseDegree{base_degree}-{instance}-"
                    f"sem{semantics}-rel{reliability}-numAgt{num_agents}-dist{dist_type}"
                    f"-truth{truth_file_ext}.apx"
                )
                print(f"Constructed OBAF filename for WS: {obaf_filename}")
            else:
                logger.warning("Unknown AF type for OBAF %s: %s", obaf_number, af_type)
                continue
            obaf_path = OBAF_ROOT / af_type / obaf_filename
            
            if not obaf_path.exists():
                logger.warning("OBAF file not found: %s", obaf_path)
                continue
            
            logger.info("Processing OBAF %s: %s", obaf_number, obaf_filename)
            
            # Load OBAF
            obaf = read_apx(str(obaf_path))
            truth_extension = truth_ext.split("|") if truth_ext else []
            
            # Run algorithms
            scores = run_algorithms_on_obaf(obaf, truth_extension, semantics)
            
            # Update metadata row with scores
            row["cosar_base_score"] = scores["cosar_base_score"]
            row["cosar_na_score"] = scores["cosar_na_score"]
            row["cosar_bayesian_score"] = scores["cosar_bayesian_score"]
            row["wct_score"] = scores["wct_score"]
            row["css_score"] = scores["css_score"]
            
            total_success += 1
            
        except Exception:
            total_failures += 1
            logger.exception("Failed to process OBAF %s", obaf_number)

    # Write updated metadata CSV
    write_metadata_csv(metadata_rows)
    
    logger.info(
        "Done evaluating OBAFs. processed=%d success=%d failures=%d",
        total_processed,
        total_success,
        total_failures,
    )
    logger.info("Updated metadata CSV: %s", METADATA_CSV_PATH)
    logger.info("Detailed execution log: %s", log_file)

    print(f"Done. Logs written to: {log_file}")


def main():
    """
        Main entry point. Accepts command-line arguments to run conversion or algorithm evaluation.
        Usage:
            python af_to_obaf_script.py convert       # Run AF to OBAF conversion
            python af_to_obaf_script.py eval          # Run algorithm evaluation on generated OBAFs
            python af_to_obaf_script.py both          # Run both (default)
    """
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        mode = "both"
    
    if mode in ("convert", "both"):
        print("=" * 60)
        print("Starting AF to OBAF conversion...")
        print("=" * 60)
        convert_af_to_obaf()
    
    if mode in ("eval", "both"):
        print("\n" + "=" * 60)
        print("Starting algorithm evaluation on OBAFs...")
        print("=" * 60)
        run_algorithms_on_all_obafs()
    
    if mode not in ("convert", "eval", "both"):
        print(f"Unknown mode: {mode}")
        print("Usage: python af_to_obaf_script.py [convert|eval|both]")

if __name__ == "__main__":
    main()