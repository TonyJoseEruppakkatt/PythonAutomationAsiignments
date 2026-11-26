
import os
import hashlib
import csv


# Step 1: Calculate file size
def get_file_size(file_path):
    return os.path.getsize(file_path)


# Step 2: Generate file hash
def calculate_file_hash(file_path):

    sha256 = hashlib.sha256()

    try:
        with open(file_path, "rb") as file:

            while True:
                chunk = file.read(4096)

                if not chunk:
                    break

                sha256.update(chunk)

        return sha256.hexdigest()

    except (PermissionError, OSError) as e:
        print(f"Unable to read: {file_path} - {e}")
        return None


# Step 3: Scan all files inside the folder
def scan_folder(folder_path):

    file_groups = {}

    for root, directories, files in os.walk(folder_path):

        for filename in files:

            file_path = os.path.join(root, filename)

            try:
                file_size = get_file_size(file_path)

                # Ignore empty files for this assignment
                if file_size == 0:
                    continue

                file_hash = calculate_file_hash(file_path)

                if file_hash is None:
                    continue

                # Group files using their hash
                key = (file_size, file_hash)

                if key not in file_groups:
                    file_groups[key] = []

                file_groups[key].append(file_path)

            except OSError as e:
                print(f"Skipping file: {file_path} - {e}")

    return file_groups


# Step 4: Identify duplicate files
def find_duplicates(file_groups):

    duplicates = []

    for key, file_paths in file_groups.items():

        if len(file_paths) > 1:

            file_size, file_hash = key

            duplicates.append({
                "files": file_paths,
                "file_size": file_size,
                "duplicate_count": len(file_paths) - 1,
                "space_savings": file_size * (len(file_paths) - 1)
            })

    return duplicates


# Step 5: Display duplicate files
def display_duplicates(duplicates):

    if not duplicates:
        print("\nNo duplicate files found.")
        return

    total_savings = 0

    print("\n========== DUPLICATE FILE REPORT ==========")

    for index, group in enumerate(duplicates, start=1):

        print(f"\nDuplicate Group {index}:")

        for path in group["files"]:
            print(f"File: {path}")

        file_size = group["file_size"]

        print(f"File Size: {file_size / (1024 * 1024):.2f} MB")

        print(f"Duplicate Copies: {group['duplicate_count']}")

        savings = group["space_savings"]

        print(f"Potential Space Savings: {savings / (1024 * 1024):.2f} MB")

        total_savings += savings

    print("\n-------------------------------------------")

    print(
        f"Total Potential Space Savings: "
        f"{total_savings / (1024 * 1024):.2f} MB"
    )


# Step 6: Export report to CSV
def export_csv(duplicates):

    filename = "duplicate_report.csv"

    try:
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:

            writer = csv.writer(csvfile)

            writer.writerow([
                "Group",
                "File Path",
                "File Size (Bytes)",
                "Duplicate Copies",
                "Potential Space Savings (Bytes)"
            ])

            for index, group in enumerate(duplicates, start=1):

                for path in group["files"]:

                    writer.writerow([
                        index,
                        path,
                        group["file_size"],
                        group["duplicate_count"],
                        group["space_savings"]
                    ])

        print(f"\nCSV report generated successfully: {filename}")

    except OSError as e:
        print(f"Unable to create CSV report: {e}")


# Step 8: Allow users to select duplicate files for deletion
def delete_selected_duplicates(duplicates):

    if not duplicates:
        print("No duplicate files available for deletion.")
        return

    selected_files = []

    print("\n========== SELECT DUPLICATE FILES ==========")

    for index, group in enumerate(duplicates, start=1):

        print(f"\nDuplicate Group {index}")

        for file_index, path in enumerate(group["files"], start=1):

            print(f"{file_index}. {path}")

        print("\nSelect the files you want to delete.")
        print("Do not select the file you want to keep.")

        choices = input(
            "Enter file numbers separated by commas (or press Enter to skip): "
        ).strip()

        if not choices:
            continue

        try:
            numbers = set()

            for value in choices.split(","):
                numbers.add(int(value.strip()))

            # Validate selections
            if any(number < 1 or number > len(group["files"])
                   for number in numbers):
                print("Invalid selection. Skipping this group.")
                continue

            # Keep at least one copy
            if len(numbers) >= len(group["files"]):
                print("You must keep at least one copy. Skipping this group.")
                continue

            for number in sorted(numbers):
                selected_files.append(group["files"][number - 1])

        except ValueError:
            print("Invalid input. Skipping this group.")

    if not selected_files:
        print("\nNo files selected for deletion.")
        return

    # Display selected files before deletion
    print("\n========== FILES SELECTED FOR DELETION ==========")

    for path in selected_files:
        print(path)

    confirmation = input(
        "\nAre you sure you want to delete these files? (yes/no): "
    ).strip().lower()

    if confirmation != "yes":
        print("Deletion cancelled.")
        return

    deleted_count = 0

    for path in selected_files:

        try:
            if os.path.isfile(path):
                os.remove(path)
                print(f"Deleted: {path}")
                deleted_count += 1

            else:
                print(f"File not found: {path}")

        except OSError as e:
            print(f"Unable to delete {path}: {e}")

    print(f"\nTotal files deleted: {deleted_count}")


# Step 7: Main program

def main():

    print("========== DUPLICATE FILE FINDER ==========")

    folder_path = input("\nEnter folder path to scan: ").strip().strip('"')

    if not os.path.isdir(folder_path):

        print("Invalid folder path!")
        return

    print("\nScanning files... Please wait.")

    file_groups = scan_folder(folder_path)

    duplicates = find_duplicates(file_groups)

    display_duplicates(duplicates)

    if duplicates:

        choice = input(
            "\nDo you want to export the report? (yes/no): "
        ).strip().lower()

        if choice == "yes":
            export_csv(duplicates)

        delete_choice = input(
            "\nDo you want to select duplicate files for deletion? (yes/no): "
        ).strip().lower()

        if delete_choice == "yes":
            delete_selected_duplicates(duplicates)

    print("\nDuplicate scanning completed!")


if __name__ == "__main__":
    main()
