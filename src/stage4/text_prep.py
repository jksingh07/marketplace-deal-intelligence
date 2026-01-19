"""
Text Preparation Module for Stage 4

Handles text normalization and sentence splitting while preserving
original text for evidence matching.
"""

import re
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class PreparedText:
    """Container for prepared text with original preserved."""
    original_title: str
    original_description: str
    combined_text: str  # title + description for full text search
    normalized_text: str  # lowercased for pattern matching
    sentences: List[str]  # sentence-split for evidence extraction


def normalize_text(title: str, description: str) -> PreparedText:
    """
    Normalize text for extraction while preserving original for evidence.
    
    Args:
        title: Listing title
        description: Listing description
        
    Returns:
        PreparedText with original, combined, normalized, and sentences
    """
    # Handle None/empty values
    title = (title or "").strip()
    description = (description or "").strip()
    
    # Combine title and description
    combined = f"{title}\n{description}" if title and description else title or description
    
    # Normalize whitespace but preserve original casing
    normalized_whitespace = re.sub(r'\s+', ' ', combined).strip()
    
    # Create lowercase version for pattern matching
    normalized_lower = normalized_whitespace.lower()
    
    # Split into sentences
    sentences = split_sentences(combined)
    
    return PreparedText(
        original_title=title,
        original_description=description,
        combined_text=combined,
        normalized_text=normalized_lower,
        sentences=sentences,
    )


def split_sentences(text: str) -> List[str]:
    """
    Split text into sentences for evidence extraction.
    
    Uses a simple but robust approach that handles common cases:
    - Period/question mark/exclamation followed by space and capital
    - Newlines as sentence boundaries
    - Bullet points and list items
    
    Args:
        text: Input text to split
        
    Returns:
        List of sentences (may include partial sentences)
    """
    if not text:
        return []
    
    # First, split on newlines
    lines = text.split('\n')
    
    sentences = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Split on sentence-ending punctuation followed by space
        # This pattern handles: "sentence. Next" but not "Mr. Smith" as well
        parts = re.split(r'(?<=[.!?])\s+(?=[A-Z])', line)
        
        for part in parts:
            part = part.strip()
            if part:
                sentences.append(part)
    
    return sentences


def find_evidence_span(
    pattern: str,
    text: str,
    sentences: List[str],
    window_size: int = 200
) -> Optional[str]:
    """
    Find the evidence span containing a pattern match.
    
    Prefers full sentence containing the match, falls back to
    a character window if no sentence boundary found.
    
    Args:
        pattern: Pattern to search for (case-insensitive)
        text: Full text to search in
        sentences: Pre-split sentences
        window_size: Character window size for fallback
        
    Returns:
        Evidence text span or None if not found
    """
    pattern_lower = pattern.lower()
    
    # First, try to find a sentence containing the pattern
    for sentence in sentences:
        if pattern_lower in sentence.lower():
            return sentence
    
    # Fallback: find in full text and extract window
    text_lower = text.lower()
    idx = text_lower.find(pattern_lower)
    
    if idx == -1:
        return None
    
    # Extract window around match
    start = max(0, idx - window_size // 2)
    end = min(len(text), idx + len(pattern) + window_size // 2)
    
    # Try to align to word boundaries
    while start > 0 and text[start - 1] not in ' \n\t':
        start -= 1
    while end < len(text) and text[end] not in ' \n\t':
        end += 1
    
    return text[start:end].strip()


def check_evidence_exists(evidence_text: str, original_text: str) -> bool:
    """
    Check if evidence text exists verbatim in original text.
    
    Case-insensitive check that handles minor whitespace differences.
    
    Args:
        evidence_text: Claimed evidence text
        original_text: Original listing text (title + description)
        
    Returns:
        True if evidence exists in original text
    """
    if not evidence_text or not original_text:
        return False
    
    # Normalize both for comparison
    evidence_normalized = re.sub(r'\s+', ' ', evidence_text.lower()).strip()
    original_normalized = re.sub(r'\s+', ' ', original_text.lower()).strip()
    
    return evidence_normalized in original_normalized


def extract_keyword_context(
    keyword: str,
    text: str,
    context_chars: int = 100
) -> Optional[str]:
    """
    Extract context around a keyword for evidence.
    
    Args:
        keyword: Keyword to find
        text: Text to search in
        context_chars: Characters to include before/after
        
    Returns:
        Context string or None if keyword not found
    """
    text_lower = text.lower()
    keyword_lower = keyword.lower()
    
    idx = text_lower.find(keyword_lower)
    if idx == -1:
        return None
    
    # Find the actual keyword with original casing
    start = max(0, idx - context_chars)
    end = min(len(text), idx + len(keyword) + context_chars)
    
    # Align to word boundaries
    while start > 0 and text[start - 1] not in ' \n\t.,!?;:':
        start -= 1
    while end < len(text) and text[end] not in ' \n\t.,!?;:':
        end += 1
    
    context = text[start:end].strip()
    
    # Clean up leading/trailing punctuation
    context = re.sub(r'^[.,!?;:\s]+', '', context)
    context = re.sub(r'[.,!?;:\s]+$', '', context)
    
    return context if context else None
