"""Intelligent segment splitting for long segments only."""

from dataclasses import dataclass

from .parser import Segment, Word


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


def split_long_segment(segment: Segment,
                       max_duration: float = 10.0,
                       max_words: int = 15,
                       comma_threshold: int = 12) -> list[SubSegment]:
    """Split a long segment into smaller sub-segments.
    
    Only splits if segment exceeds limits. Preserves short segments as-is.
    
    Args:
        segment: Original Whisper segment
        max_duration: Max duration in seconds
        max_words: Max words per sub-segment
        comma_threshold: Words before splitting at comma
        
    Returns:
        List of sub-segments (or single item if no splitting needed)
    """
    # Check if splitting is needed
    if segment.duration <= max_duration and segment.word_count <= max_words:
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
        current_words.append(word)
        word_count = len(current_words)
        duration = word.end - (current_words[0].start if current_words else word.start)
        
        should_split = False
        
        # Check if adding this word would exceed limits
        if current_words and duration >= max_duration:
            # Split before this word
            sub_seg = SubSegment(
                start=current_words[0].start,
                end=current_words[-1].end,
                text=' '.join(w.text for w in current_words),
                words=current_words
            )
            sub_segments.append(sub_seg)
            current_words = [word]
            word_count = 1
        
        # Check punctuation-based split
        if should_split_at_word(word, word_count, comma_threshold):
            should_split = True
        
        # Check word count limit
        if word_count >= max_words:
            should_split = True
        
        # Force split at last word
        if i == len(segment.words) - 1:
            should_split = True
        
        if should_split and current_words:
            sub_seg = SubSegment(
                start=current_words[0].start,
                end=word.end,
                text=' '.join(w.text for w in current_words),
                words=current_words
            )
            sub_segments.append(sub_seg)
            current_words = []
    
    return sub_segments


def process_segments(segments: list[Segment],
                     max_duration: float = 10.0,
                     max_words: int = 15,
                     comma_threshold: int = 12) -> list[SubSegment]:
    """Process all segments, splitting only long ones.
    
    Args:
        segments: List of Whisper segments
        max_duration: Max duration in seconds
        max_words: Max words per sub-segment
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
            comma_threshold=comma_threshold
        )
        all_sub_segments.extend(sub_segments)
    
    return all_sub_segments
