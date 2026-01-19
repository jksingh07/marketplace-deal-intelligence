"""
Input Validation Module

Validates and sanitizes input data before processing.
Prevents DoS attacks and ensures data quality.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ValidationConfig:
    """Configuration for input validation."""
    max_title_length: int = 500
    max_description_length: int = 10_000
    max_listing_id_length: int = 100
    min_description_length: int = 10
    required_fields: List[str] = None
    
    def __post_init__(self):
        if self.required_fields is None:
            self.required_fields = ["listing_id", "title", "description"]


@dataclass
class ValidationResult:
    """Result of input validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    sanitized_input: Optional[Dict[str, Any]] = None


class InputValidator:
    """
    Validates listing input before pipeline processing.
    """
    
    def __init__(self, config: Optional[ValidationConfig] = None):
        self.config = config or ValidationConfig()
    
    def validate(self, listing: Dict[str, Any]) -> ValidationResult:
        """
        Validate a listing input.
        
        Args:
            listing: Raw listing dictionary
            
        Returns:
            ValidationResult with errors, warnings, and sanitized input
        """
        errors = []
        warnings = []
        
        # Check for required fields
        for field in self.config.required_fields:
            if field not in listing or listing[field] is None:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
            )
        
        # Validate listing_id
        listing_id = str(listing.get("listing_id", ""))
        if len(listing_id) > self.config.max_listing_id_length:
            errors.append(
                f"listing_id too long: {len(listing_id)} > {self.config.max_listing_id_length}"
            )
        
        # Validate title
        title = str(listing.get("title", ""))
        if len(title) > self.config.max_title_length:
            warnings.append(
                f"Title truncated: {len(title)} > {self.config.max_title_length}"
            )
            title = title[:self.config.max_title_length]
        
        # Validate description
        description = str(listing.get("description", ""))
        if len(description) > self.config.max_description_length:
            warnings.append(
                f"Description truncated: {len(description)} > {self.config.max_description_length}"
            )
            description = description[:self.config.max_description_length]
        
        if len(description) < self.config.min_description_length:
            warnings.append(
                f"Description very short: {len(description)} chars"
            )
        
        # Check for suspicious content
        suspicious = self._check_suspicious_content(title + " " + description)
        if suspicious:
            warnings.extend(suspicious)
        
        # Create sanitized input
        sanitized = self._sanitize_listing(listing, title, description)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_input=sanitized,
        )
    
    def _check_suspicious_content(self, text: str) -> List[str]:
        """Check for suspicious or malicious content."""
        warnings = []
        
        # Check for excessive special characters
        special_ratio = len(re.findall(r'[^\w\s]', text)) / max(len(text), 1)
        if special_ratio > 0.3:
            warnings.append("High ratio of special characters detected")
        
        # Check for potential injection patterns
        injection_patterns = [
            r'<script',
            r'javascript:',
            r'data:text/html',
            r'onerror\s*=',
            r'onclick\s*=',
        ]
        for pattern in injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                warnings.append(f"Potential injection pattern detected: {pattern}")
        
        # Check for excessive repetition
        words = text.lower().split()
        if len(words) > 10:
            unique_words = set(words)
            if len(unique_words) / len(words) < 0.3:
                warnings.append("Excessive word repetition detected")
        
        return warnings
    
    def _sanitize_listing(
        self,
        listing: Dict[str, Any],
        title: str,
        description: str,
    ) -> Dict[str, Any]:
        """Create a sanitized copy of the listing."""
        sanitized = {
            "listing_id": str(listing.get("listing_id", "")),
            "title": self._sanitize_text(title),
            "description": self._sanitize_text(description),
        }
        
        # Copy optional fields
        if "vehicle_type" in listing:
            vehicle_type = str(listing["vehicle_type"])
            if vehicle_type in ["car", "bike", "unknown"]:
                sanitized["vehicle_type"] = vehicle_type
            else:
                sanitized["vehicle_type"] = "unknown"
        
        if "price" in listing and listing["price"] is not None:
            try:
                sanitized["price"] = float(listing["price"])
            except (ValueError, TypeError):
                pass
        
        if "mileage" in listing and listing["mileage"] is not None:
            try:
                sanitized["mileage"] = int(listing["mileage"])
            except (ValueError, TypeError):
                pass
        
        return sanitized
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize text content."""
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters (except newlines)
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        
        return text.strip()


# Global validator instance
_validator: Optional[InputValidator] = None


def get_validator() -> InputValidator:
    """Get the global input validator."""
    global _validator
    if _validator is None:
        _validator = InputValidator()
    return _validator


def validate_listing(listing: Dict[str, Any]) -> ValidationResult:
    """Validate a listing using the global validator."""
    return get_validator().validate(listing)


def validate_and_sanitize(listing: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate and return sanitized listing or raise on error.
    
    Args:
        listing: Raw listing dictionary
        
    Returns:
        Tuple of (sanitized_listing, warnings)
        
    Raises:
        ValueError: If validation fails
    """
    result = validate_listing(listing)
    
    if not result.is_valid:
        raise ValueError(f"Validation failed: {', '.join(result.errors)}")
    
    return result.sanitized_input, result.warnings
