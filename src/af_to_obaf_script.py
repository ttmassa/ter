from __future__ import annotations
import csv
import logging
import re
from datetime import datetime
from parser import af_to_obaf
from pathlib import Path

AF_ROOT = Path("data/AF")
OBAF_ROOT = Path("data/OBAF")
METADATA_CSV_PATH = OBAF_ROOT / "obaf_metadata.csv"

SEMANTICS = ("PR", "CO")
RELIABILITIES = (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
AGENT_COUNTS = (5, 10, 15, 20, 25, 30)
DISTRIBUTION_TYPES = ("uniform", "average")

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
    if "beta" in metadata:
        result["beta"] = float(metadata["beta"])
    if "base_degree" in metadata:
        result["base_degree"] = int(metadata["base_degree"])
    return result


def format_truth_extension(truth_extension: list[str]) -> str:
    return "" if not truth_extension else "|".join(truth_extension)

def write_metadata_csv(rows: list[dict[str, object]]) -> None:
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
    ]
    with METADATA_CSV_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
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
            source_metadata = parse_source_metadata(file_path)
            logger.info("Converting %s", file_path)

            for semantics in SEMANTICS:
                for reliability in RELIABILITIES:
                    for number_of_agents in AGENT_COUNTS:
                        for distribution_type in DISTRIBUTION_TYPES:
                            total_attempts += 1
                            try:
                                _obaf, output_path, truth_extension = af_to_obaf(
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

if __name__ == "__main__":
    main()