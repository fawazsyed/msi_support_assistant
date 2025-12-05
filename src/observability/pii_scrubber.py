"""
PII (Personally Identifiable Information) scrubbing utilities.

Removes or redacts sensitive information before logging or storing data.
Critical for compliance with privacy regulations (GDPR, HIPAA, etc.).
"""

import re
import logging
from typing import Dict, Any, List, Union

logger = logging.getLogger(__name__)

# Regex patterns for common PII
EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
PHONE_PATTERN = r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'
SSN_PATTERN = r'\b\d{3}-\d{2}-\d{4}\b'
CREDIT_CARD_PATTERN = r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
IP_ADDRESS_PATTERN = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
URL_PATTERN = r'https?://[^\s<>"{}|\\^`\[\]]+'

# Replacement tokens
REDACTED_EMAIL = '[EMAIL_REDACTED]'
REDACTED_PHONE = '[PHONE_REDACTED]'
REDACTED_SSN = '[SSN_REDACTED]'
REDACTED_CC = '[CC_REDACTED]'
REDACTED_IP = '[IP_REDACTED]'
REDACTED_URL = '[URL_REDACTED]'


def scrub_email(text: str) -> str:
    """
    Remove email addresses from text.
    
    Args:
        text: Input text potentially containing emails
        
    Returns:
        Text with emails redacted
    """
    return re.sub(EMAIL_PATTERN, REDACTED_EMAIL, text)


def scrub_phone(text: str) -> str:
    """
    Remove phone numbers from text.
    
    Args:
        text: Input text potentially containing phone numbers
        
    Returns:
        Text with phone numbers redacted
    """
    return re.sub(PHONE_PATTERN, REDACTED_PHONE, text)


def scrub_ssn(text: str) -> str:
    """
    Remove Social Security Numbers from text.
    
    Args:
        text: Input text potentially containing SSNs
        
    Returns:
        Text with SSNs redacted
    """
    return re.sub(SSN_PATTERN, REDACTED_SSN, text)


def scrub_credit_card(text: str) -> str:
    """
    Remove credit card numbers from text.
    
    Args:
        text: Input text potentially containing credit card numbers
        
    Returns:
        Text with credit card numbers redacted
    """
    return re.sub(CREDIT_CARD_PATTERN, REDACTED_CC, text)


def scrub_ip_address(text: str) -> str:
    """
    Remove IP addresses from text.
    
    Args:
        text: Input text potentially containing IP addresses
        
    Returns:
        Text with IP addresses redacted
    """
    return re.sub(IP_ADDRESS_PATTERN, REDACTED_IP, text)


def scrub_url(text: str, keep_domain: bool = False) -> str:
    """
    Remove or partially redact URLs from text.
    
    Args:
        text: Input text potentially containing URLs
        keep_domain: If True, keeps the domain but redacts the path
        
    Returns:
        Text with URLs redacted
    """
    if keep_domain:
        def replace_url(match):
            url = match.group(0)
            # Extract domain
            domain_match = re.match(r'(https?://[^/]+)', url)
            if domain_match:
                return domain_match.group(1) + '/[PATH_REDACTED]'
            return REDACTED_URL
        return re.sub(URL_PATTERN, replace_url, text)
    else:
        return re.sub(URL_PATTERN, REDACTED_URL, text)


def scrub_all_pii(
    text: str,
    scrub_emails: bool = True,
    scrub_phones: bool = True,
    scrub_ssns: bool = True,
    scrub_credit_cards: bool = True,
    scrub_ips: bool = False,
    scrub_urls: bool = False
) -> str:
    """
    Scrub all configured PII types from text.
    
    Args:
        text: Input text to scrub
        scrub_emails: Remove email addresses
        scrub_phones: Remove phone numbers
        scrub_ssns: Remove Social Security Numbers
        scrub_credit_cards: Remove credit card numbers
        scrub_ips: Remove IP addresses (default False - may be needed for debugging)
        scrub_urls: Remove URLs (default False - may break context)
        
    Returns:
        Text with all configured PII redacted
    """
    if not isinstance(text, str):
        logger.warning(f"scrub_all_pii called with non-string: {type(text)}")
        return str(text)
    
    result = text
    
    if scrub_emails:
        result = scrub_email(result)
    
    if scrub_phones:
        result = scrub_phone(result)
    
    if scrub_ssns:
        result = scrub_ssn(result)
    
    if scrub_credit_cards:
        result = scrub_credit_card(result)
    
    if scrub_ips:
        result = scrub_ip_address(result)
    
    if scrub_urls:
        result = scrub_url(result)
    
    return result


