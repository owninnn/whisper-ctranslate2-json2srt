"""Convert Whisper JSON to LRC/SRT, preserving segments and splitting only long ones."""

from .converter import convert, format_time_lrc, format_time_srt
from .parser import parse_whisper_json, Segment, Word
from .segmenter import process_segments, SubSegment

__all__ = [
    "convert",
    "parse_whisper_json",
    "process_segments",
    "format_time_lrc",
    "format_time_srt",
    "Segment",
    "SubSegment",
    "Word",
]
__version__ = "0.2.0"
