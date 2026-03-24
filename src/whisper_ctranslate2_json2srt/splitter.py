"""Intelligent segment splitting for long segments only."""

from dataclasses import dataclass

from .parsers.whisper_json_parser import Segment, Word


@dataclass
class SubSegment:
    """A sub-segment created by splitting a long segment."""
    start: float
    end: float
    text: str
    words: list[Word]
    
    @property
    def duration(self) -> float:
        return self.end - self.start
    
    @property
    def word_count(self) -> int:
        return len(self.words)


# Sentence-ending punctuation
END_PUNCT = {'.', '?', '!', '。', '？', '！'}
# Pause punctuation
PAUSE_PUNCT = {',', ';', '，', '；'}


def should_split_at_word(word: Word, current_word_count: int,
                         comma_threshold: int = 12) -> bool:
    """Determine if we should split after this word.
    
    Args:
        word: Current word
        current_word_count: Number of words in current sub-segment
        comma_threshold: Min words before splitting at comma
        
    Returns:
        True if should split
    """
    text = word.text
    
    # Always split at sentence-ending punctuation
    if any(text.endswith(p) for p in END_PUNCT):
        return True
    
    # Split at comma if sub-segment is long enough
    if any(p in text for p in PAUSE_PUNCT) and current_word_count >= comma_threshold:
        return True
    
    return False


def is_repetitive_filler(words: list[Word]) -> bool:
    """Check if words are repetitive fillers (e.g., 'that that that')."""
    if len(words) < 3:
        return False
    
    texts = [w.text.strip().lower() for w in words]
    # Check if all words are the same filler word
    fillers = {'that', 'the', 'a', 'um', 'uh', 'er'}
    unique_words = set(texts)
    
    if len(unique_words) == 1 and list(unique_words)[0] in fillers:
        return True
    
    return False


def split_long_segment(segment: Segment,
                       max_duration: float = 3600.0,
                       max_words: int = 12,
                       max_chars: int = 200,
                       comma_threshold: int = 12) -> list[SubSegment]:
    """Split a long segment into smaller sub-segments.
    
    Only splits if segment exceeds limits. Preserves short segments as-is.
    
    Args:
        segment: Original Whisper segment
        max_duration: Max duration in seconds (default 3600, rarely triggers)
        max_words: Max words per sub-segment (default 12)
        max_chars: Max characters per sub-segment (default 200)
        comma_threshold: Words before splitting at comma
        
    Returns:
        List of sub-segments (or single item if no splitting needed)
    """
    # Special case: repetitive fillers - keep as-is
    if is_repetitive_filler(segment.words):
        return [SubSegment(
            start=segment.start,
            end=segment.end,
            text=segment.text,
            words=segment.words
        )]
    
    # Check if splitting is needed (duration rarely triggers due to high default)
    char_count = len(segment.text)
    if (segment.duration <= max_duration and 
        segment.word_count <= max_words and 
        char_count <= max_chars):
        # Return as-is, no splitting needed
        return [SubSegment(
            start=segment.start,
            end=segment.end,
            text=segment.text,
            words=segment.words
        )]
    
    # Need to split this long segment
    sub_segments: list[SubSegment] = []
    current_words: list[Word] = []
    
    for i, word in enumerate(segment.words):
        # Check if adding this word would exceed limits
        test_words = current_words + [word]
        word_count = len(test_words)
        duration = word.end - (test_words[0].start if test_words else word.start)
        char_count = len(' '.join(w.text for w in test_words))
        
        should_split = False
        
        # Check duration limit
        if duration >= max_duration:
            should_split = True
        
        # Check word count limit
        if word_count >= max_words:
            should_split = True
        
        # Check character count limit
        if char_count >= max_chars:
            should_split = True
        
        # Check punctuation-based split
        if should_split_at_word(word, word_count, comma_threshold):
            should_split = True
        
        # Force split at last word
        if i == len(segment.words) - 1:
            should_split = True
        
        if should_split and test_words:
            sub_seg = SubSegment(
                start=test_words[0].start,
                end=word.end,
                text=' '.join(w.text for w in test_words),
                words=test_words
            )
            sub_segments.append(sub_seg)
            current_words = []
        else:
            current_words = test_words
    
    return sub_segments


def process_segments(segments: list[Segment],
                     max_duration: float = 3600.0,
                     max_words: int = 12,
                     max_chars: int = 200,
                     comma_threshold: int = 12) -> list[SubSegment]:
    """Process all segments, splitting only long ones.
    
    Args:
        segments: List of Whisper segments
        max_duration: Max duration in seconds (default 3600, rarely triggers)
        max_words: Max words per sub-segment (default 12)
        max_chars: Max characters per sub-segment (default 200)
        comma_threshold: Words before splitting at comma
        
    Returns:
        List of sub-segments (preserves short segments, splits long ones)
    """
    all_sub_segments: list[SubSegment] = []
    
    for segment in segments:
        sub_segments = split_long_segment(
            segment,
            max_duration=max_duration,
            max_words=max_words,
            max_chars=max_chars,
            comma_threshold=comma_threshold
        )
        all_sub_segments.extend(sub_segments)
    
    return all_sub_segments
