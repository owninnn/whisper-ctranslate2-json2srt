"""Shared data models for segments and words."""

from dataclasses import dataclass, field


@dataclass
class Word:
    """A single word with timing."""
    start: float  # seconds
    end: float    # seconds
    text: str
    
    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class Segment:
    """A segment containing words with timing."""
    id: int
    start: float
    end: float
    text: str
    words: list[Word] = field(default_factory=list)
    
    @property
    def duration(self) -> float:
        return self.end - self.start
    
    @property
    def word_count(self) -> int:
        return len(self.words)
