"""Main conversion logic."""

from pathlib import Path

from .parser import parse_whisper_json
from .segmenter import process_segments


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
            max_duration: float = 3600.0,
            max_words: int = 12,
            max_chars: int = 200,
            comma_threshold: int = 12) -> Path:
    """Convert Whisper JSON to LRC or SRT, splitting only long segments.
    
    Args:
        json_path: Path to Whisper JSON file
        output_path: Output path (default: same name with appropriate suffix)
        output_format: Output format ("lrc" or "srt")
        max_duration: Max duration in seconds (default 3600, rarely triggers)
        max_words: Max words per segment (default 12)
        max_chars: Max characters per segment (default 200)
        comma_threshold: Words before splitting at comma
        
    Returns:
        Path to output file
    """
    if output_path is None:
        output_path = json_path.with_suffix(f".{output_format}")
    
    # Parse JSON (preserving segment structure)
    segments = parse_whisper_json(json_path)
    
    # Process segments (split only long ones)
    sub_segments = process_segments(
        segments,
        max_duration=max_duration,
        max_words=max_words,
        max_chars=max_chars,
        comma_threshold=comma_threshold
    )
    
    # Write output
    with open(output_path, "w", encoding="utf-8") as f:
        if output_format == "lrc":
            for sub_seg in sub_segments:
                time_tag = format_time_lrc(sub_seg.start)
                f.write(f"{time_tag}{sub_seg.text}\n")
        else:  # srt
            for i, sub_seg in enumerate(sub_segments, 1):
                start_time = format_time_srt(sub_seg.start)
                end_time = format_time_srt(sub_seg.end)
                f.write(f"{i}\n{start_time} --> {end_time}\n{sub_seg.text}\n\n")
    
    return output_path
