
from pathlib import Path
import re
from datetime import datetime


# 1. Get folder path
def get_folder():

    folder_path = input("Enter folder path: ")

    folder = Path(folder_path)

    if not folder.exists():
        print("Folder does not exist!")
        return None

    if not folder.is_dir():
        print("The given path is not a folder!")
        return None

    return folder


# 2. Get file extensions
def get_file_types():

    extensions = input(
        "Enter file types (example: jpg,png): "
    )

    extensions = extensions.split(",")

    extensions = [
        "." + ext.strip().lower().lstrip(".")
        for ext in extensions
        if ext.strip()
    ]

    return extensions


# 3. Get file creation or modification date
def get_file_date(file, date_option):

    file_info = file.stat()

    if date_option == "creation":
        timestamp = file_info.st_ctime

    else:
        timestamp = file_info.st_mtime

    file_date = datetime.fromtimestamp(timestamp)

    return file_date.strftime("%Y-%m-%d")


# 4. Main renaming function
def rename_files():

    folder = get_folder()

    if folder is None:
        return

    # Get filename prefix
    prefix = input("Enter filename prefix: ").strip()

    prefix = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "_",
        prefix
    ).strip("_-")

    if not prefix:
        print("Invalid filename prefix!")
        return

    # Get starting number
    try:
        start_number = int(
            input("Enter starting number: ")
        )

        if start_number < 0:
            print("Starting number cannot be negative!")
            return

    except ValueError:
        print("Enter a valid number!")
        return

    # Get extensions
    extensions = get_file_types()

    if not extensions:
        print("Please enter at least one file type!")
        return

    # Select renaming method
    print("\nChoose renaming method:")
    print("1. Sequential numbering")
    print("2. Creation date")
    print("3. Modification date")

    method = input("Enter your choice: ").strip()

    if method not in ["1", "2", "3"]:
        print("Invalid choice!")
        return

    # Get matching files
    files = [
        file for file in folder.iterdir()
        if file.is_file()
        and file.suffix.lower() in extensions
    ]

    # Sort files
    files.sort(key=lambda file: file.name.lower())

    if not files:
        print("No matching files found!")
        return

    # Generate rename plan
    rename_plan = []

    number = start_number

    try:

        for file in files:

            if method == "1":

                new_name = (
                    f"{prefix}_{number:03d}{file.suffix}"
                )

            elif method == "2":

                file_date = get_file_date(
                    file, "creation"
                )

                new_name = (
                    f"{file_date}_{prefix}_"
                    f"{number:03d}{file.suffix}"
                )

            else:

                file_date = get_file_date(
                    file, "modification"
                )

                new_name = (
                    f"{file_date}_{prefix}_"
                    f"{number:03d}{file.suffix}"
                )

            new_path = folder / new_name

            rename_plan.append((file, new_path))

            number += 1

    except OSError as error:
        print("Unable to read file information:", error)
        return

    # Validate duplicate target names
    targets = [new_path for _, new_path in rename_plan]

    if len(set(targets)) != len(targets):
        print("Duplicate target filenames detected!")
        return

    # Prevent overwriting existing files
    original_files = {old_path for old_path, _ in rename_plan}

    for old_file, new_file in rename_plan:

        if new_file.exists() and new_file not in original_files:
            print(
                "Cannot rename. File already exists:",
                new_file.name
            )
            return

    # Preview
    print("\n========== RENAME PREVIEW ==========")

    for old_file, new_file in rename_plan:

        print(
            f"{old_file.name}  -->  {new_file.name}"
        )

    # Confirm
    choice = input(
        "\nApply these changes? (yes/no): "
    ).strip().lower()

    if choice != "yes":

        print("Renaming cancelled!")
        return

    # Rename using temporary names to avoid
    # conflicts between original and target filenames
    completed = []
    temporary_files = []

    try:

        # First phase: move original files to temporary names
        for index, (old_file, new_file) in enumerate(rename_plan):

            temp_file = folder / f".renametemp_{index}"

            if temp_file.exists():
                raise FileExistsError(
                    f"Temporary filename already exists: {temp_file.name}"
                )

            old_file.rename(temp_file)

            temporary_files.append(
                (temp_file, old_file, new_file)
            )

        # Second phase: rename temporary files
        for temp_file, old_file, new_file in temporary_files:

            if new_file.exists():
                raise FileExistsError(
                    f"Target already exists: {new_file.name}"
                )

            temp_file.rename(new_file)

            completed.append((new_file, old_file))

        print("\nAll files renamed successfully!")

    except OSError as error:

        print("\nRenaming failed:", error)

        # Attempt to restore original filenames
        for current_file, old_file in reversed(completed):

            try:
                if current_file.exists() and not old_file.exists():
                    current_file.rename(old_file)
            except OSError:
                print("Could not restore:", old_file.name)

        for temp_file, old_file, new_file in reversed(temporary_files):

            try:
                if temp_file.exists() and not old_file.exists():
                    temp_file.rename(old_file)
            except OSError:
                print("Could not restore:", old_file.name)

        print("Please check the folder for any files that need recovery.")


# 5. Execute program
if __name__ == "__main__":

    rename_files()
