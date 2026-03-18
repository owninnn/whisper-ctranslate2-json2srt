"""Intelligent sentence segmentation."""

import re
from dataclasses import dataclass

from .parser import Word


@dataclass
class Sentence:
    """A sentence with timing."""
    start: float
    end: float
    words: list[Word]
    
    @property
    def text(self) -> str:
        return " ".join(w.text for w in self.words)
    
    @property
    def duration(self) -> float:
        return self.end - self.start
    
    @property
    def word_count(self) -> int:
        return len(self.words)


# Sentence-ending punctuation
END_PUNCT = {'.', '?', '!', '。', '？', '！'}
# Pause punctuation (comma, etc.)
PAUSE_PUNCT = {',', ';', '，', '；'}


def should_break_at_word(word: Word, word_count: int, 
                         comma_threshold: int = 12) -> bool:
    """Determine if we should break after this word.
    
    Args:
        word: Current word
        word_count: Number of words in current sentence
        comma_threshold: Min words before breaking at comma
        
    Returns:
        True if should break
    """
    text = word.text
    
    # Always break at sentence-ending punctuation
    if any(text.endswith(p) for p in END_PUNCT):
        return True
    
    # Break at comma if sentence is long enough
    if any(p in text for p in PAUSE_PUNCT) and word_count >= comma_threshold:
        return True
    
    return False


def segment_words(words: list[Word], 
                  max_duration: float = 10.0,
                  max_words: int = 15,
                  comma_threshold: int = 12) -> list[Sentence]:
    """Segment words into sentences intelligently.
    
    Args:
        words: List of words from Whisper
        max_duration: Max sentence duration in seconds
        max_words: Max words per sentence
        comma_threshold: Min words before breaking at comma
        
    Returns:
        List of Sentence objects
    """
    sentences: list[Sentence] = []
    current_words: list[Word] = []
    
    for i, word in enumerate(words):
        # Check if adding this word would exceed limits
        word_count = len(current_words) + 1
        duration = word.end - (current_words[0].start if current_words else word.start)
        
        should_break = False
        
        # Check duration limit BEFORE adding word
        if current_words and duration >= max_duration:
            # Break before this word
            sentence = Sentence(
                start=current_words[0].start,
                end=current_words[-1].end,
                words=current_words
            )
            sentences.append(sentence)
            current_words = []
            word_count = 1
        
        current_words.append(word)
        
        # Check punctuation-based break
        if should_break_at_word(word, word_count, comma_threshold):
            should_break = True
        
        # Check word count limit
        if word_count >= max_words:
            should_break = True
        
        # Force break at last word
        if i == len(words) - 1:
            should_break = True
        
        if should_break and current_words:
            sentence = Sentence(
                start=current_words[0].start,
                end=word.end,
                words=current_words
            )
            sentences.append(sentence)
            current_words = []
    
    return sentences
