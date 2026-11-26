
import pandas as pd
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def clean_data(file_path):

    # Step 1: Read CSV file
    df = pd.read_csv(file_path, dtype=str, keep_default_na=False)

    total_records = len(df)

    # Step 2: Display available columns
    available_columns = list(df.columns)

    print("\nAvailable Columns:")
    for column in available_columns:
        print("-", column)

    # Step 3: Ask user to select mandatory columns
    print("\nEnter mandatory columns separated by commas.")
    print("Example: Name,Email,City")

    user_input = input("Mandatory columns: ")

    mandatory_columns = [
        column.strip() for column in user_input.split(",")
        if column.strip()
    ]

    # Validate selected columns
    invalid_columns = [
        column for column in mandatory_columns
        if column not in available_columns
    ]

    if invalid_columns:
        raise ValueError(
            f"Columns not found: {', '.join(invalid_columns)}"
        )

    if not mandatory_columns:
        raise ValueError("Select at least one mandatory column.")

    # Step 4: Remove unnecessary spaces
    for column in df.select_dtypes(include="object").columns:
        df[column] = df[column].str.strip()

    # Step 5: Standardise city names if City exists
    if "City" in df.columns:
        df["City"] = df["City"].str.title()

    # Step 6: Detect duplicates
    duplicate_mask = df.duplicated(
        subset=available_columns,
        keep="first"
    )

    duplicate_count = duplicate_mask.sum()

    df = df.loc[~duplicate_mask].copy()

    # Step 7: Validate records
    def validate_record(row):

        errors = []

        # Check user-selected mandatory columns
        for column in mandatory_columns:
            if row[column] == "":
                errors.append(f"Missing {column}")

        # Validate email only if Email column exists
        if "Email" in df.columns and row["Email"] != "":

            email_pattern = (
                r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
            )

            if not re.match(email_pattern, row["Email"]):
                errors.append("Invalid Email")

        return ", ".join(errors)

    df["Reason"] = df.apply(validate_record, axis=1)

    # Step 8: Separate valid and invalid records
    invalid_df = df[df["Reason"] != ""].copy()

    valid_df = df[df["Reason"] == ""].copy()

    valid_df = valid_df[available_columns]

    # Step 9: Generate output files
    output_folder = Path(file_path).parent

    cleaned_file = output_folder / "cleaned_customers.csv"
    invalid_file = output_folder / "invalid_records.csv"

    valid_df.to_csv(cleaned_file, index=False)
    invalid_df.to_csv(invalid_file, index=False)

    # Step 10: Display summary
    print("\n========== CSV CLEANING SUMMARY ==========")

    print(f"Total records processed : {total_records}")
    print(f"Duplicates removed      : {duplicate_count}")
    print(f"Valid records           : {len(valid_df)}")
    print(f"Invalid records         : {len(invalid_df)}")

    print("\nMandatory Columns:", ", ".join(mandatory_columns))

    print("\nGenerated Files:")
    print("1. cleaned_customers.csv")
    print("2. invalid_records.csv")

    print("\nCSV cleaning completed successfully!")


# Main program
if __name__ == "__main__":

    print("===== CSV DATA CLEANER =====")

    file_name = input(
        "Enter CSV file path (press Enter for customers.csv): "
    ).strip()

    if file_name == "":
        file_path = BASE_DIR / "customers.csv"
    else:
        file_path = Path(file_name)

        if not file_path.is_absolute():
            file_path = BASE_DIR / file_path

    try:

        if not file_path.exists():
            print("Error: CSV file not found!")

        else:
            clean_data(file_path)

    except pd.errors.EmptyDataError:
        print("Error: CSV file is empty!")

    except pd.errors.ParserError:
        print("Error: Invalid CSV format!")

    except PermissionError:
        print("Error: Permission denied!")

    except ValueError as error:
        print("Error:", error)

    except Exception as error:
        print("Unexpected error:", error)
