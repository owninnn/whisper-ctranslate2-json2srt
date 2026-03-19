"""Convert Whisper JSON to LRC/SRT with two modes: splitter and arranger."""

from .converter import convert, format_time_lrc, format_time_srt
from .parser import parse_whisper_json, Segment, Word
from .splitter import process_segments
from .arranger import arrange_words

__all__ = [
    "convert",
    "parse_whisper_json",
    "process_segments",
    "arrange_words",
    "format_time_lrc",
    "format_time_srt",
    "Segment",
    "Word",
]
__version__ = "0.3.0"
