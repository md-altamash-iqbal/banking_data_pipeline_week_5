import pandas as pd

from config import (
    REQUIRED_COLUMNS,
    ALLOWED_TRANSACTION_TYPES,
    ALLOWED_CURRENCY,
)


# Check whether required columns exist
def validate_columns(df):
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    return missing_columns


def validate_transactions(df):

    df = df.copy()

    errors = []

    for index, row in df.iterrows():

        row_errors = []

        # 1. Validate transaction_id
        if (
            pd.isna(row["transaction_id"])
            or str(row["transaction_id"]).strip() == ""
        ):
            row_errors.append(
                "transaction_id is missing"
            )

        # 2. Validate account_id
        if (
            pd.isna(row["account_id"])
            or str(row["account_id"]).strip() == ""
        ):
            row_errors.append(
                "account_id is missing"
            )

        # 3. Validate transaction_date
        try:
            date = pd.to_datetime(
                row["transaction_date"],
                format="%Y-%m-%d",
                errors="raise"
            )

            if date.strftime("%Y-%m-%d") != str(
                row["transaction_date"]
            ):
                row_errors.append(
                    "transaction_date must be in YYYY-MM-DD format"
                )

        except (ValueError, TypeError):
            row_errors.append(
                "transaction_date is invalid"
            )

        # 4. Validate transaction_type
        if (
            row["transaction_type"]
            not in ALLOWED_TRANSACTION_TYPES
        ):
            row_errors.append(
                "transaction_type must be CREDIT or DEBIT"
            )

        # 5. Validate amount
        try:
            amount = float(row["amount"])

            if pd.isna(amount):
                row_errors.append(
                    "amount must be numeric"
                )
            elif amount <= 0:
                row_errors.append(
                    "amount must be greater than 0"
                )

        except (ValueError, TypeError):
            row_errors.append(
                "amount must be numeric"
            )

        # 6. Validate currency
        if row["currency"] != ALLOWED_CURRENCY:
            row_errors.append(
                "currency must be USD"
            )

        # Store ALL errors for this row
        errors.append(
            "; ".join(row_errors)
        )

    # Add error_reason column
    df["error_reason"] = errors

    # Find duplicate transaction IDs
    duplicate_mask = df["transaction_id"].duplicated(
        keep=False
    )

    # Add duplicate error without removing existing errors
    df.loc[
        duplicate_mask,
        "error_reason"
    ] = (
        df.loc[
            duplicate_mask,
            "error_reason"
        ].apply(
            lambda error:
                (
                    error + "; transaction_id is duplicated"
                    if error
                    else "transaction_id is duplicated"
                )
        )
    )

    return df