"""Parse Whisper JSON output."""

import json
from pathlib import Path

from ..model import Segment, Word


def parse_whisper_json(json_path: Path) -> list[Segment]:
    """Parse Whisper JSON preserving segment structure.
    
    Args:
        json_path: Path to Whisper JSON output file
        
    Returns:
        List of Segment objects with words
    """
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    
    segments: list[Segment] = []
    
    for seg_data in data.get("segments", []):
        segment = Segment(
            id=seg_data.get("id", 0),
            start=seg_data["start"],
            end=seg_data["end"],
            text=seg_data.get("text", "").strip()
        )
        
        # Parse words within segment
        for word_data in seg_data.get("words", []):
            word = Word(
                start=word_data["start"],
                end=word_data["end"],
                text=word_data["word"].strip()
            )
            segment.words.append(word)
        
        segments.append(segment)
    
    return segments
