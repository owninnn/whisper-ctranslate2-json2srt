"""Parse YouTube VTT format to extract word-level timestamps."""

import re
from pathlib import Path

# Import from whisper_json_parser to ensure compatibility
from .whisper_json_parser import Word, Segment


def parse_time(time_str: str) -> float:
    """Parse time string to seconds."""
    parts = time_str.strip().split(':')
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    else:
        return float(parts[0])


def parse_youtube_vtt(vtt_path: Path) -> list[Segment]:
    """Parse YouTube VTT file to extract word-level timestamps.
    
    YouTube VTT format has overlapping cues for karaoke-style display.
    Each cue shows progressively more words of the same sentence.
    
    Returns:
        List of Segment objects with words (compatible with main parser)
    """
    with open(vtt_path, encoding='utf-8') as f:
        content = f.read()
    
    raw_words = []
    
    # Pattern to match cue timing line and content
    cue_pattern = r'(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})[^\n]*\n(.*?)(?=\n\n|\Z)'
    
    for match in re.finditer(cue_pattern, content, re.DOTALL):
        cue_start_str, cue_end_str, cue_text = match.groups()
        cue_start = parse_time(cue_start_str)
        cue_end = parse_time(cue_end_str)
        cue_text = cue_text.replace('\n', ' ').strip()
        
        if not cue_text:
            continue
        
        # Check if this cue has word-level timestamps (YouTube style)
        if '<c>' in cue_text or re.search(r'<\d{2}:\d{2}:\d{2}\.\d{3}>', cue_text):
            # Parse word-level timestamps
            # Format: word<00:00:03.310><c> next_word</c>
            
            # First, get the initial word(s) before first timestamp
            initial_match = re.match(r'^([^<]+)', cue_text)
            if initial_match:
                initial_text = initial_match.group(1).strip()
                if initial_text:
                    first_ts_match = re.search(r'<(\d{2}:\d{2}:\d{2}\.\d{3})>', cue_text)
                    if first_ts_match:
                        first_end = parse_time(first_ts_match.group(1))
                    else:
                        first_end = cue_end
                    
                    initial_words = initial_text.split()
                    if initial_words:
                        word_duration = (first_end - cue_start) / len(initial_words)
                        for i, w in enumerate(initial_words):
                            w_start = cue_start + i * word_duration
                            w_end = cue_start + (i + 1) * word_duration
                            raw_words.append(Word(start=w_start, end=w_end, text=w))
            
            # Extract all <timestamp><c>word</c> patterns
            word_ts_pattern = r'<(\d{2}:\d{2}:\d{2}\.\d{3})><c>\s*([^<]+)</c>'
            for word_match in re.finditer(word_ts_pattern, cue_text):
                start_str, text = word_match.groups()
                text = text.strip()
                if text:
                    word_start = parse_time(start_str)
                    # Estimate end time (will be adjusted later)
                    word_end = word_start + 0.5
                    raw_words.append(Word(start=word_start, end=word_end, text=text))
    
    # Deduplicate and sort
    single_words = [w for w in raw_words if len(w.text.split()) == 1]
    single_words.sort(key=lambda w: w.start)
    
    # Remove duplicates (3s window)
    unique_words = []
    last_seen = {}
    for word in single_words:
        text_lower = word.text.lower()
        if text_lower in last_seen:
            if abs(word.start - last_seen[text_lower]) < 3.0:
                continue
        unique_words.append(word)
        last_seen[text_lower] = word.start
    
    # Fix end times (next word's start time)
    for i in range(len(unique_words) - 1):
        unique_words[i].end = unique_words[i + 1].start
    
    # Create segments from words
    # For VTT, we create one segment per sentence (based on punctuation)
    return _words_to_segments(unique_words)


def _words_to_segments(words: list[Word]) -> list[Segment]:
    """Convert flat word list to segments (for splitter mode compatibility)."""
    if not words:
        return []
    
    segments = []
    current_words = []
    seg_id = 0
    
    END_PUNCT = {'.', '?', '!', '。', '？', '！'}
    
    for word in words:
        current_words.append(word)
        
        # Check if word ends with sentence punctuation
        if any(word.text.endswith(p) for p in END_PUNCT):
            # Create segment
            text = ' '.join(w.text for w in current_words)
            segment = Segment(
                id=seg_id,
                start=current_words[0].start,
                end=current_words[-1].end,
                text=text,
                words=current_words
            )
            segments.append(segment)
            current_words = []
            seg_id += 1
    
    # Add remaining words as last segment
    if current_words:
        text = ' '.join(w.text for w in current_words)
        segment = Segment(
            id=seg_id,
            start=current_words[0].start,
            end=current_words[-1].end,
            text=text,
            words=current_words
        )
        segments.append(segment)
    
    return segments


def parse_standard_vtt(vtt_path: Path) -> list[Segment]:
    """Parse standard WebVTT without word-level timestamps."""
    with open(vtt_path, encoding='utf-8') as f:
        content = f.read()
    
    segments = []
    seg_id = 0
    
    cue_pattern = r'(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})[^\n]*\n(.*?)(?=\n\n|\Z)'
    
    for match in re.finditer(cue_pattern, content, re.DOTALL):
        cue_start_str, cue_end_str, cue_text = match.groups()
        cue_start = parse_time(cue_start_str)
        cue_end = parse_time(cue_end_str)
        cue_text = cue_text.replace('\n', ' ').strip()
        
        if cue_text:
            # For standard VTT, create one word containing the full text
            word = Word(start=cue_start, end=cue_end, text=cue_text)
            segment = Segment(
                id=seg_id,
                start=cue_start,
                end=cue_end,
                text=cue_text,
                words=[word]
            )
            segments.append(segment)
            seg_id += 1
    
    return segments


def parse_vtt(vtt_path: Path) -> list[Segment]:
    """Parse VTT file (auto-detect format)."""
    with open(vtt_path, encoding='utf-8') as f:
        content = f.read()
    
    # Check if it's YouTube style (has <c> tags with timestamps)
    if '<c>' in content and re.search(r'<\d{2}:\d{2}:\d{2}\.\d{3}>', content):
        return parse_youtube_vtt(vtt_path)
    else:
        return parse_standard_vtt(vtt_path)
