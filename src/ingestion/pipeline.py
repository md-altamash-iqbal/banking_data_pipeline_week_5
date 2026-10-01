from pathlib import Path
import logging

import pandas as pd

from config import REQUIRED_COLUMNS
from validation import validate_columns, validate_transactions
from dq_metrics import create_dq_summary


# --------------------------------
# DIRECTORIES
# --------------------------------

INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")
LOG_DIR = Path("logs")


# Create required directories
OUTPUT_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)


# --------------------------------
# LOGGING
# --------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename=LOG_DIR / "pipeline.log",
)

logger = logging.getLogger(__name__)


# --------------------------------
# EXTRACT
# --------------------------------

def load_files(input_dir):
    """
    Find CSV files, safely read them,
    validate their schema, and preserve
    source file information.
    """

    files = sorted(input_dir.glob("*.csv"))

    print("Input directory:", input_dir.resolve())
    print("Files found:", files)

    dataframes = []

    files_discovered = len(files)
    files_read = 0
    files_skipped = 0

    if files_discovered == 0:
        logger.warning(
            "No CSV files found in input directory: %s",
            input_dir
        )

    for file in files:

        logger.info(
            "Reading file: %s",
            file.name
        )

        try:
            df = pd.read_csv(file)

        except (
            pd.errors.EmptyDataError,
            pd.errors.ParserError,
            UnicodeDecodeError,
            OSError,
        ) as exc:

            logger.error(
                "Could not read file %s: %s. Skipping this file.",
                file.name,
                exc
            )

            files_skipped += 1
            continue

        # Check required columns
        missing_columns = validate_columns(df)

        if missing_columns:

            logger.warning(
                "File %s is missing required columns: %s. "
                "Skipping this file.",
                file.name,
                missing_columns
            )

            files_skipped += 1
            continue

        # Empty file
        if df.empty:

            logger.warning(
                "File %s contains no transactions.",
                file.name
            )

        # Preserve source file
        df["source_file"] = file.name

        dataframes.append(df)

        files_read += 1

        logger.info(
            "Successfully read file: %s",
            file.name
        )

    return (
        dataframes,
        files_discovered,
        files_read,
        files_skipped,
    )


# --------------------------------
# MAIN PIPELINE
# --------------------------------

def run_pipeline(input_dir, output_dir):

    logger.info("Pipeline started")

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    # --------------------------------
    # 1. EXTRACT
    # --------------------------------

    (
        dataframes,
        files_discovered,
        files_read,
        files_skipped,
    ) = load_files(input_dir)

    # --------------------------------
    # Combine data
    # --------------------------------

    if dataframes:

        daily_df = pd.concat(
            dataframes,
            ignore_index=True
        )

    else:

        logger.warning(
            "No valid input files to process."
        )

        daily_df = pd.DataFrame(
            columns=list(REQUIRED_COLUMNS)
            + ["source_file"]
        )

    print(
        "\nTotal records:",
        len(daily_df)
    )

    # --------------------------------
    # 2. TRANSFORM
    # --------------------------------

    daily_df = validate_transactions(
        daily_df
    )

    # --------------------------------
    # 3. SEPARATE VALID / INVALID
    # --------------------------------

    valid_df = daily_df[
        daily_df["error_reason"] == ""
    ].copy()

    invalid_df = daily_df[
        daily_df["error_reason"] != ""
    ].copy()

    print(
        "\nValid records:",
        len(valid_df)
    )

    print(
        "Invalid records:",
        len(invalid_df)
    )

    # --------------------------------
    # 4. LOAD
    # --------------------------------

    valid_df.to_csv(
        output_dir / "valid_transactions.csv",
        index=False
    )

    invalid_df.to_csv(
        output_dir / "invalid_transactions.csv",
        index=False
    )

    # --------------------------------
    # 5. BASIC SUMMARY
    # --------------------------------

    summary_df = pd.DataFrame(
        {
            "metric": [
                "total_input_records",
                "valid_records",
                "invalid_records",
            ],

            "count": [
                len(daily_df),
                len(valid_df),
                len(invalid_df),
            ],
        }
    )

    summary_df.to_csv(
        output_dir / "summary.csv",
        index=False
    )

    # --------------------------------
    # 6. DATA QUALITY SUMMARY
    # --------------------------------

    dq_summary = create_dq_summary(
        daily_df,
        files_discovered,
        files_read,
        files_skipped,
    )

    dq_summary.to_csv(
        output_dir / "dq_summary.csv",
        index=False
    )

    # --------------------------------
    # 7. PRINT RESULTS
    # --------------------------------

    print("\nSummary:")

    print(
        summary_df.to_string(
            index=False
        )
    )

    print(
        "\nOutput files created successfully."
    )

    logger.info(
        "Pipeline completed successfully. "
        "Total=%s, Valid=%s, Invalid=%s",
        len(daily_df),
        len(valid_df),
        len(invalid_df),
    )


# --------------------------------
# RUN PIPELINE
# --------------------------------

def main():

    run_pipeline(
        INPUT_DIR,
        OUTPUT_DIR
    )


if __name__ == "__main__":
    main()