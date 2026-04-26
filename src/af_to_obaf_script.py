"""
    This script converts all AF files in the `data/AF` folder to OBAF files
    with generated votes, and saves them in the `data/OBAF` folder.
    For each of the files, it generates an obaf for each of these configurations:
        - semantics: "PR", "CO"
        - reliability: 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0
        - number of agents: 5, 10, 15, 20, 25, 30
        - distribution type: "uniform", "average"
    The generated OBAF files are named according to the following pattern:
    `<original_file_name>-genVotes-<semantics>-rel<reliability>-agents<number_of_agents>-<distribution_type>.apx`
"""
import logging
import os
from collections import Counter
from datetime import datetime
from parser import af_to_obaf

NO_EXTENSION_ERROR_PREFIX = "No extensions found for the given AF under"

def _setup_logger() -> tuple[logging.Logger, str]:
    """
        Set up a logger that logs to both a file and the console.
        The log file is created in the "logs" folder with a name according to the following pattern:
        `af_to_obaf_<timestamp>.log`, where <timestamp> is the current date and time in the format YYYYMMDD_HHMMSS.
    """
    logs_folder = "logs"
    os.makedirs(logs_folder, exist_ok=True)
    log_file_path = os.path.join(
        logs_folder,
        f"af_to_obaf_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
    )

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

logger, log_file = _setup_logger()

# Convert all AF files with all configurations
af_folder = "data/AF"
total_attempts = 0
total_successes = 0
total_failures = 0
# Since no extension failures happen a lot, we track 
# them separately to provide more insights about them without filling 
# the logs with repeated error messages about no extensions found for the same file
total_no_extension_failures = 0
no_extension_by_file = Counter()
no_extension_by_semantics = Counter()
no_extension_by_file_semantics = Counter()
first_seen_no_extension_context = set()

logger.info("Starting AF to OBAF conversion.")
for af_subfolder in ["BA", "WS"]:
    subfolder_path = os.path.join(af_folder, af_subfolder)
    if not os.path.isdir(subfolder_path):
        logger.warning("Skipping missing subfolder: %s", subfolder_path)
        continue

    logger.info("Processing subfolder: %s", subfolder_path)
    for file_name in os.listdir(subfolder_path):
        if not file_name.endswith(".apx"):
            continue

        file_path = os.path.join(subfolder_path, file_name)
        logger.info("Converting %s with all configurations...", file_path)

        file_attempts = 0
        file_successes = 0
        file_failures = 0
        file_no_extension_failures = 0

        for semantics in ["PR", "CO"]:
            for reliability in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
                for number_of_agents in [5, 10, 15, 20, 25, 30]:
                    for distribution_type in ["uniform", "average"]:
                        total_attempts += 1
                        file_attempts += 1
                        try:
                            af_to_obaf(
                                file_path,
                                semantics,
                                reliability,
                                number_of_agents,
                                distribution_type,
                            )
                            total_successes += 1
                            file_successes += 1
                        except Exception as exc:
                            total_failures += 1
                            file_failures += 1
                            error_message = str(exc)
                            is_no_extension_error = (
                                isinstance(exc, ValueError)
                                and error_message.startswith(NO_EXTENSION_ERROR_PREFIX)
                            )

                            if is_no_extension_error:
                                total_no_extension_failures += 1
                                file_no_extension_failures += 1
                                no_extension_by_file[file_path] += 1
                                no_extension_by_semantics[semantics] += 1
                                no_extension_by_file_semantics[(file_path, semantics)] += 1

                                context_key = (file_path, semantics)
                                if context_key not in first_seen_no_extension_context:
                                    first_seen_no_extension_context.add(context_key)
                                    logger.warning(
                                        "No truth extension for file=%s semantics=%s. Repeated occurrences for this file/semantics are counted and summarized.",
                                        file_path,
                                        semantics,
                                    )
                            else:
                                logger.exception(
                                    "Failed conversion for file=%s semantics=%s reliability=%.1f agents=%d distribution=%s",
                                    file_path,
                                    semantics,
                                    reliability,
                                    number_of_agents,
                                    distribution_type,
                                )

        logger.info(
            "Finished %s: attempts=%d successes=%d failures=%d no_extension_failures=%d",
            file_path,
            file_attempts,
            file_successes,
            file_failures,
            file_no_extension_failures,
        )

logger.info(
    "Done converting all AF files. attempts=%d successes=%d failures=%d",
    total_attempts,
    total_successes,
    total_failures,
)
logger.info("No-extension failures total=%d", total_no_extension_failures)

if total_no_extension_failures:
    for semantics_key in sorted(no_extension_by_semantics):
        logger.info(
            "No-extension failures by semantics: %s=%d",
            semantics_key,
            no_extension_by_semantics[semantics_key],
        )

    for file_path_key in sorted(no_extension_by_file):
        logger.info(
            "No-extension failures by file: %s=%d",
            file_path_key,
            no_extension_by_file[file_path_key],
        )

    for file_semantics_key in sorted(no_extension_by_file_semantics):
        current_file_path, current_semantics = file_semantics_key
        logger.info(
            "No-extension failures by file+semantics: file=%s semantics=%s count=%d",
            current_file_path,
            current_semantics,
            no_extension_by_file_semantics[file_semantics_key],
        )

logger.info("All results are available in data/OBAF.")
logger.info("Detailed execution log: %s", log_file)

print(f"Done. Logs written to: {log_file}")
