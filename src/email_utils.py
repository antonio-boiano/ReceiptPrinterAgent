#!/usr/bin/env python3
"""Utility functions for email handling."""

import hashlib
import uuid
from typing import Any, List, Optional


# Common keys used in Arcade API responses that may contain list data
RESPONSE_LIST_KEYS = ["emails", "messages", "items", "data", "results", "databases"]


def extract_list_from_response(value: Any) -> List[Any]:
    """Extract a list from an Arcade API response value.
    
    The response value might be:
    - A list directly
    - A dict containing a list under common keys like 'emails', 'messages', etc.
    
    Args:
        value: The response.output.value from an Arcade API response
        
    Returns:
        A list extracted from the value, or empty list if not found
    """
    if value is None:
        return []
    
    # Handle case where value is already a list
    if isinstance(value, list):
        return value
    
    # Handle case where value is a dict containing a list
    if isinstance(value, dict):
        for key in RESPONSE_LIST_KEYS:
            if key in value and isinstance(value[key], list):
                return value[key]
        return []
    
    return []


def get_email_key(email: dict) -> str:
    """Generate a unique key for an email using available identifiers.
    
    Args:
        email: Dictionary containing email data
        
    Returns:
        A unique string key for the email
    """
    # Prefer official IDs
    if email.get("id"):
        return email["id"]
    if email.get("message_id"):
        return email["message_id"]
    
    # Fallback to hash of sender, subject, and date
    sender = email.get("sender", "")
    subject = email.get("subject", "")
    date = email.get("date", email.get("received_at", ""))
    
    composite = f"{sender}{subject}{date}"
    
    # If all fields are empty, generate a unique ID to avoid losing emails
    if not composite:
        return f"unknown_{uuid.uuid4().hex[:8]}"
    
    # Use hash to avoid issues with special characters
    return hashlib.sha256(composite.encode()).hexdigest()
