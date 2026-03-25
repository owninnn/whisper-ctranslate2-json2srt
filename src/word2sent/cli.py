"""Command-line interface."""

import argparse
import sys
from pathlib import Path

from .converter import convert


def main():
    parser = argparse.ArgumentParser(
        description="Convert Whisper JSON or YouTube VTT to LRC/SRT with splitter or arranger mode"
    )
    parser.add_argument("input_file", type=Path, help="Input file (Whisper JSON or YouTube VTT)")
    parser.add_argument("-o", "--output", type=Path, help="Output file")
    parser.add_argument(
        "-f", "--format", choices=["lrc", "srt"], default="lrc",
        help="Output format (default: lrc)"
    )
    parser.add_argument(
        "-m", "--mode", choices=["splitter", "arranger"], default="splitter",
        help="Processing mode: splitter (preserve segments) or arranger (ignore segments)"
    )
    parser.add_argument(
        "--input-format", choices=["auto", "json", "vtt"], default="auto",
        help="Input format (default: auto-detect)"
    )
    parser.add_argument(
        "--max-duration", type=float, default=3600.0,
        help="Max sentence duration in seconds (default: 3600)"
    )
    parser.add_argument(
        "--max-words", type=int, default=12,
        help="Max words per sentence (default: 12)"
    )
    parser.add_argument(
        "--max-chars", type=int, default=200,
        help="Max characters per sentence (default: 200)"
    )
    
    args = parser.parse_args()
    
    if not args.input_file.exists():
        print(f"Error: File not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)
    
    output = convert(
        args.input_file,
        args.output,
        output_format=args.format,
        mode=args.mode,
        max_duration=args.max_duration,
        max_words=args.max_words,
        max_chars=args.max_chars,
        input_format=args.input_format
    )
    
    print(f"Converted: {output}")


if __name__ == "__main__":
    main()
