
from pathlib import Path
from datetime import datetime
import shutil
import zipfile
import json
import logging
import hashlib


# --------------------------------
# 1. Logging Configuration
# --------------------------------

# Create logs folder automatically
LOG_FOLDER = Path("logs")
LOG_FOLDER.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    filename=LOG_FOLDER / "backup.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# --------------------------------
# 2. Load JSON Configuration
# --------------------------------

def load_config():

    try:

        with open("config.json", "r") as file:
            config = json.load(file)

        return config

    except Exception as e:

        logging.error(f"Configuration error: {e}")
        print("Unable to load configuration!")

        return None


# --------------------------------
# 3. Validate Source Folder
# --------------------------------

def validate_source(source_folder):

    if not source_folder.exists():

        print("Source folder does not exist!")

        logging.error("Source folder not found")

        return False

    if not source_folder.is_dir():

        print("Source path is not a folder!")

        return False

    return True


# --------------------------------
# 4. Create ZIP Backup
# --------------------------------

def create_backup(source_folder, backup_folder):

    try:

        backup_folder.mkdir(parents=True, exist_ok=True)

        current_time = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        backup_name = f"backup_{current_time}.zip"

        backup_path = backup_folder / backup_name

        with zipfile.ZipFile(
            backup_path,
            "w",
            zipfile.ZIP_DEFLATED
        ) as zip_file:

            for file in source_folder.rglob("*"):

                if file.is_file():

                    relative_path = file.relative_to(source_folder)

                    zip_file.write(file, relative_path)

        print(f"Backup created successfully: {backup_name}")

        logging.info(f"Backup created: {backup_name}")

        return backup_path

    except OSError as e:

        print(f"Backup failed: {e}")

        logging.error(f"Backup failed: {e}")

        return None

    except Exception as e:

        print(f"Unexpected error: {e}")

        logging.exception("Unexpected backup error")

        return None


# --------------------------------
# 5. Manage Backup Versions
# --------------------------------

def manage_backups(backup_folder, max_backups):

    try:

        backup_files = sorted(
            backup_folder.glob("backup_*.zip"),
            key=lambda file: file.stat().st_mtime,
            reverse=True
        )

        old_backups = backup_files[max_backups:]

        for backup in old_backups:

            backup.unlink()

            print(f"Old backup removed: {backup.name}")

            logging.info(f"Old backup removed: {backup.name}")

    except Exception as e:

        print(f"Backup management error: {e}")

        logging.exception("Backup management failed")



# --------------------------------
# 1. Calculate File Hash
# --------------------------------

def calculate_hash(file_path):

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:

        for chunk in iter(lambda: file.read(4096), b""):

            sha256.update(chunk)

    return sha256.hexdigest()


# --------------------------------
# 2. Load Previous File Hashes
# --------------------------------

def load_previous_hashes():

    hash_file = Path(__file__).parent / "file_hashes.json"

    if hash_file.exists():

        try:

            with open(hash_file, "r") as file:

                return json.load(file)

        except (json.JSONDecodeError, OSError) as e:

            logging.error(f"Unable to load file hashes: {e}")

    return {}


# --------------------------------
# 3. Save Current File Hashes
# --------------------------------

def save_hashes(current_hashes):

    hash_file = Path(__file__).parent / "file_hashes.json"

    with open(hash_file, "w") as file:

        json.dump(current_hashes, file, indent=4)


# --------------------------------
# 4. Create Incremental Backup
# --------------------------------

def create_incremental_backup(source_folder, backup_folder):

    try:

        backup_folder.mkdir(parents=True, exist_ok=True)

        previous_hashes = load_previous_hashes()

        current_hashes = {}

        changed_files = []

        for file in source_folder.rglob("*"):

            if file.is_file():

                relative_path = str(
                    file.relative_to(source_folder)
                )

                file_hash = calculate_hash(file)

                current_hashes[relative_path] = file_hash

                if previous_hashes.get(relative_path) != file_hash:

                    changed_files.append(file)

        current_time = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        backup_name = f"backup_{current_time}.zip"

        backup_path = backup_folder / backup_name

        if changed_files:

            with zipfile.ZipFile(
                backup_path,
                "w",
                zipfile.ZIP_DEFLATED
            ) as zip_file:

                for file in changed_files:

                    relative_path = file.relative_to(source_folder)

                    zip_file.write(file, relative_path)

                    print(f"Added: {relative_path}")

        else:

            print("No files have changed. Backup not required.")

            logging.info("No changes detected")

            return None

        save_hashes(current_hashes)

        print(f"\nIncremental backup created: {backup_name}")

        print(f"Files included: {len(changed_files)}")

        logging.info(
            f"Incremental backup created: {backup_name}"
        )

        return backup_path

    except OSError as e:

        print(f"Backup failed: {e}")

        logging.exception("Incremental backup failed")

        return None

    except Exception as e:

        print(f"Unexpected error: {e}")

        logging.exception("Unexpected incremental backup error")

        return None

# --------------------------------
# 6. Main Function
# --------------------------------

def main():

    config = load_config()

    if config is None:
        return

    source_folder = Path(config["source_folder"])

    backup_folder = Path(config["backup_folder"])

    max_backups = config["max_backups"]

    if not isinstance(max_backups, int) or isinstance(max_backups, bool) or max_backups < 1:

        print("Maximum backups must be a positive integer!")

        return

    if not validate_source(source_folder):
        return

    backup_path = create_incremental_backup(
        source_folder,
        backup_folder
    )

    if backup_path is not None:

        manage_backups(
            backup_folder,
            max_backups
        )

        print("\nBackup process completed!")

    else:

        print("\nNo new backup created.")


# --------------------------------
# 7. Program Execution
# --------------------------------

if __name__ == "__main__":

    main()
