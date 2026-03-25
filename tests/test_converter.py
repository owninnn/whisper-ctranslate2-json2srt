"""Tests for word2sent converter."""

import json
import tempfile
from pathlib import Path

import pytest

from word2sent.converter import (
    convert,
    format_time_lrc,
    format_time_srt,
)
from word2sent.model import Segment, Word
from word2sent.parsers.whisper_json_parser import parse_whisper_json
from word2sent.splitter import process_segments
from word2sent.arranger import arrange_words
from word2sent.parsers.vtt_parser import (
    parse_vtt,
    parse_youtube_vtt,
    parse_standard_vtt,
    parse_time,
)


def create_test_json(segments_data: list[dict]) -> Path:
    """Create a test JSON file with segment structure."""
    data = {
        "text": " ".join(seg["text"] for seg in segments_data),
        "segments": segments_data,
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
            ],
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
            ],
        ),
    ]

    sub_segments = process_segments(
        segments, max_duration=3600.0, max_words=12, max_chars=200
    )

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
            words=[Word(i, i + 0.5, f"word{i}") for i in range(20)],
        ),
    ]

    sub_segments = process_segments(
        segments, max_duration=3600.0, max_words=12, max_chars=200
    )

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
    words = [Word(i, i + 0.5, f"word{i}") for i in range(20)]

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
            ],
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
            ],
        },
        {
            "id": 1,
            "start": 3.0,
            "end": 5.0,
            "text": " Second part.",
            "words": [
                {"start": 3.0, "end": 4.0, "word": " Second"},
                {"start": 4.0, "end": 5.0, "word": " part."},
            ],
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
            ],
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


# ===== VTT Parser Tests =====


def test_parse_time():
    """Test time parsing from VTT format."""
    assert parse_time("00:00:00.000") == 0.0
    assert parse_time("00:01:30.500") == 90.5
    assert parse_time("01:30:45.250") == 5445.25
    assert parse_time("30.500") == 30.5
    assert parse_time("00:30.500") == 30.5


def test_parse_standard_vtt_basic():
    """Test parsing standard WebVTT file."""
    vtt_content = """WEBVTT

00:00:01.000 --> 00:00:03.000
Hello world

00:00:04.000 --> 00:00:06.000
Second line
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".vtt", delete=False, encoding="utf-8"
    ) as f:
        f.write(vtt_content)
        vtt_path = Path(f.name)

    try:
        segments = parse_standard_vtt(vtt_path)
        assert len(segments) == 2
        assert segments[0].text == "Hello world"
        assert segments[0].start == 1.0
        assert segments[0].end == 3.0
        assert segments[1].text == "Second line"
    finally:
        vtt_path.unlink()


def test_parse_standard_vtt_multiline():
    """Test parsing standard VTT with multiline text."""
    vtt_content = """WEBVTT

00:00:01.000 --> 00:00:04.000
Line 1
Line 2 continues

00:00:05.000 --> 00:00:07.000
Single line
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".vtt", delete=False, encoding="utf-8"
    ) as f:
        f.write(vtt_content)
        vtt_path = Path(f.name)

    try:
        segments = parse_standard_vtt(vtt_path)
        assert len(segments) == 2
        assert "Line 1 Line 2 continues" in segments[0].text
        assert segments[0].start == 1.0
        assert segments[0].end == 4.0
    finally:
        vtt_path.unlink()


def test_parse_standard_vtt_with_cue_settings():
    """Test parsing VTT with cue settings (position, alignment)."""
    vtt_content = """WEBVTT

00:00:01.000 --> 00:00:03.000 position:50% align:middle
Hello with settings

00:00:04.000 --> 00:00:06.000 line:0 position:100%
Top right text
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".vtt", delete=False, encoding="utf-8"
    ) as f:
        f.write(vtt_content)
        vtt_path = Path(f.name)

    try:
        segments = parse_standard_vtt(vtt_path)
        assert len(segments) == 2
        assert segments[0].text == "Hello with settings"
        assert segments[1].text == "Top right text"
    finally:
        vtt_path.unlink()


def test_parse_standard_vtt_empty_cues():
    """Test parsing VTT with empty cues."""
    vtt_content = """WEBVTT

00:00:01.000 --> 00:00:02.000

00:00:03.000 --> 00:00:04.000
Valid text
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".vtt", delete=False, encoding="utf-8"
    ) as f:
        f.write(vtt_content)
        vtt_path = Path(f.name)

    try:
        segments = parse_standard_vtt(vtt_path)
        # Empty cues are skipped, only valid text is parsed
        assert len(segments) >= 1
        assert "Valid text" in segments[-1].text
    finally:
        vtt_path.unlink()


