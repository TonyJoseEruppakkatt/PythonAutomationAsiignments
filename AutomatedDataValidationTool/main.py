
import pandas as pd
import json

from pathlib import Path

from validator import validate_records

from report_generator import (
    generate_reports,
    generate_summary
)


# Load CSV or Excel file
def load_data(file_path):

    extension = file_path.suffix.lower()

    if extension == ".csv":

        return pd.read_csv(file_path)

    elif extension in [".xlsx", ".xls"]:

        return pd.read_excel(file_path)

    else:

        raise ValueError("Unsupported file format!")


# Display available configurations
def select_configuration():

    config_folder = Path("configurations")

    config_folder.mkdir(exist_ok=True)

    config_files = list(config_folder.glob("*.json"))

    if not config_files:

        raise FileNotFoundError(
            "No validation configurations found!"
        )

    print("\nAvailable Validation Configurations:")

    for index, file in enumerate(config_files, start=1):

        print(f"{index}. {file.name}")

    try:

        choice = int(input("\nSelect configuration number: "))

        if choice < 1 or choice > len(config_files):

            raise ValueError("Invalid selection!")

        return config_files[choice - 1]

    except ValueError:

        raise ValueError("Please enter a valid configuration number!")


# Load selected JSON configuration
def load_rules(config_path):

    with open(config_path, "r") as file:

        return json.load(file)


# Main program
def main():

    try:

        print("===================================")

        print(" AUTOMATED DATA VALIDATION TOOL")

        print("===================================")

        # Select configuration
        config_path = select_configuration()

        print("\nSelected configuration:", config_path.name)

        # Get input file
        file_name = input("\nEnter CSV or Excel file path: ")

        file_path = Path(file_name)

        if not file_path.exists():

            print("Input file does not exist!")

            return

        # Load data
        df = load_data(file_path)

        # Load validation rules
        rules = load_rules(config_path)

        # Validate records
        valid_records, invalid_records = validate_records(
            df,
            rules
        )

        # Generate reports
        generate_reports(
            valid_records,
            invalid_records
        )

        # Display summary
        generate_summary(
            len(df),
            len(valid_records),
            len(invalid_records)
        )

    except FileNotFoundError as error:

        print("File not found:", error)

    except json.JSONDecodeError:

        print("Invalid JSON configuration file!")

    except pd.errors.EmptyDataError:

        print("Input CSV file is empty!")

    except Exception as error:

        print("Error:", error)


if __name__ == "__main__":

    main()
