#!/usr/bin/env python3
"""Utility functions for email handling."""

import uuid
from typing import Optional


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
    
    # Fallback to combination of sender, subject, and date
    sender = email.get("sender", "")
    subject = email.get("subject", "")
    date = email.get("date", email.get("received_at", ""))
    
    composite_key = f"{sender}|{subject}|{date}"
    
    # If all fields are empty, generate a unique ID to avoid losing emails
    if composite_key == "||":
        return f"unknown_{uuid.uuid4().hex[:8]}"
    
    return composite_key
