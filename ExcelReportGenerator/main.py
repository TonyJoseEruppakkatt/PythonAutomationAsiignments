
import pandas as pd
from pathlib import Path


# ==========================================
# 1. FOLDER PATHS
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_FOLDER = BASE_DIR / "ExcelFiles"
OUTPUT_FOLDER = BASE_DIR / "output"

OUTPUT_FILE = OUTPUT_FOLDER / "consolidated_sales_report.xlsx"


# Required columns
REQUIRED_COLUMNS = [
    "Date",
    "Product",
    "Category",
    "Quantity",
    "Unit Price"
]


# ==========================================
# 2. READ EXCEL FILES
# ==========================================

def read_excel_files():

    all_data = []

    excel_files = list(INPUT_FOLDER.glob("*.xlsx"))

    if not excel_files:
        print("No Excel files found!")
        return pd.DataFrame()

    for file in excel_files:

        try:
            print(f"Reading: {file.name}")

            df = pd.read_excel(file)

            df.columns = df.columns.astype(str).str.strip()

            missing_columns = [
                col for col in REQUIRED_COLUMNS
                if col not in df.columns
            ]

            if missing_columns:
                print(
                    f"Skipping {file.name}. "
                    f"Missing columns: {missing_columns}"
                )
                continue

            df = df[REQUIRED_COLUMNS].copy()

            df["Source File"] = file.name

            all_data.append(df)

        except Exception as e:
            print(f"Error reading {file.name}: {e}")

    if not all_data:
        return pd.DataFrame()

    return pd.concat(all_data, ignore_index=True)


# ==========================================
# 3. CLEAN AND VALIDATE DATA
# ==========================================

def clean_data(df):

    if df.empty:
        return df

    for column in ["Product", "Category"]:
        df[column] = df[column].astype("string").str.strip()

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce",
        dayfirst=True
    )

    df["Quantity"] = pd.to_numeric(
        df["Quantity"],
        errors="coerce"
    )

    df["Unit Price"] = pd.to_numeric(
        df["Unit Price"],
        errors="coerce"
    )

    df = df.dropna(
        subset=REQUIRED_COLUMNS
    ).copy()

    df = df[
        (df["Product"] != "") &
        (df["Category"] != "")
    ].copy()

    df = df[
        (df["Quantity"] > 0) &
        (df["Unit Price"] >= 0)
    ].copy()

    df["Total Sales"] = (
        df["Quantity"] * df["Unit Price"]
    )

    return df


# ==========================================
# 4. FILTER DATA BY DATE RANGE
# ==========================================

def filter_by_date_range(df):

    print("\n===== DATE FILTERING =====")

    while True:

        try:

            start_date = pd.to_datetime(
                input("Enter start date (DD-MM-YYYY): "),
                format="%d-%m-%Y"
            )

            end_date = pd.to_datetime(
                input("Enter end date (DD-MM-YYYY): "),
                format="%d-%m-%Y"
            )

            if start_date > end_date:
                print("Start date cannot be after end date!")
                continue

            break

        except ValueError:
            print("Invalid date! Please enter DD-MM-YYYY.")

    filtered_df = df[
        (df["Date"] >= start_date) &
        (df["Date"] <= end_date)
    ].copy()

    print("\nDate filtering completed!")

    print(
        f"Start Date: {start_date.strftime('%d-%m-%Y')}"
    )

    print(
        f"End Date: {end_date.strftime('%d-%m-%Y')}"
    )

    print(f"Transactions found: {len(filtered_df)}")

    return filtered_df


# ==========================================
# 5. PRODUCT SUMMARY
# ==========================================

def product_summary(df):

    summary = df.groupby("Product").agg(
        Total_Quantity=("Quantity", "sum"),
        Total_Revenue=("Total Sales", "sum"),
        Total_Transactions=("Product", "count")
    ).reset_index()

    summary = summary.sort_values(
        by="Total_Quantity",
        ascending=False
    )

    return summary


# ==========================================
# 6. CATEGORY SUMMARY
# ==========================================

def category_summary(df):

    summary = df.groupby("Category").agg(
        Total_Quantity=("Quantity", "sum"),
        Total_Revenue=("Total Sales", "sum"),
        Total_Transactions=("Category", "count")
    ).reset_index()

    summary = summary.sort_values(
        by="Total_Revenue",
        ascending=False
    )

    return summary


# ==========================================
# 7. OVERALL SUMMARY
# ==========================================

def overall_summary(df):

    total_revenue = df["Total Sales"].sum()

    total_quantity = df["Quantity"].sum()

    total_transactions = len(df)

    unique_products = df["Product"].nunique()

    unique_categories = df["Category"].nunique()

    best_selling = (
        df.groupby("Product")["Quantity"]
        .sum()
        .idxmax()
    )

    summary = pd.DataFrame({

        "Metric": [
            "Total Revenue",
            "Total Quantity Sold",
            "Total Transactions",
            "Unique Products",
            "Unique Categories",
            "Best-Selling Product"
        ],

        "Value": [
            total_revenue,
            total_quantity,
            total_transactions,
            unique_products,
            unique_categories,
            best_selling
        ]
    })

    return summary


# ==========================================
# 8. GENERATE EXCEL REPORT
# ==========================================

def generate_report(df):

    OUTPUT_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    products = product_summary(df)

    categories = category_summary(df)

    overall = overall_summary(df)

    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            sheet_name="All Transactions",
            index=False
        )

        products.to_excel(
            writer,
            sheet_name="Product Summary",
            index=False
        )

        categories.to_excel(
            writer,
            sheet_name="Category Summary",
            index=False
        )

        overall.to_excel(
            writer,
            sheet_name="Overall Summary",
            index=False
        )

        # Format worksheets
        for worksheet in writer.sheets.values():

            worksheet.freeze_panes = "A2"

            worksheet.auto_filter.ref = worksheet.dimensions

            for column_cells in worksheet.columns:

                max_length = max(
                    len(str(cell.value or ""))
                    for cell in column_cells
                )

                column_letter = (
                    column_cells[0].column_letter
                )

                worksheet.column_dimensions[
                    column_letter
                ].width = min(max_length + 3, 35)

    print("\nReport generated successfully!")

    print(f"Location: {OUTPUT_FILE}")


# ==========================================
# 9. MAIN PROGRAM
# ==========================================

def main():

    print("===== EXCEL REPORT GENERATOR =====")

    # Read Excel files
    df = read_excel_files()

    if df.empty:
        print("No valid sales records found.")
        return

    # Clean data
    print("\nCleaning data...")

    original_count = len(df)

    df = clean_data(df)

    removed_count = original_count - len(df)

    print(f"Valid records: {len(df)}")

    print(f"Invalid records removed: {removed_count}")

    if df.empty:
        print("No valid records available for reporting.")
        return

    # Filter by date range
    df = filter_by_date_range(df)

    if df.empty:
        print("No transactions found within the selected date range.")
        return

    # Generate report
    print("\nGenerating report...")

    generate_report(df)


# ==========================================
# 10. PROGRAM EXECUTION
# ==========================================

if __name__ == "__main__":
    main()
