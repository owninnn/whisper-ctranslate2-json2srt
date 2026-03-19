"""Main conversion logic."""

from pathlib import Path

from .parser import parse_whisper_json
from .segmenter import segment_words


def format_time_lrc(seconds: float) -> str:
    """Format seconds to LRC time format [mm:ss.xx]."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    hundredths = int((seconds % 1) * 100)
    return f"[{minutes:02d}:{secs:02d}.{hundredths:02d}]"


def format_time_srt(seconds: float) -> str:
    """Format seconds to SRT time format HH:MM:SS,mmm."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def convert(json_path: Path, output_path: Path | None = None,
            output_format: str = "lrc",
            max_duration: float = 10.0,
            max_words: int = 15,
            comma_threshold: int = 12) -> Path:
    """Convert Whisper JSON to LRC or SRT.
    
    Args:
        json_path: Path to Whisper JSON file
        output_path: Output path (default: same name with appropriate suffix)
        output_format: Output format ("lrc" or "srt")
        max_duration: Max sentence duration
        max_words: Max words per sentence
        comma_threshold: Words before breaking at comma
        
    Returns:
        Path to output file
    """
    if output_path is None:
        output_path = json_path.with_suffix(f".{output_format}")
    
    # Parse JSON
    words = parse_whisper_json(json_path)
    
    # Segment into sentences
    sentences = segment_words(
        words,
        max_duration=max_duration,
        max_words=max_words,
        comma_threshold=comma_threshold
    )
    
    # Write output
    with open(output_path, "w", encoding="utf-8") as f:
        if output_format == "lrc":
            for sentence in sentences:
                time_tag = format_time_lrc(sentence.start)
                text = sentence.text
                f.write(f"{time_tag}{text}\n")
        else:  # srt
            for i, sentence in enumerate(sentences, 1):
                start_time = format_time_srt(sentence.start)
                end_time = format_time_srt(sentence.end)
                text = sentence.text
                f.write(f"{i}\n{start_time} --> {end_time}\n{text}\n\n")
    
    return output_path
