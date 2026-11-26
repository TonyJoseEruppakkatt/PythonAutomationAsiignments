
import json
import logging
import shutil
import threading
import time

from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

try:
    from plyer import notification
except ImportError:
    notification = None


# --------------------------------------------------
# 1. LOAD CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).parent

with open(BASE_DIR / "config.json", "r") as file:
    config = json.load(file)

MONITOR_FOLDER = BASE_DIR / config["monitor_folder"]
PROCESSED_FOLDER = BASE_DIR / config["processed_folder"]
LOG_FOLDER = BASE_DIR / config["log_folder"]

LOG_FILE = LOG_FOLDER / config["log_file"]
STATE_FILE = BASE_DIR / config["state_file"]

CHECK_INTERVAL = config["check_interval"]
STABLE_CHECKS = config["stable_checks"]

CATEGORIES = config["categories"]
DEFAULT_CATEGORY = config["default_category"]

NOTIFICATIONS = config["notifications"]


# --------------------------------------------------
# 2. CREATE REQUIRED FOLDERS
# --------------------------------------------------

MONITOR_FOLDER.mkdir(parents=True, exist_ok=True)
PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)
LOG_FOLDER.mkdir(parents=True, exist_ok=True)

for category in CATEGORIES.values():

    destination = PROCESSED_FOLDER / category["destination"]

    destination.mkdir(parents=True, exist_ok=True)

DEFAULT_FOLDER = PROCESSED_FOLDER / DEFAULT_CATEGORY["destination"]
DEFAULT_FOLDER.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# 3. CONFIGURE LOGGING
# --------------------------------------------------

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# --------------------------------------------------
# 4. LOAD PROCESSED FILE HISTORY
# --------------------------------------------------

if STATE_FILE.exists():

    try:
        with open(STATE_FILE, "r") as file:
            processed_files = set(json.load(file))

    except (json.JSONDecodeError, OSError):
        processed_files = set()

else:
    processed_files = set()


state_lock = threading.Lock()
processing_files = set()


def save_processed_history():

    with state_lock:
        with open(STATE_FILE, "w") as file:
            json.dump(
                sorted(processed_files),
                file,
                indent=4
            )


# --------------------------------------------------
# 5. IDENTIFY FILE CATEGORY FROM JSON
# --------------------------------------------------

def identify_file_type(file_path):

    extension = file_path.suffix.lower()

    for category_name, details in CATEGORIES.items():

        extensions = [
            ext.lower() for ext in details["extensions"]
        ]

        if extension in extensions:

            return (
                category_name,
                details["destination"]
            )

    return (
        DEFAULT_CATEGORY["name"],
        DEFAULT_CATEGORY["destination"]
    )


# --------------------------------------------------
# 6. WAIT UNTIL FILE COPYING IS COMPLETED
# --------------------------------------------------

def wait_for_file_completion(file_path):

    stable_count = 0
    previous_size = -1

    while stable_count < STABLE_CHECKS:

        if not file_path.exists():
            return False

        try:

            current_size = file_path.stat().st_size

            if current_size == previous_size:
                stable_count += 1

            else:
                stable_count = 0

            previous_size = current_size

        except OSError:

            stable_count = 0

        time.sleep(CHECK_INTERVAL)

    return file_path.exists()


# --------------------------------------------------
# 7. GENERATE DESKTOP NOTIFICATION
# --------------------------------------------------

def send_notification(file_name, destination):

    if not NOTIFICATIONS["enabled"]:
        return

    message = (
        f"File: {file_name}\n"
        f"Destination: {destination}"
    )

    try:

        if notification is None:
            raise ImportError("Plyer is not installed")

        notification.notify(
            title=NOTIFICATIONS["title"],
            message=message,
            timeout=NOTIFICATIONS["timeout"]
        )

        print("\n[NOTIFICATION]")
        print(message)

    except Exception as error:

        logger.warning(
            "Desktop notification failed: %s",
            error
        )

        print("\n[NOTIFICATION - CONSOLE]")
        print(message)


