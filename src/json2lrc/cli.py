"""Command-line interface."""

import argparse
import sys
from pathlib import Path

from .converter import convert


def main():
    parser = argparse.ArgumentParser(
        description="Convert Whisper JSON to LRC/SRT with intelligent segmentation"
    )
    parser.add_argument("json_file", type=Path, help="Whisper JSON file")
    parser.add_argument("-o", "--output", type=Path, help="Output file")
    parser.add_argument(
        "-f", "--format", choices=["lrc", "srt"], default="lrc",
        help="Output format (default: lrc)"
    )
    parser.add_argument(
        "--max-duration", type=float, default=10.0,
        help="Max sentence duration in seconds (default: 10)"
    )
    parser.add_argument(
        "--max-words", type=int, default=15,
        help="Max words per sentence (default: 15)"
    )
    parser.add_argument(
        "--comma-threshold", type=int, default=12,
        help="Words before breaking at comma (default: 12)"
    )
    
    args = parser.parse_args()
    
    if not args.json_file.exists():
        print(f"Error: File not found: {args.json_file}", file=sys.stderr)
        sys.exit(1)
    
    output = convert(
        args.json_file,
        args.output,
        output_format=args.format,
        max_duration=args.max_duration,
        max_words=args.max_words,
        comma_threshold=args.comma_threshold
    )
    
    print(f"Converted: {output}")


if __name__ == "__main__":
    main()
