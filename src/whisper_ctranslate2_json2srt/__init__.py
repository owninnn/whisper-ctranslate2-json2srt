"""whisper-ctranslate2-json2srt: Convert Whisper JSON or YouTube VTT to LRC/SRT with two modes: splitter and arranger."""

from .converter import convert, format_time_lrc, format_time_srt
from .model import Segment, Word
from .parsers.whisper_json_parser import parse_whisper_json
from .parsers import parse_input
from .parsers.vtt_parser import parse_vtt, parse_youtube_vtt, parse_standard_vtt
from .splitter import process_segments
from .arranger import arrange_words

__all__ = [
    "convert",
    "parse_whisper_json",
    "parse_input",
    "parse_vtt",
    "parse_youtube_vtt",
    "parse_standard_vtt",
    "process_segments",
    "arrange_words",
    "format_time_lrc",
    "format_time_srt",
    "Segment",
    "Word",
]
__version__ = "0.3.0"
