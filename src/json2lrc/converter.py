"""Main conversion logic."""

from pathlib import Path

from .parser import parse_whisper_json
from .segmenter import segment_words


def format_time(seconds: float) -> str:
    """Format seconds to LRC time format [mm:ss.xx]."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    hundredths = int((seconds % 1) * 100)
    return f"[{minutes:02d}:{secs:02d}.{hundredths:02d}]"


def convert(json_path: Path, lrc_path: Path | None = None,
            max_duration: float = 10.0,
            max_words: int = 15,
            comma_threshold: int = 12) -> Path:
    """Convert Whisper JSON to LRC.
    
    Args:
        json_path: Path to Whisper JSON file
        lrc_path: Output path (default: same name with .lrc)
        max_duration: Max sentence duration
        max_words: Max words per sentence
        comma_threshold: Words before breaking at comma
        
    Returns:
        Path to output LRC file
    """
    if lrc_path is None:
        lrc_path = json_path.with_suffix(".lrc")
    
    # Parse JSON
    words = parse_whisper_json(json_path)
    
    # Segment into sentences
    sentences = segment_words(
        words,
        max_duration=max_duration,
        max_words=max_words,
        comma_threshold=comma_threshold
    )
    
    # Write LRC
    with open(lrc_path, "w", encoding="utf-8") as f:
        for sentence in sentences:
            time_tag = format_time(sentence.start)
            text = sentence.text
            f.write(f"{time_tag}{text}\n")
    
    return lrc_path
