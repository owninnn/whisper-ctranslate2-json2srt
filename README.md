# whisper-ctranslate2-json2srt

Convert Whisper JSON to LRC/SRT with two processing modes.

## Features

- **Two Processing Modes:**
  - **Splitter** (default): Preserve Whisper segments, split only long ones
  - **Arranger**: Ignore segments, arrange words purely by word info
- Intelligent sentence segmentation based on:
  - Punctuation (periods, question marks, exclamation marks)
  - Comma threshold (break long sentences at commas)
  - Duration limit (default 3600s, rarely triggers)
  - Word count limit (default 12)
  - Character count limit (default 200)
- Clean, modern Python 3.11+ code
- Zero external dependencies

## Installation

```bash
uv pip install -e .
```

## Usage

### Splitter Mode (Default)

Preserve Whisper's segment structure, only split segments that exceed limits:

```bash
whisper-ctranslate2-json2srt input.json
whisper-ctranslate2-json2srt input.json -m splitter
```

### Arranger Mode

Ignore Whisper's segments, flatten all words and rearrange:

```bash
whisper-ctranslate2-json2srt input.json -m arranger
```

### Output Format

```bash
# LRC format (default)
whisper-ctranslate2-json2srt input.json

# SRT format
whisper-ctranslate2-json2srt input.json -f srt

# Custom parameters
whisper-ctranslate2-json2srt input.json -m arranger -f srt --max-words 10 --max-chars 150
```

## Modes Comparison

| Mode | Use Case | Behavior |
|------|----------|----------|
| **Splitter** | Trust Whisper's segmentation | Preserve segments, split only if >12 words or >200 chars |
| **Arranger** | Want pure word-based segmentation | Flatten all words, create new segments based on limits |

## Testing

```bash
uv run pytest tests/ -v
```

## Output Format

### LRC
```
[00:00.00]Hello world.
[00:01.50]This is a test.
```

### SRT
```
1
00:00:00,000 --> 00:00:02,000
Hello world.

2
00:00:01,500 --> 00:00:03,000
This is a test.
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--max-duration` | 3600 | Max duration in seconds (rarely triggers) |
| `--max-words` | 12 | Max words per segment |
| `--max-chars` | 200 | Max characters per segment |
| `--mode` | splitter | Processing mode: splitter or arranger |
| `--format` | lrc | Output format: lrc or srt |
