"""Main conversion logic supporting both splitter and arranger modes."""

from pathlib import Path

from .parser import parse_whisper_json
from .splitter import process_segments as split_segments
from .arranger import arrange_words


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
            mode: str = "splitter",
            max_duration: float = 3600.0,
            max_words: int = 12,
            max_chars: int = 200,
            comma_threshold: int = 12) -> Path:
    """Convert Whisper JSON to LRC or SRT.
    
    Args:
        json_path: Path to Whisper JSON file
        output_path: Output path (default: same name with appropriate suffix)
        output_format: Output format ("lrc" or "srt")
        mode: Processing mode ("splitter" or "arranger")
            - splitter: Preserve Whisper segments, split only long ones
            - arranger: Ignore segments, arrange words purely by word info
        max_duration: Max duration in seconds
        max_words: Max words per segment
        max_chars: Max characters per segment
        comma_threshold: Words before splitting at comma
        
    Returns:
        Path to output file
    """
    if output_path is None:
        output_path = json_path.with_suffix(f".{output_format}")
    
    # Parse JSON
    segments = parse_whisper_json(json_path)
    
    if mode == "splitter":
        # Splitter mode: Preserve segments, split only long ones
        sub_segments = split_segments(
            segments,
            max_duration=max_duration,
            max_words=max_words,
            max_chars=max_chars,
            comma_threshold=comma_threshold
        )
        # Convert to output format
        items = [(s.start, s.end, s.text) for s in sub_segments]
    else:
        # Arranger mode: Flatten all words, arrange purely
        all_words = []
        for seg in segments:
            all_words.extend(seg.words)
        
        arranged = arrange_words(
            all_words,
            max_duration=max_duration,
            max_words=max_words,
            max_chars=max_chars,
            comma_threshold=comma_threshold
        )
        # Convert to output format
        items = [(s.start, s.end, s.text) for s in arranged]
    
    # Write output
    with open(output_path, "w", encoding="utf-8") as f:
        if output_format == "lrc":
            for start, end, text in items:
                time_tag = format_time_lrc(start)
                f.write(f"{time_tag}{text}\n")
        else:  # srt
            for i, (start, end, text) in enumerate(items, 1):
                start_time = format_time_srt(start)
                end_time = format_time_srt(end)
                f.write(f"{i}\n{start_time} --> {end_time}\n{text}\n\n")
    
    return output_path
