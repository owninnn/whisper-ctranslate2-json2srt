"""Convert Whisper JSON to LRC/SRT with intelligent sentence segmentation."""

from .converter import convert, format_time_lrc, format_time_srt
from .parser import parse_whisper_json
from .segmenter import segment_words

__all__ = ["convert", "parse_whisper_json", "segmenter", "format_time_lrc", "format_time_srt"]
__version__ = "0.1.0"
