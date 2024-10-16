""" Create a report of word frequency in a given file or directory. """

# Standard imports
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import logging
import re
import time

# Third party imports

# Project imports


# Regular expressions for managing USFM and Markdown
HEADING_REGEX = re.compile(r"^\\h (.*)$")
CHAPTER_REGEX = re.compile(r"^\\c (.*)$")
VERSE_REGEX = re.compile(r"^\\v (\d+) (.*)$")
FOOTNOTE_REGEX = re.compile(r"\\f(.*?)\\f\*")
USFM_MARKER_REGEX = re.compile(r"\\\w+(\d+)?")
NUMBER_REGEX = re.compile(r"\d+")
PUNCTUATION_REGEX = re.compile(r"""[\[\]*+?!()"',.:;—]+""")


@dataclass
class VerseReference:
    """Encapsulates a reference to a verse"""

    book: str
    chapter: int
    verse: int
    file_path: Path
    text: str

    def __str__(self) -> str:
        """Return a string representation of the verse reference, e.g., 'Genesis 1:6'"""
        return f"{self.book} {self.chapter}:{self.verse}"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, VerseReference):
            return NotImplemented
        return (
            self.book == other.book
            and self.chapter == other.chapter
            and self.verse == other.verse
        )

    def __hash__(self) -> int:
        """Implement hash to allow caching and quick lookups"""
        return hash((self.book, self.chapter, self.verse))


@dataclass
class WordEntry:
    """Contains metadata about a word"""

    # Text of word
    word: str

    # This is a list of references found for this word.
    #
    # TRICKY: Because there can be duplicate verses in which a word appears more
    # than once, we want to be able to efficiently check the collection for a
    # matching item before inserting.  To do this with a list is super slow.  To
    # do it with a set would lose the order of the references (we want to keep
    # them in canonical order).
    #
    # So we apply a huge hack -- As of Python 3.7, dictionaries now retain
    # insertion order.  That means we can put each reference as a key in the
    # dictionary, and it will do double-duty for us -- keeping uniqueness like a
    # set, but retaining order like a list.  Since we don't care about the
    # values, we'll set them all to None.
    #
    # This is a bit strange, but I can't argue with the results -- the merging
    # process on my laptop went from 90 seconds for a list-based approach to
    # 0.3s (!!) with a dictionary approach.
    refs: dict[VerseReference, None]


def process_file(path: Path) -> dict[str, WordEntry]:
    """Process a file"""

    begin = time.time()
    logging.debug("%s: Reading %s", path.name, path)

    word_entries: dict[str, WordEntry] = {}

    current_book: str = ""
    current_chapter: str = ""
    current_verse: str = ""

    with open(path, "r", encoding="utf-8") as infile:
        for line in infile.readlines():

            # Process heading
            match = HEADING_REGEX.match(line)
            if match:
                current_book = match.group(1)
                continue

            # Process chapter
            match = CHAPTER_REGEX.match(line)
            if match:
                current_chapter = match.group(1)
                continue

            # Process verse
            match = VERSE_REGEX.match(line)
            if match:
                current_verse = match.group(1)

            # Don't process if we haven't gotten to verses yet
            if current_chapter == "" or current_verse == "":
                continue

            # Clean up non-words
            line = FOOTNOTE_REGEX.sub(" ", line)
            line = USFM_MARKER_REGEX.sub(" ", line)
            line = NUMBER_REGEX.sub(" ", line)
            text = line
            line = PUNCTUATION_REGEX.sub(" ", line)
            line = line.strip()
            if len(line) == 0:
                continue

            # Extract words
            words = line.split()
            for word in words:
                word = word.strip()
                if len(word) == 0:
                    continue
                verse_ref = VerseReference(
                    current_book, int(current_chapter), int(current_verse), path, text
                )

                # If new word, create entry for it
                if word not in word_entries:
                    word_entry = WordEntry(word, {verse_ref: None})
                    word_entries[word] = word_entry

                # Otherwise update entry if new ref
                else:
                    word_entry = word_entries[word]
                    if verse_ref not in word_entry.refs:
                        word_entry.refs[verse_ref] = None

    elapsed = time.time() - begin
    logging.debug(
        "%s: Finished, found %d unique words in %0.2fs.",
        path.name,
        len(word_entries),
        elapsed,
    )
    return word_entries


def process_file_or_dir(path: Path) -> dict[str, WordEntry]:  # pragma: no cover
    """Main function"""

    word_entries: dict[str, WordEntry] = {}

    # Check path argument
    if path.is_file():
        return process_file(path)

    if not path.is_dir():
        logging.error("Unable to process path: %s", path)
        return word_entries

    usfm_files = sorted(list(path.rglob("*.usfm")) + list(path.rglob("*.USFM")))

    # Process files in parallel
    begin = time.time()
    with ProcessPoolExecutor() as executor:
        all_word_entries = list(executor.map(process_file, usfm_files))
    elapsed = time.time() - begin
    logging.debug("Finished processing files in %0.2fs", elapsed)

    # Collate refs into master list -- has to be sequential because of shared dictionary
    begin = time.time()
    logging.debug("Start merge of %d word lists", len(all_word_entries))
    count = 0
    for file_word_entries in all_word_entries:
        for file_word_entry in file_word_entries.values():
            word = file_word_entry.word
            if word in word_entries:
                word_entry = word_entries[word]
                for ref in file_word_entry.refs:
                    if ref not in word_entry.refs:
                        word_entry.refs[ref] = None
            else:
                word_entries[file_word_entry.word] = file_word_entry
        count += 1
        logging.debug("Working, merged %d/%d so far...", count, len(all_word_entries))
    elapsed = time.time() - begin
    logging.debug(
        "Finished merge in %0.2fs, total of %d unique words",
        elapsed,
        len(word_entries),
    )

    return word_entries
