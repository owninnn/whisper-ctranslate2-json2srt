"""Convert Whisper JSON to LRC with intelligent sentence segmentation."""

from .converter import convert
from .parser import parse_whisper_json
from .segmenter import segment_words

__all__ = ["convert", "parse_whisper_json", "segmenter"]
__version__ = "0.1.0"
