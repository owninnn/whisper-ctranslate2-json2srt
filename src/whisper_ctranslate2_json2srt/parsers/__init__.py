"""Parsers for different input formats."""

from pathlib import Path

from ..parser import Segment, parse_whisper_json
from .vtt_parser import parse_vtt


def parse_input(input_path: Path, input_format: str = "auto") -> list[Segment]:
    """Parse input file based on format.
    
    Args:
        input_path: Path to input file
        input_format: Input format ("auto", "json", "vtt")
        
    Returns:
        List of segments
        
    Raises:
        ValueError: If format is unknown
    """
    # Auto-detect based on file extension
    if input_format == "auto":
        ext = input_path.suffix.lower()
        if ext == '.vtt':
            input_format = "vtt"
        elif ext == '.json':
            input_format = "json"
        else:
            raise ValueError(f"Cannot auto-detect format for {input_path}. "
                           f"Please specify --input-format")
    
    # Static dispatch
    if input_format == "json":
        return parse_whisper_json(input_path)
    elif input_format == "vtt":
        return parse_vtt(input_path)
    else:
        raise ValueError(f"Unknown input format: {input_format}. "
                        f"Supported: json, vtt")