def scrub_dict(
    data: Dict[str, Any],
    scrub_emails: bool = True,
    scrub_phones: bool = True,
    scrub_ssns: bool = True,
    scrub_credit_cards: bool = True,
    scrub_ips: bool = False,
    scrub_urls: bool = False,
    fields_to_scrub: Union[List[str], None] = None
) -> Dict[str, Any]:
    """
    Recursively scrub PII from dictionary values.
    
    Args:
        data: Dictionary to scrub
        scrub_emails: Remove email addresses
        scrub_phones: Remove phone numbers
        scrub_ssns: Remove Social Security Numbers
        scrub_credit_cards: Remove credit card numbers
        scrub_ips: Remove IP addresses
        scrub_urls: Remove URLs
        fields_to_scrub: If provided, only scrub these specific fields.
                        If None, scrub all string values.
        
    Returns:
        Dictionary with PII redacted
    """
    scrubbed = {}
    
    for key, value in data.items():
        # Check if we should scrub this field
        should_scrub = (fields_to_scrub is None) or (key in fields_to_scrub)
        
        if isinstance(value, str) and should_scrub:
            scrubbed[key] = scrub_all_pii(
                value,
                scrub_emails=scrub_emails,
                scrub_phones=scrub_phones,
                scrub_ssns=scrub_ssns,
                scrub_credit_cards=scrub_credit_cards,
                scrub_ips=scrub_ips,
                scrub_urls=scrub_urls
            )
        elif isinstance(value, dict):
            scrubbed[key] = scrub_dict(
                value,
                scrub_emails=scrub_emails,
                scrub_phones=scrub_phones,
                scrub_ssns=scrub_ssns,
                scrub_credit_cards=scrub_credit_cards,
                scrub_ips=scrub_ips,
                scrub_urls=scrub_urls,
                fields_to_scrub=fields_to_scrub
            )
        elif isinstance(value, list):
            scrubbed[key] = [
                scrub_all_pii(item, scrub_emails, scrub_phones, scrub_ssns, 
                             scrub_credit_cards, scrub_ips, scrub_urls)
                if isinstance(item, str) and should_scrub
                else scrub_dict(item, scrub_emails, scrub_phones, scrub_ssns,
                               scrub_credit_cards, scrub_ips, scrub_urls, fields_to_scrub)
                if isinstance(item, dict)
                else item
                for item in value
            ]
        else:
            scrubbed[key] = value
    
    return scrubbed


# Default scrubbing configuration for observability data
OBSERVABILITY_PII_CONFIG = {
    "scrub_emails": True,
    "scrub_phones": True,
    "scrub_ssns": True,
    "scrub_credit_cards": True,
    "scrub_ips": False,  # May be useful for debugging
    "scrub_urls": False,  # URLs often needed for context
}


def scrub_observability_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scrub PII from observability data with default config for MSI Assistant.
    
    Args:
        data: Observability data dictionary
        
    Returns:
        Dictionary with PII redacted using default configuration
    """
    # Fields that commonly contain PII in our system
    sensitive_fields = [
        "user_input",
        "response",
        "retrieved_contexts",
        "reference",
        "content",
        "messages",
    ]
    
    return scrub_dict(
        data,
        **OBSERVABILITY_PII_CONFIG,
        fields_to_scrub=sensitive_fields
    )
