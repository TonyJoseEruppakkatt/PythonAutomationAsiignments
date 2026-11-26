
from pathlib import Path
from PIL import Image
import csv

# Supported image extensions
SUPPORTED_FORMATS = [".jpg", ".jpeg", ".png", ".webp", ".bmp"]


# Get image files from input folder
def get_image_files(input_folder):

    image_files = []

    for file in input_folder.iterdir():

        if file.is_file() and file.suffix.lower() in SUPPORTED_FORMATS:
            image_files.append(file)

    return image_files


# Resize image while maintaining aspect ratio
def resize_image(image, width, height):

    image.thumbnail((width, height), Image.Resampling.LANCZOS)

    return image


# Process individual image
def process_image(file, output_folder, width, height, output_format, quality):

    try:

        # Get original file size
        original_size = file.stat().st_size / 1024

        # Open original image
        with Image.open(file) as img:

            original_width, original_height = img.size

            # Convert image to RGB if saving as JPEG
            if output_format == "JPEG":

                if img.mode in ("RGBA", "P", "LA"):
                    img = img.convert("RGBA")

                    background = Image.new("RGB", img.size, "white")
                    background.paste(img, mask=img.getchannel("A"))
                    img = background

                else:
                    img = img.convert("RGB")

            # Resize image
            resized_img = resize_image(img, width, height)

            new_width, new_height = resized_img.size

            # Generate output filename
            output_name = file.stem + "." + output_format.lower()

            output_path = output_folder / output_name

            # Save image
            if output_format == "JPEG":

                resized_img.save(
                    output_path,
                    format="JPEG",
                    quality=quality,
                    optimize=True
                )

            else:

                resized_img.save(
                    output_path,
                    format="PNG",
                    optimize=True
                )

            # Get resulting file size
            new_size = output_path.stat().st_size / 1024

            print(f"Processed: {file.name}")

            return [
                file.name,
                f"{original_width}x{original_height}",
                round(original_size, 2),
                f"{new_width}x{new_height}",
                round(new_size, 2),
                output_name,
                "Success"
            ]

    except Exception as e:

        print(f"Error processing {file.name}: {e}")

        return [
            file.name,
            "",
            "",
            "",
            "",
            "",
            f"Failed: {e}"
        ]

def create_thumbnail(file, thumbnail_folder):

    try:

        with Image.open(file) as img:

            # Convert image to RGB for JPEG-compatible processing
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGBA")

            # Resize image while maintaining aspect ratio
            img.thumbnail((150, 150), Image.Resampling.LANCZOS)

            # Generate thumbnail filename
            thumbnail_name = file.stem + "_thumbnail.jpg"

            thumbnail_path = thumbnail_folder / thumbnail_name

            # JPEG does not support transparency
            if img.mode == "RGBA":

                background = Image.new("RGB", img.size, "white")
                background.paste(img, mask=img.getchannel("A"))
                img = background

            else:
                img = img.convert("RGB")

            img.save(
                thumbnail_path,
                format="JPEG",
                quality=80
            )

            print(f"Thumbnail created: {thumbnail_name}")

    except Exception as e:

        print(f"Thumbnail error for {file.name}: {e}")

# Generate CSV report
def generate_report(report_data, output_folder):

    report_path = output_folder / "image_resizing_report.csv"

    headers = [
        "Original Filename",
        "Original Dimensions",
        "Original Size (KB)",
        "Resized Dimensions",
        "Resized Size (KB)",
        "Output Filename",
        "Status"
    ]

    with open(report_path, "w", newline="", encoding="utf-8") as file:

        writer = csv.writer(file)

        writer.writerow(headers)

        writer.writerows(report_data)

    print("\nReport generated successfully!")


# Main function

# Main function
def main():

    print("===== BULK IMAGE RESIZER =====")

    input_folder = Path(input("Enter input folder path: "))

    output_folder = Path(input("Enter output folder path: "))

    if not input_folder.exists() or not input_folder.is_dir():

        print("Invalid input folder!")
        return

    output_folder.mkdir(parents=True, exist_ok=True)

    width = int(input("Enter maximum width: "))
    height = int(input("Enter maximum height: "))

    if width <= 0 or height <= 0:
        print("Width and height must be positive!")
        return

    print("\nSelect output format:")
    print("1. JPEG")
    print("2. PNG")

    choice = input("Enter choice (1 or 2): ")

    if choice == "1":
        output_format = "JPEG"

    elif choice == "2":
        output_format = "PNG"

    else:
        print("Invalid format selection!")
        return

    quality = 85

    if output_format == "JPEG":

        quality = int(input("Enter JPEG quality (1-100): "))

        if quality < 1 or quality > 100:
            print("Quality must be between 1 and 100!")
            return

    # Ask for thumbnail generation
    print("\nGenerate thumbnails?")
    print("1. Yes")
    print("2. No")

    thumbnail_choice = input("Enter choice (1 or 2): ")

    if thumbnail_choice not in ("1", "2"):
        print("Invalid thumbnail selection!")
        return

    generate_thumbnails = thumbnail_choice == "1"

    # Find supported images
    image_files = get_image_files(input_folder)

    if not image_files:

        print("No supported images found!")
        return

    print(f"\nFound {len(image_files)} images.")

    report_data = []

    # Create thumbnail folder if requested
    thumbnail_folder = output_folder / "thumbnails"

    if generate_thumbnails:
        thumbnail_folder.mkdir(parents=True, exist_ok=True)

    # Process all images
    for file in image_files:

        result = process_image(
            file,
            output_folder,
            width,
            height,
            output_format,
            quality
        )

        report_data.append(result)

        # Generate thumbnail
        if generate_thumbnails:
            create_thumbnail(file, thumbnail_folder)

    # Generate CSV report
    generate_report(report_data, output_folder)

    print("\n===== PROCESSING COMPLETED =====")


if __name__ == "__main__":
    main()