# --------------------------------------------------
# 8. MOVE FILE TO DESTINATION
# --------------------------------------------------

def move_file(file_path):

    try:

        # Wait until file copying finishes
        if not wait_for_file_completion(file_path):
            return

        # Generate file fingerprint
        fingerprint = (
            f"{file_path.resolve()}|"
            f"{file_path.stat().st_size}|"
            f"{file_path.stat().st_mtime_ns}"
        )

        # Check duplicate processing
        with state_lock:

            if fingerprint in processed_files:

                logger.info(
                    "Duplicate file ignored: %s",
                    file_path.name
                )

                return

        # Identify category dynamically
        category, destination_name = identify_file_type(
            file_path
        )

        destination_folder = (
            PROCESSED_FOLDER / destination_name
        )

        destination_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        destination_path = (
            destination_folder / file_path.name
        )

        # Avoid overwriting existing files
        counter = 1

        while destination_path.exists():

            destination_path = destination_folder / (
                f"{file_path.stem}_{counter}"
                f"{file_path.suffix}"
            )

            counter += 1

        # Move file
        shutil.move(
            str(file_path),
            str(destination_path)
        )

        # Update processing history
        with state_lock:
            processed_files.add(fingerprint)

        save_processed_history()

        # Record activity
        logger.info(
            "Processed: %s | Category: %s | Destination: %s",
            file_path.name,
            category,
            destination_path
        )

        print(
            f"\n[PROCESSED] {file_path.name}"
        )

        print(
            f"[CATEGORY] {category}"
        )

        print(
            f"[DESTINATION] {destination_path}"
        )

        # Send success notification
        send_notification(
            file_path.name,
            destination_path
        )

    except Exception as error:

        logger.exception(
            "Error processing %s: %s",
            file_path.name,
            error
        )

        print(
            f"[ERROR] {file_path.name}: {error}"
        )

    finally:

        with state_lock:
            processing_files.discard(str(file_path))


# --------------------------------------------------
# 9. WATCHDOG EVENT HANDLER
# --------------------------------------------------

class FolderMonitorHandler(FileSystemEventHandler):

    def process_new_file(self, file_path):

        path = Path(file_path)

        if not path.is_file():
            return

        if path.name.startswith("~$"):
            return

        key = str(path)

        with state_lock:

            if key in processing_files:
                return

            processing_files.add(key)

        # Run file processing in background
        thread = threading.Thread(
            target=move_file,
            args=(path,),
            daemon=True
        )

        thread.start()

    def on_created(self, event):

        if not event.is_directory:
            self.process_new_file(event.src_path)

    def on_moved(self, event):

        if not event.is_directory:
            self.process_new_file(event.dest_path)


# --------------------------------------------------
# 10. START MONITORING
# --------------------------------------------------

def main():

    print("=" * 50)
    print(" AUTOMATED FOLDER MONITORING SYSTEM")
    print("=" * 50)

    print(f"Monitoring: {MONITOR_FOLDER}")
    print(f"Destination: {PROCESSED_FOLDER}")
    print("Notifications:", NOTIFICATIONS["enabled"])

    print("\nAvailable categories:")

    for name, details in CATEGORIES.items():
        print(
            f"{name} -> {details['destination']}"
        )

    print("\nStatus: Monitoring started")
    print("Press CTRL + C to stop.")
    print("=" * 50)

    logger.info("Folder monitoring started.")

    event_handler = FolderMonitorHandler()

    observer = Observer()

    observer.schedule(
        event_handler,
        str(MONITOR_FOLDER),
        recursive=True
    )

    observer.start()

    try:

        while True:
            time.sleep(1)

    except KeyboardInterrupt:

        print("\nStopping folder monitoring...")

        observer.stop()

    observer.join()

    logger.info("Folder monitoring stopped.")

    print("Monitoring stopped successfully.")


# --------------------------------------------------
# 11. PROGRAM ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    main()
