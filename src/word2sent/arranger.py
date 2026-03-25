"""Arranger mode: Ignore Whisper segments, arrange words purely by word info."""

from dataclasses import dataclass

from .model import Word


@dataclass
class ArrangedSegment:
    """A segment created by arranging words."""
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


def should_break_at_word(word: Word, current_word_count: int,
                         comma_threshold: int = 12) -> bool:
    """Determine if we should break after this word."""
    text = word.text
    
    # Always break at sentence-ending punctuation
    if any(text.endswith(p) for p in END_PUNCT):
        return True
    
    # Break at comma if segment is long enough
    if any(p in text for p in PAUSE_PUNCT) and current_word_count >= comma_threshold:
        return True
    
    return False


def arrange_words(words: list[Word],
                  max_duration: float = 10.0,
                  max_words: int = 12,
                  max_chars: int = 200,
                  comma_threshold: int = 12) -> list[ArrangedSegment]:
    """Arrange all words into segments, ignoring original Whisper segmentation.
    
    Args:
        words: List of all words from Whisper (flattened from all segments)
        max_duration: Max duration in seconds
        max_words: Max words per segment
        max_chars: Max characters per segment
        comma_threshold: Words before breaking at comma
        
    Returns:
        List of arranged segments
    """
    segments: list[ArrangedSegment] = []
    current_words: list[Word] = []
    
    for i, word in enumerate(words):
        # Check if adding this word would exceed limits
        test_words = current_words + [word]
        word_count = len(test_words)
        duration = word.end - (test_words[0].start if test_words else word.start)
        char_count = len(' '.join(w.text for w in test_words))
        
        should_break = False
        
        # Check duration limit
        if duration >= max_duration:
            should_break = True
        
        # Check word count limit
        if word_count >= max_words:
            should_break = True
        
        # Check character count limit
        if char_count >= max_chars:
            should_break = True
        
        # Check punctuation-based split
        if should_break_at_word(word, word_count, comma_threshold):
            should_break = True
        
        # Force break at last word
        if i == len(words) - 1:
            should_break = True
        
        if should_break and test_words:
            seg = ArrangedSegment(
                start=test_words[0].start,
                end=word.end,
                text=' '.join(w.text for w in test_words),
                words=test_words
            )
            segments.append(seg)
            current_words = []
        else:
            current_words = test_words
    
    return segments
