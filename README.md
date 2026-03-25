# word2sent

Convert Whisper JSON or YouTube VTT to LRC/SRT with two processing modes.

## Features

- **Input Formats:**
  - Whisper JSON (with word-level timestamps)
  - YouTube VTT (with word-level timestamps, auto-detected)
  - Standard WebVTT
- **Two Processing Modes:**
  - **Splitter** (default): Preserve segments, split only long ones
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

### Whisper JSON Input

```bash
# JSON input (auto-detected)
word2sent input.json

# Explicit JSON input
word2sent input.json --input-format json
```

### YouTube VTT Input

```bash
# VTT input (auto-detected by .vtt extension)
word2sent input.vtt

# Explicit VTT input
word2sent input.vtt --input-format vtt

# Recommended: Use arranger mode for YouTube VTT
word2sent input.vtt -m arranger -f srt
```

### Processing Modes

**Splitter Mode (Default)**: Preserve segment structure, only split segments that exceed limits:

```bash
word2sent input.json -m splitter
```

**Arranger Mode**: Ignore segments, flatten all words and rearrange:

```bash
word2sent input.json -m arranger
```

### Output Format

```bash
# LRC format (default)
word2sent input.json

# SRT format
word2sent input.json -f srt

# Custom parameters
word2sent input.json -m arranger -f srt --max-words 10 --max-chars 150
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
| `--input-format` | auto | Input format: auto, json, or vtt |
| `--max-duration` | 3600 | Max duration in seconds (rarely triggers) |
| `--max-words` | 12 | Max words per segment |
| `--max-chars` | 200 | Max characters per segment |
| `--mode` | splitter | Processing mode: splitter or arranger |
| `--format` | lrc | Output format: lrc or srt |

## YouTube VTT Support

YouTube VTT files contain word-level timestamps in a special format with overlapping cues. This tool:

1. Parses the word-level timestamps from `<timestamp><c>word</c>` tags
2. Removes duplicate words that appear in multiple overlapping cues
3. Reconstructs clean sentences using the arranger algorithm

**Note**: For YouTube VTT, the `arranger` mode is recommended as it produces cleaner output by ignoring the overlapping cue structure.
