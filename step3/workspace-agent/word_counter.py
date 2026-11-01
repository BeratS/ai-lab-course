import re
import sys
from collections import Counter


def tokenize(text):
    """Split text into lowercase words (letters, digits, apostrophes)."""
    return re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z]+)*", text.lower())


def count_words(text):
    """Return total number of words in text."""
    return len(tokenize(text))


def word_frequencies(text):
    """Return a Counter mapping each word to its frequency."""
    return Counter(tokenize(text))


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            text = f.read()
    else:
        text = sys.stdin.read()
    print("Total words:", count_words(text))
    for word, n in word_frequencies(text).most_common(10):
        print(f"{word}: {n}")


if __name__ == "__main__":
    main()
