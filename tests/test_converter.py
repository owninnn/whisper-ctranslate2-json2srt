"""Tests for json2lrc converter."""

import json
import tempfile
from pathlib import Path

import pytest

from json2lrc.converter import convert, format_time
from json2lrc.parser import Word, parse_whisper_json
from json2lrc.segmenter import Sentence, segment_words


def create_test_json(words_data: list[dict]) -> Path:
    """Create a test JSON file."""
    data = {
        "text": " ".join(w["word"] for w in words_data),
        "segments": [
            {
                "words": words_data
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        return Path(f.name)


def test_format_time():
    """Test time formatting."""
    assert format_time(0) == "[00:00.00]"
    assert format_time(61.5) == "[01:01.50]"
    assert format_time(123.456) == "[02:03.45]"


def test_parse_whisper_json():
    """Test JSON parsing."""
    words_data = [
        {"start": 0.0, "end": 0.5, "word": " Hello"},
        {"start": 0.5, "end": 1.0, "word": " world"},
    ]
    
    json_path = create_test_json(words_data)
    words = parse_whisper_json(json_path)
    
    assert len(words) == 2
    assert words[0].text == "Hello"
    assert words[0].start == 0.0
    assert words[1].text == "world"
    
    json_path.unlink()


def test_segment_words_basic():
    """Test basic word segmentation."""
    words = [
        Word(0.0, 0.5, "Hello"),
        Word(0.5, 1.0, "world."),
        Word(1.5, 2.0, "This"),
        Word(2.0, 2.5, "is"),
        Word(2.5, 3.0, "test."),
    ]
    
    sentences = segment_words(words)
    
    assert len(sentences) == 2
    assert sentences[0].text == "Hello world."
    assert sentences[1].text == "This is test."


def test_segment_words_max_duration():
    """Test segmentation with max duration."""
    words = [
        Word(0.0, 1.0, "Word1"),
        Word(1.0, 2.0, "Word2"),
        Word(2.0, 12.0, "Word3"),  # This exceeds max_duration
    ]
    
    sentences = segment_words(words, max_duration=5.0)
    
    assert len(sentences) >= 2  # Should split due to duration


def test_segment_words_max_words():
    """Test segmentation with max words."""
    words = [Word(i, i+1, f"Word{i}") for i in range(20)]
    
    sentences = segment_words(words, max_words=5)
    
    assert len(sentences) == 4  # 20 words / 5 per sentence


def test_segment_words_comma():
    """Test segmentation at comma."""
    words = [
        Word(0.0, 0.5, "This"),
        Word(0.5, 1.0, "is"),
        Word(1.0, 1.5, "a"),
        Word(1.5, 2.0, "long"),
        Word(2.0, 2.5, "sentence,"),
        Word(2.5, 3.0, "continued."),
    ]
    
    sentences = segment_words(words, comma_threshold=5)
    
    # Should break at comma since we have 5 words before it
    assert len(sentences) == 2


def test_convert():
    """Test full conversion."""
    words_data = [
        {"start": 0.0, "end": 0.5, "word": " Hello"},
        {"start": 0.5, "end": 1.0, "word": " world."},
        {"start": 1.5, "end": 2.0, "word": " This"},
        {"start": 2.0, "end": 2.5, "word": " is"},
        {"start": 2.5, "end": 3.0, "word": " test."},
    ]
    
    json_path = create_test_json(words_data)
    
    with tempfile.NamedTemporaryFile(suffix=".lrc", delete=False) as f:
        lrc_path = Path(f.name)
    
    result = convert(json_path, lrc_path)
    
    assert result == lrc_path
    assert lrc_path.exists()
    
    content = lrc_path.read_text()
    assert "[00:00.00]Hello world." in content
    assert "[00:01.50]This is test." in content
    
    json_path.unlink()
    lrc_path.unlink()


def test_compare_with_srt():
    """Compare LRC output with original SRT timing."""
    # This test would need actual Whisper output files
    # For now, just verify the structure
    pass
