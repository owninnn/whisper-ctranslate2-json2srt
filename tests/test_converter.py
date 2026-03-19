"""Tests for whisper-ctranslate2-json2srt converter."""

import json
import tempfile
from pathlib import Path

import pytest

from whisper_ctranslate2_json2srt.converter import convert, format_time_lrc, format_time_srt
from whisper_ctranslate2_json2srt.parser import Segment, Word, parse_whisper_json
from whisper_ctranslate2_json2srt.splitter import process_segments
from whisper_ctranslate2_json2srt.arranger import arrange_words


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
    ]
    
    json_path = create_test_json(segments_data)
    segments = parse_whisper_json(json_path)
    
    assert len(segments) == 1
    assert segments[0].id == 0
    assert segments[0].text == "Hello world."
    assert len(segments[0].words) == 2
    
    json_path.unlink()


# ===== Splitter Mode Tests =====

def test_splitter_short_segments():
    """Test that splitter preserves short segments."""
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
    ]
    
    sub_segments = process_segments(segments, max_duration=3600.0, max_words=12, max_chars=200)
    
    # Short segments should NOT be split
    assert len(sub_segments) == 1
    assert sub_segments[0].text == "Short segment."


def test_splitter_long_words():
    """Test splitter splits long segments by word count."""
    segments = [
        Segment(
            id=0,
            start=0.0,
            end=5.0,
            text="Many words here.",
            words=[Word(i, i+0.5, f"word{i}") for i in range(20)]
        ),
    ]
    
    sub_segments = process_segments(segments, max_duration=3600.0, max_words=12, max_chars=200)
    
    # Should be split into 2 parts (20 / 12)
    assert len(sub_segments) == 2


# ===== Arranger Mode Tests =====

def test_arranger_basic():
    """Test arranger mode flattens and rearranges words."""
    words = [
        Word(0.0, 0.5, "Hello"),
        Word(0.5, 1.0, "world."),
        Word(1.5, 2.0, "This"),
        Word(2.0, 2.5, "is"),
        Word(2.5, 3.0, "test."),
    ]
    
    arranged = arrange_words(words, max_duration=3600.0, max_words=12, max_chars=200)
    
    # Should create segments based on punctuation
    assert len(arranged) == 2
    assert arranged[0].text == "Hello world."
    assert arranged[1].text == "This is test."


def test_arranger_long_words():
    """Test arranger splits by word count."""
    words = [Word(i, i+0.5, f"word{i}") for i in range(20)]
    
    arranged = arrange_words(words, max_duration=3600.0, max_words=5, max_chars=200)
    
    # Should be split into 4 parts (20 / 5)
    assert len(arranged) == 4


# ===== Converter Tests =====

def test_convert_splitter_mode():
    """Test converter in splitter mode."""
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
    
    result = convert(json_path, lrc_path, output_format="lrc", mode="splitter")
    
    assert result == lrc_path
    assert lrc_path.exists()
    
    content = lrc_path.read_text()
    assert "[00:00.00]Hello world." in content
    
    json_path.unlink()
    lrc_path.unlink()


def test_convert_arranger_mode():
    """Test converter in arranger mode."""
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
            "start": 3.0,
            "end": 5.0,
            "text": " Second part.",
            "words": [
                {"start": 3.0, "end": 4.0, "word": " Second"},
                {"start": 4.0, "end": 5.0, "word": " part."},
            ]
        },
    ]
    
    json_path = create_test_json(segments_data)
    
    with tempfile.NamedTemporaryFile(suffix=".lrc", delete=False) as f:
        lrc_path = Path(f.name)
    
    result = convert(json_path, lrc_path, output_format="lrc", mode="arranger")
    
    assert result == lrc_path
    assert lrc_path.exists()
    
    content = lrc_path.read_text()
    # In arranger mode, segments are flattened
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
    
    result = convert(json_path, srt_path, output_format="srt", mode="splitter")
    
    assert result == srt_path
    assert srt_path.exists()
    
    content = srt_path.read_text()
    assert "1\n00:00:00,000 --> 00:00:02,000\nHello world." in content
    
    json_path.unlink()
    srt_path.unlink()
