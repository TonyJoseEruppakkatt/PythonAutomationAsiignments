import pandas as pd
from pathlib import Path


def generate_reports(valid_records, invalid_records):

    output_folder = Path("output")

    output_folder.mkdir(exist_ok=True)

    # Generate valid records
    valid_df = pd.DataFrame(valid_records)

    valid_df.to_csv(
        output_folder / "valid_records.csv",
        index=False
    )

    # Generate invalid records
    invalid_df = pd.DataFrame(invalid_records)

    invalid_df.to_csv(
        output_folder / "invalid_records.csv",
        index=False
    )

    print("\nReports generated successfully!")


def generate_summary(total, valid, invalid):

    print("\n========== VALIDATION SUMMARY ==========")

    print(f"Total records processed : {total}")

    print(f"Valid records            : {valid}")

    print(f"Invalid records          : {invalid}")

    print(f"Validation failure rate  : {(invalid / total * 100):.2f}%" if total else "Validation failure rate: 0.00%")

    print("========================================")