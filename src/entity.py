from dataclasses import dataclass

@dataclass
class NEREntity:
    """A dataclass to hold information about a named entity."""
    text: str
    label: str
    score: float
    start: int
    end: int
