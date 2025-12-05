"""
Unit tests for PII scrubber.

Tests PII detection and redaction for various sensitive data types.
"""

import re
import pytest
from src.observability.pii_scrubber import (
    scrub_email,
    scrub_phone,
    scrub_ssn,
    scrub_credit_card,
    scrub_ip_address,
    scrub_url,
    scrub_all_pii,
    scrub_dict,
    scrub_observability_data,
    REDACTED_EMAIL,
    REDACTED_PHONE,
    REDACTED_SSN,
    REDACTED_CC,
    REDACTED_IP,
    REDACTED_URL,
)


class TestPIIScrubber:
    """Test suite for PII scrubbing utilities"""
    
    def test_scrub_email(self):
        """Test email address redaction"""
        text = "Contact me at john.doe@example.com for more info"
        result = scrub_email(text)
        
        assert "john.doe@example.com" not in result
        assert REDACTED_EMAIL in result
        assert result == f"Contact me at {REDACTED_EMAIL} for more info"
    
    def test_scrub_multiple_emails(self):
        """Test redacting multiple email addresses"""
        text = "Email alice@example.com or bob@test.org"
        result = scrub_email(text)
        
        assert "alice@example.com" not in result
        assert "bob@test.org" not in result
        assert result.count(REDACTED_EMAIL) == 2
    
    def test_scrub_phone_various_formats(self):
        """Test phone number redaction in various formats"""
        test_cases = [
            "Call 555-123-4567",
            "Call (555) 123-4567",
            "Call 5551234567",
            "Call +1-555-123-4567",
        ]
        
        for text in test_cases:
            result = scrub_phone(text)
            assert REDACTED_PHONE in result
            # Ensure no digits remain in typical phone pattern
            assert not re.search(r'\d{3}.*\d{3}.*\d{4}', result)
    
    def test_scrub_ssn(self):
        """Test Social Security Number redaction"""
        text = "SSN: 123-45-6789"
        result = scrub_ssn(text)
        
        assert "123-45-6789" not in result
        assert REDACTED_SSN in result
    
    def test_scrub_credit_card(self):
        """Test credit card number redaction"""
        test_cases = [
            "Card: 1234-5678-9012-3456",
            "Card: 1234 5678 9012 3456",
            "Card: 1234567890123456",
        ]
        
        for text in test_cases:
            result = scrub_credit_card(text)
            assert REDACTED_CC in result
            # Ensure pattern doesn't remain
            assert not re.search(r'\d{13,16}', result.replace(" ", "").replace("-", ""))
    
    def test_scrub_ip_address(self):
        """Test IP address redaction"""
        text = "Server IP: 192.168.1.1"
        result = scrub_ip_address(text)
        
        assert "192.168.1.1" not in result
        assert REDACTED_IP in result
    
    def test_scrub_url_full(self):
        """Test full URL redaction"""
        text = "Visit https://example.com/secret/path for details"
        result = scrub_url(text, keep_domain=False)
        
        assert "example.com" not in result
        assert REDACTED_URL in result
    
    def test_scrub_url_keep_domain(self):
        """Test URL redaction keeping domain"""
        text = "Visit https://example.com/secret/path for details"
        result = scrub_url(text, keep_domain=True)
        
        assert "example.com" in result
        assert "/secret/path" not in result
        assert "[PATH_REDACTED]" in result
    
    def test_scrub_all_pii_default(self):
        """Test scrubbing all PII with default settings"""
        text = (
            "Contact john@example.com at 555-123-4567. "
            "SSN: 123-45-6789, Card: 1234-5678-9012-3456"
        )
        result = scrub_all_pii(text)
        
        assert "john@example.com" not in result
        assert "555-123-4567" not in result
        assert "123-45-6789" not in result
        assert "1234-5678-9012-3456" not in result
        
        assert REDACTED_EMAIL in result
        assert REDACTED_PHONE in result
        assert REDACTED_SSN in result
        assert REDACTED_CC in result
    
    def test_scrub_all_pii_selective(self):
        """Test scrubbing only selected PII types"""
        text = "Email: john@example.com, Phone: 555-123-4567"
        
        # Only scrub emails
        result = scrub_all_pii(
            text,
            scrub_emails=True,
            scrub_phones=False,
            scrub_ssns=False,
            scrub_credit_cards=False
        )
        
        assert "john@example.com" not in result
        assert "555-123-4567" in result  # Phone not scrubbed
        assert REDACTED_EMAIL in result
    
    def test_scrub_dict_simple(self):
        """Test scrubbing dictionary values"""
        data = {
            "user_input": "Contact me at john@example.com",
            "response": "Call 555-123-4567",
            "metadata": {"timestamp": "2024-01-01"}
        }
        
        result = scrub_dict(data)
        
        assert "john@example.com" not in result["user_input"]
        assert "555-123-4567" not in result["response"]
        assert REDACTED_EMAIL in result["user_input"]
        assert REDACTED_PHONE in result["response"]
        assert result["metadata"]["timestamp"] == "2024-01-01"  # Non-string unchanged
    
    def test_scrub_dict_nested(self):
        """Test scrubbing nested dictionary"""
        data = {
            "level1": {
                "level2": {
                    "email": "test@example.com"
                }
            }
        }
        
        result = scrub_dict(data)
        
        assert "test@example.com" not in str(result)
        assert REDACTED_EMAIL in result["level1"]["level2"]["email"]
    
    def test_scrub_dict_with_list(self):
        """Test scrubbing dictionary containing lists"""
        data = {
            "messages": [
                "Email me at alice@test.com",
                "Or call 555-123-4567"
            ]
        }
        
        result = scrub_dict(data)
        
        assert "alice@test.com" not in str(result)
        assert "555-123-4567" not in str(result)
        assert REDACTED_EMAIL in result["messages"][0]
        assert REDACTED_PHONE in result["messages"][1]
    
    def test_scrub_dict_specific_fields(self):
        """Test scrubbing only specific fields"""
        data = {
            "sensitive": "Email: john@example.com",
            "public": "Email: alice@example.com"
        }
        
        result = scrub_dict(data, fields_to_scrub=["sensitive"])
        
        assert "john@example.com" not in result["sensitive"]
        assert "alice@example.com" in result["public"]  # Not scrubbed
    
    def test_scrub_observability_data(self):
        """Test scrubbing typical observability data structure"""
        data = {
            "user_input": "My email is john@example.com",
            "response": "Call me at 555-123-4567",
            "retrieved_contexts": [
                "User contact: alice@test.com"
            ],
            "metadata": {
                "timestamp": "2024-01-01",
                "model": "gpt-4"
            }
        }
        
        result = scrub_observability_data(data)
        
        # Sensitive fields should be scrubbed
        assert "john@example.com" not in result["user_input"]
        assert "555-123-4567" not in result["response"]
        assert "alice@test.com" not in str(result["retrieved_contexts"])
        
        # Metadata should be unchanged
        assert result["metadata"]["timestamp"] == "2024-01-01"
        assert result["metadata"]["model"] == "gpt-4"
    
    def test_scrub_non_string_input(self):
        """Test that non-string inputs are handled gracefully"""
        result = scrub_all_pii(12345)
        assert result == "12345"  # Converted to string
        
        result = scrub_all_pii(None)
        assert result == "None"
