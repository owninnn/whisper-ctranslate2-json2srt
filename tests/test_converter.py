"""Tests for json2lrc converter."""

import json
import tempfile
from pathlib import Path

import pytest

from json2lrc.converter import convert, format_time_lrc, format_time_srt
from json2lrc.parser import Segment, Word, parse_whisper_json
from json2lrc.segmenter import process_segments, SubSegment


def create_test_json(segments_data: list[dict]) -> Path:
    """Create a test JSON file with segment structure."""
    data = {
        "text": " ".join(seg["text"] for seg in segments_data),
        "segments": segments_data
    }
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        return Path(f.name)


def test_format_time_lrc():
    """Test LRC time formatting."""
    assert format_time_lrc(0) == "[00:00.00]"
    assert format_time_lrc(61.5) == "[01:01.50]"
    assert format_time_lrc(123.456) == "[02:03.45]"


def test_format_time_srt():
    """Test SRT time formatting."""
    assert format_time_srt(0) == "00:00:00,000"
    assert format_time_srt(61.5) == "00:01:01,500"
    assert format_time_srt(3661.123) == "01:01:01,123"


def test_parse_whisper_json():
    """Test JSON parsing preserving segments."""
    segments_data = [
        {
            "id": 0,
            "start": 0.0,
            "end": 2.0,
            "text": " Hello world.",
            "words": [
                {"start": 0.0, "end": 0.5, "word": " Hello"},
                {"start": 0.5, "end": 2.0, "word": " world."},
            ]
        },
        {
            "id": 1,
            "start": 2.5,
            "end": 5.0,
            "text": " This is test.",
            "words": [
                {"start": 2.5, "end": 3.0, "word": " This"},
                {"start": 3.0, "end": 3.5, "word": " is"},
                {"start": 3.5, "end": 5.0, "word": " test."},
            ]
        }
    ]
    
    json_path = create_test_json(segments_data)
    segments = parse_whisper_json(json_path)
    
    assert len(segments) == 2
    assert segments[0].id == 0
    assert segments[0].text == "Hello world."
    assert len(segments[0].words) == 2
    assert segments[0].words[0].text == "Hello"
    
    json_path.unlink()


def test_process_segments_short():
    """Test that short segments are preserved (not split)."""
    segments = [
        Segment(
            id=0,
            start=0.0,
            end=3.0,
            text="Short segment.",
            words=[
                Word(0.0, 1.0, "Short"),
                Word(1.0, 2.0, "segment."),
            ]
        ),
        Segment(
            id=1,
            start=3.5,
            end=6.0,
            text="Another short one.",
            words=[
                Word(3.5, 4.0, "Another"),
                Word(4.0, 4.5, "short"),
                Word(4.5, 6.0, "one."),
            ]
        ),
    ]
    
    sub_segments = process_segments(segments, max_duration=3600.0, max_words=12, max_chars=200)
    
    # Short segments should NOT be split
    assert len(sub_segments) == 2
    assert sub_segments[0].text == "Short segment."
    assert sub_segments[1].text == "Another short one."


def test_process_segments_long_words():
    """Test splitting long segments by word count."""
    segments = [
        Segment(
            id=0,
            start=0.0,
            end=5.0,
            text="Many words here that exceed limit.",
            words=[Word(i, i+0.5, f"word{i}") for i in range(20)]  # 20 words
        ),
    ]
    
    sub_segments = process_segments(segments, max_duration=3600.0, max_words=12, max_chars=200)
    
    # Should be split into 2 parts (20 / 12)
    assert len(sub_segments) == 2


def test_process_segments_long_chars():
    """Test splitting long segments by character count."""
    # Create words with long text to exceed char limit
    long_words = []
    for i in range(5):
        text = f"word{i}" + "A" * 30  # Each word is ~37 chars
        long_words.append(Word(i, i+0.5, text))
    
    segments = [
        Segment(
            id=0,
            start=0.0,
            end=5.0,
            text=" ".join(w.text for w in long_words),  # ~185 chars
            words=long_words
        ),
    ]
    
    sub_segments = process_segments(segments, max_duration=3600.0, max_words=100, max_chars=50)
    
    # Should be split due to char limit
    assert len(sub_segments) >= 2


def test_process_segments_punctuation():
    """Test splitting at punctuation."""
    segments = [
        Segment(
            id=0,
            start=0.0,
            end=12.0,  # Long duration
            text="First sentence. Second sentence. Third one.",
            words=[
                Word(0.0, 1.0, "First"),
                Word(1.0, 2.0, "sentence."),
                Word(2.5, 3.0, "Second"),
                Word(3.0, 4.0, "sentence."),
                Word(5.0, 6.0, "Third"),
                Word(6.0, 12.0, "one."),
            ]
        ),
    ]
    
    # Use stricter limits to force splitting
    sub_segments = process_segments(segments, max_duration=3600.0, max_words=4, max_chars=200)
    
    # Should split at sentence endings
    assert len(sub_segments) >= 2
    assert "First sentence." in [s.text for s in sub_segments]


def test_convert_to_lrc():
    """Test full conversion to LRC."""
    segments_data = [
        {
            "id": 0,
            "start": 0.0,
            "end": 2.0,
            "text": " Hello world.",
            "words": [
                {"start": 0.0, "end": 0.5, "word": " Hello"},
                {"start": 0.5, "end": 2.0, "word": " world."},
            ]
        },
    ]
    
    json_path = create_test_json(segments_data)
    
    with tempfile.NamedTemporaryFile(suffix=".lrc", delete=False) as f:
        lrc_path = Path(f.name)
    
    result = convert(json_path, lrc_path, output_format="lrc")
    
    assert result == lrc_path
    assert lrc_path.exists()
    
    content = lrc_path.read_text()
    assert "[00:00.00]Hello world." in content
    
    json_path.unlink()
    lrc_path.unlink()


def test_convert_to_srt():
    """Test conversion to SRT format."""
    segments_data = [
        {
            "id": 0,
            "start": 0.0,
            "end": 2.0,
            "text": " Hello world.",
            "words": [
                {"start": 0.0, "end": 0.5, "word": " Hello"},
                {"start": 0.5, "end": 2.0, "word": " world."},
            ]
        },
    ]
    
    json_path = create_test_json(segments_data)
    
    with tempfile.NamedTemporaryFile(suffix=".srt", delete=False) as f:
        srt_path = Path(f.name)
    
    result = convert(json_path, srt_path, output_format="srt")
    
    assert result == srt_path
    assert srt_path.exists()
    
    content = srt_path.read_text()
    assert "1\n00:00:00,000 --> 00:00:02,000\nHello world." in content
    
    json_path.unlink()
    srt_path.unlink()
