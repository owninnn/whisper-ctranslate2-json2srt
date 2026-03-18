"""Parse Whisper JSON output."""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Word:
    """A single word with timing."""
    start: float  # seconds
    end: float    # seconds
    text: str
    
    @property
    def duration(self) -> float:
        return self.end - self.start


def parse_whisper_json(json_path: Path) -> list[Word]:
    """Parse Whisper JSON and extract word-level timestamps.
    
    Args:
        json_path: Path to Whisper JSON output file
        
    Returns:
        List of Word objects with timing
    """
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    
    words: list[Word] = []
    
    for segment in data.get("segments", []):
        for word_data in segment.get("words", []):
            word = Word(
                start=word_data["start"],
                end=word_data["end"],
                text=word_data["word"].strip()
            )
            words.append(word)
    
    return words