def test_parse_standard_vtt_unicode():
    """Test parsing VTT with unicode content."""
    vtt_content = """WEBVTT

00:00:01.000 --> 00:00:03.000
你好世界 🌍 مرحبا

00:00:04.000 --> 00:00:06.000
Привет мир
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".vtt", delete=False, encoding="utf-8"
    ) as f:
        f.write(vtt_content)
        vtt_path = Path(f.name)

    try:
        segments = parse_standard_vtt(vtt_path)
        assert len(segments) == 2
        assert "你好世界" in segments[0].text
        assert "Привет" in segments[1].text
    finally:
        vtt_path.unlink()


def test_parse_youtube_vtt_basic():
    """Test parsing YouTube VTT with word-level timestamps."""
    vtt_content = """WEBVTT

00:00:01.000 --> 00:00:03.000
Hello<00:00:01.500><c> world</c>

00:00:04.000 --> 00:00:06.000
Second<00:00:04.500><c> sentence.</c>
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".vtt", delete=False, encoding="utf-8"
    ) as f:
        f.write(vtt_content)
        vtt_path = Path(f.name)

    try:
        segments = parse_youtube_vtt(vtt_path)
        assert len(segments) >= 1
        # Should extract words with timestamps
        total_words = sum(len(seg.words) for seg in segments)
        assert total_words >= 2
    finally:
        vtt_path.unlink()


def test_parse_youtube_vtt_overlapping_cues():
    """Test parsing YouTube VTT with overlapping karaoke-style cues."""
    vtt_content = """WEBVTT

00:00:01.000 --> 00:00:04.000
Hello<00:00:02.000><c> world</c>

00:00:02.000 --> 00:00:05.000
Hello world<00:00:03.000><c> again.</c>
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".vtt", delete=False, encoding="utf-8"
    ) as f:
        f.write(vtt_content)
        vtt_path = Path(f.name)

    try:
        segments = parse_youtube_vtt(vtt_path)
        # Should deduplicate words from overlapping cues
        assert len(segments) >= 1
    finally:
        vtt_path.unlink()


def test_parse_vtt_auto_detect_standard():
    """Test auto-detection of standard VTT format."""
    vtt_content = """WEBVTT

00:00:01.000 --> 00:00:03.000
Standard VTT without word timestamps
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".vtt", delete=False, encoding="utf-8"
    ) as f:
        f.write(vtt_content)
        vtt_path = Path(f.name)

    try:
        segments = parse_vtt(vtt_path)
        assert len(segments) == 1
        assert segments[0].text == "Standard VTT without word timestamps"
        # Standard VTT has one word per segment
        assert len(segments[0].words) == 1
    finally:
        vtt_path.unlink()


def test_parse_vtt_auto_detect_youtube():
    """Test auto-detection of YouTube VTT format."""
    vtt_content = """WEBVTT

00:00:01.000 --> 00:00:03.000
Hello<00:00:01.500><c> world</c>
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".vtt", delete=False, encoding="utf-8"
    ) as f:
        f.write(vtt_content)
        vtt_path = Path(f.name)

    try:
        segments = parse_vtt(vtt_path)
        # Should detect as YouTube format and extract words
        assert len(segments) >= 1
        total_words = sum(len(seg.words) for seg in segments)
        assert total_words >= 2
    finally:
        vtt_path.unlink()


def test_parse_vtt_empty_file():
    """Test parsing empty VTT file."""
    vtt_content = "WEBVTT\n"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".vtt", delete=False, encoding="utf-8"
    ) as f:
        f.write(vtt_content)
        vtt_path = Path(f.name)

    try:
        segments = parse_standard_vtt(vtt_path)
        assert len(segments) == 0
    finally:
        vtt_path.unlink()


def test_parse_vtt_hour_timestamps():
    """Test parsing VTT with hour-level timestamps."""
    vtt_content = """WEBVTT

01:30:45.500 --> 01:30:50.000
Over one hour

00:10:00.000 --> 00:10:05.000
Ten minutes
"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".vtt", delete=False, encoding="utf-8"
    ) as f:
        f.write(vtt_content)
        vtt_path = Path(f.name)

    try:
        segments = parse_standard_vtt(vtt_path)
        assert len(segments) == 2
        assert segments[0].start == 5445.5  # 1:30:45.500
        assert segments[1].start == 600.0  # 00:10:00.000
    finally:
        vtt_path.unlink()
