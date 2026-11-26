
from pathlib import Path
from collections import Counter
import pandas as pd
import re


# # Folder containing text files
# INPUT_FOLDER = Path("input_files")

BASE_DIR = Path(__file__).parent

INPUT_FOLDER = BASE_DIR / "input_files"

OUTPUT_FILE = BASE_DIR / "analysis_report.csv"

# Output CSV file
OUTPUT_FILE = Path("analysis_report.csv")


# Common words to ignore
STOP_WORDS = {
    "the", "is", "and", "a", "an",
    "was", "were", "are", "to",
    "of", "in", "on", "it", "with",
    "for", "this", "that", "very",
    "my", "i", "we", "they", "he",
    "she", "you", "our", "your"
}


# Read all text files
def get_text_files():

    if not INPUT_FOLDER.exists():
        print("Input folder does not exist!")
        return []

    return list(INPUT_FOLDER.glob("*.txt"))


# Analyse one text file
def analyze_file(file_path):

    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Count words
    words = re.findall(r"\b[a-zA-Z0-9']+\b", content.lower())

    total_words = len(words)

    # Count lines
    total_lines = len(content.splitlines())

    # Count characters
    total_characters = len(content)

    # Remove common words
    filtered_words = [
        word for word in words
        if word not in STOP_WORDS
    ]

    # Find word frequencies
    word_frequency = Counter(filtered_words)

    # Get top 5 frequently occurring words
    top_words = word_frequency.most_common(5)

    top_words_text = ", ".join(
        f"{word} ({count})"
        for word, count in top_words
    )

    return {
        "File": file_path.name,
        "Words": total_words,
        "Lines": total_lines,
        "Characters": total_characters,
        "Top Words": top_words_text
    }


# Find frequently occurring bigrams
def find_bigrams():

    text_files = get_text_files()

    all_bigrams = []

    for file_path in text_files:

        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read().lower()

        # Extract words
        words = re.findall(r"\b[a-zA-Z0-9']+\b", content)

        # Remove common words
        filtered_words = [
            word for word in words
            if word not in STOP_WORDS
        ]

        # Generate two-word combinations
        bigrams = zip(
            filtered_words,
            filtered_words[1:]
        )

        all_bigrams.extend(bigrams)

    # Count bigram frequencies
    bigram_frequency = Counter(all_bigrams)

    # Display top 10 bigrams
    print("\n===== TOP 10 BIGRAMS =====")

    for bigram, count in bigram_frequency.most_common(10):

        phrase = " ".join(bigram)

        print(f"{phrase}: {count}")


# Analyse all files
def analyze_all_files():

    text_files = get_text_files()

    if not text_files:
        print("No text files found!")
        return

    results = []

    for file_path in text_files:

        print(f"Analyzing: {file_path.name}")

        result = analyze_file(file_path)

        results.append(result)

    # Convert results into DataFrame
    df = pd.DataFrame(results)

    # Save CSV report
    df.to_csv(OUTPUT_FILE, index=False)

    print("\n===== TEXT FILE ANALYSIS REPORT =====")

    print(df.to_string(index=False))

    print("\nReport generated successfully!")
    print(f"Saved at: {OUTPUT_FILE.resolve()}")


# Main function
def main():

    analyze_all_files()

    find_bigrams()


if __name__ == "__main__":
    main()
