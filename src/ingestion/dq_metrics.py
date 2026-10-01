import pandas as pd


def count_error(df, text):
    """
    Count rows where error_reason contains the given text.
    """

    if "error_reason" not in df.columns:
        return 0

    if df.empty:
        return 0

    return df["error_reason"].fillna("").astype(str).str.contains(
        text,
        na=False
    ).sum()


def create_dq_summary(
    df,
    files_discovered,
    files_read,
    files_skipped
):
    """
    Create Data Quality metrics for the pipeline run.
    """

    total_records = len(df)

    valid_records = len(
        df[df["error_reason"] == ""]
    )

    invalid_records = len(
        df[df["error_reason"] != ""]
    )

    # Calculate rejection rate
    if total_records > 0:
        rejection_rate = (
            invalid_records / total_records
        ) * 100
    else:
        rejection_rate = 0

    dq_summary = pd.DataFrame(
        {
            "metric": [
                "files_discovered",
                "files_read",
                "files_skipped",
                "total_input_records",
                "valid_records",
                "invalid_records",
                "rejection_rate_percent",
                "duplicate_transaction_count",
                "missing_transaction_id",
                "missing_account_id",
                "invalid_transaction_date",
                "invalid_transaction_type",
                "invalid_amount",
                "invalid_currency",
            ],

            "count": [
                files_discovered,
                files_read,
                files_skipped,
                total_records,
                valid_records,
                invalid_records,
                round(rejection_rate, 2),

                count_error(
                    df,
                    "transaction_id is duplicated"
                ),

                count_error(
                    df,
                    "transaction_id is missing"
                ),

                count_error(
                    df,
                    "account_id is missing"
                ),

                count_error(
                    df,
                    "transaction_date is invalid"
                ),

                count_error(
                    df,
                    "transaction_type must be CREDIT or DEBIT"
                ),

                count_error(
                    df,
                    "amount"
                ),

                count_error(
                    df,
                    "currency must be USD"
                ),
            ],
        }
    )

    return dq_summary