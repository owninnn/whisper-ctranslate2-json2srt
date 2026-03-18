# json2lrc

Convert Whisper JSON to LRC with intelligent sentence segmentation.

## Features

- Parse Whisper JSON output with word-level timestamps
- Intelligent sentence segmentation based on:
  - Punctuation (periods, question marks, exclamation marks)
  - Comma threshold (break long sentences at commas)
  - Duration limit (max 10 seconds per sentence)
  - Word count limit (max 15 words per sentence)
- Clean, modern Python 3.11+ code
- Zero external dependencies

## Installation

```bash
uv pip install -e .
```

## Usage

```bash
# Basic usage
json2lrc whisper_output.json

# With custom parameters
json2lrc whisper_output.json -o output.lrc --max-duration 8 --max-words 12

# Using uvx
uvx --from json2lrc json2lrc whisper_output.json
```

## Testing

```bash
uv run pytest tests/ -v
```

## Output Format

LRC format with intelligent line breaks:

```
[00:00.00]Hello world.
[00:01.50]This is a test.
[00:03.00]Another sentence here.
```

## Comparison with SRT

The tool generates LRC that matches the timing of Whisper's SRT output,
but with better sentence boundaries for karaoke-style display.
