"""
Unit tests for validator utilities.

Tests email, password, phone, username, and other validation functions.
"""
import pytest
from tuned.utils.validators import (
    validate_email,
    validate_password_strength,
    validate_phone_number,
    validate_username,
    validate_url,
    validate_integer,
    sanitize_string
)


class TestEmailValidation:
    """Tests for email validation."""
    
    @pytest.mark.parametrize('email', [
        'test@example.com',
        'user.name@example.com',
        'user+tag@example.co.uk',
        'user_name@example-domain.com',
        'test123@test.org',
    ])
    def test_valid_emails(self, email):
        """Test that valid emails are accepted."""
        assert validate_email(email) is True
    
    @pytest.mark.parametrize('email', [
        'invalid',
        'invalid@',
        '@example.com',
        'invalid@.com',
        'invalid..email@example.com',
        'invalid@example',
        '',
        None,
        'user name@example.com',  # Space in email
        'user@exam ple.com',  # Space in domain
    ])
    def test_invalid_emails(self, email):
        """Test that invalid emails are rejected."""
        assert validate_email(email) is False
    
    def test_email_max_length(self):
        """Test email length validation (RFC 5321)."""
        # Email longer than 320 chars should fail
        long_email = 'a' * 310 + '@example.com'
        assert validate_email(long_email) is False


class TestPasswordStrength:
    """Tests for password strength validation."""
    
    def test_valid_password(self):
        """Test that a strong password is accepted."""
        is_valid, error = validate_password_strength('SecurePass123!')
        
        assert is_valid is True
        assert error is None
    
    def test_password_too_short(self):
        """Test that passwords under 8 characters are rejected."""
        is_valid, error = validate_password_strength('Short1!')
        
        assert is_valid is False
        assert 'at least 8 characters' in error
    
    def test_password_too_long(self):
        """Test that passwords over 128 characters are rejected."""
        long_password = 'A1!' + 'a' * 130
        is_valid, error = validate_password_strength(long_password)
        
        assert is_valid is False
        assert 'must not exceed 128 characters' in error
    
    def test_password_missing_uppercase(self):
        """Test that password without uppercase is rejected."""
        is_valid, error = validate_password_strength('lowercase123!')
        
        assert is_valid is False
        assert 'uppercase' in error.lower()
    
    def test_password_missing_lowercase(self):
        """Test that password without lowercase is rejected."""
        is_valid, error = validate_password_strength('UPPERCASE123!')
        
        assert is_valid is False
        assert 'lowercase' in error.lower()
    
    def test_password_missing_digit(self):
        """Test that password without digit is rejected."""
        is_valid, error = validate_password_strength('NoDigitsHere!')
        
        assert is_valid is False
        assert 'digit' in error.lower()
    
    def test_password_missing_special_char(self):
        """Test that password without special character is rejected."""
        is_valid, error = validate_password_strength('NoSpecial123')
        
        assert is_valid is False
        assert 'special character' in error.lower()
    
    
    # Note: Common password checking is not implemented yet
    # This test is skipped for now
    # def test_common_password_rejected(self):
    #     """Test that common passwords are rejected."""
    #     is_valid, error = validate_password_strength('Password123!')
    #     assert is_valid is False
    #     assert 'too common' in error.lower()


class TestPhoneNumberValidation:
    """Tests for phone number validation."""
    
    @pytest.mark.parametrize('phone', [
        '+1234567890',
        '+12345678901234',
        '+44 (123) 456-7890',
        '+1-234-567-8900',
    ])
    def test_valid_phone_numbers(self, phone):
        """Test that valid phone numbers are accepted."""
        assert validate_phone_number(phone) is True
    
    @pytest.mark.parametrize('phone', [
        '1234567890',  # Missing +
        '+123',  # Too short
        '+12345678901234567',  # Too long
        'invalid',
        '',
        None,
    ])
    def test_invalid_phone_numbers(self, phone):
        """Test that invalid phone numbers are rejected."""
        assert validate_phone_number(phone) is False


class TestUsernameValidation:
    """Tests for username validation."""
    
    @pytest.mark.parametrize('username', [
        'user123',
        'test_user',
        'user-name',
        'testuser',
        'a1b',  # Minimum 3 chars
    ])
    def test_valid_usernames(self, username):
        """Test that valid usernames are accepted."""
        is_valid, error = validate_username(username)
        
        assert is_valid is True
        assert error is None
    
    def test_username_too_short(self):
        """Test that usernames under 3 characters are rejected."""
        is_valid, error = validate_username('ab')
        
        assert is_valid is False
        assert 'at least 3 characters' in error
    
    def test_username_too_long(self):
        """Test that usernames over 64 characters are rejected."""
        long_username = 'a' * 65
        is_valid, error = validate_username(long_username)
        
        assert is_valid is False
        assert 'must not exceed 64 characters' in error
    
    def test_username_invalid_characters(self):
        """Test that usernames with special characters are rejected."""
        is_valid, error = validate_username('user@name')
        
        assert is_valid is False
        assert 'letters, numbers, underscores, and hyphens' in error
    
    def test_username_cannot_start_with_special(self):
        """Test that usernames cannot start with underscore/hyphen."""
        is_valid, error = validate_username('_username')
        
        assert is_valid is False
    
    def test_reserved_usernames(self):
        """Test that reserved usernames are rejected."""
        is_valid, error = validate_username('admin')
        
        assert is_valid is False
        assert 'reserved' in error.lower()


class TestURLValidation:
    """Tests for URL validation."""
    
    @pytest.mark.parametrize('url', [
        'https://example.com',
        'http://www.example.com',
        'https://example.com/path/to/page',
        'https://example.com?query=param',
        'https://sub.example.co.uk',
    ])
    def test_valid_urls(self, url):
        """Test that valid URLs are accepted."""
        assert validate_url(url) is True
    
    @pytest.mark.parametrize('url', [
        'not a url',
        'ftp://example.com',  # Not http(s)
        'example.com',  # Missing protocol
        '',
        None,
    ])
    def test_invalid_urls(self, url):
        """Test that invalid URLs are rejected."""
        assert validate_url(url) is False


class TestIntegerValidation:
    """Tests for integer validation."""
    
    def test_valid_integer(self):
        """Test that valid integers are accepted."""
        is_valid, error = validate_integer(42)
        
        assert is_valid is True
        assert error is None
    
    def test_integer_string(self):
        """Test that integer strings are accepted."""
        is_valid, error = validate_integer('123')
        
        assert is_valid is True
        assert error is None
    
    def test_invalid_integer(self):
        """Test that non-integers are rejected."""
        is_valid, error = validate_integer('not a number')
        
        assert is_valid is False
        assert 'valid integer' in error
    
    def test_integer_min_value(self):
        """Test integer minimum value validation."""
        is_valid, error = validate_integer(5, min_value=10)
        
        assert is_valid is False
        assert 'at least 10' in error
    
    def test_integer_max_value(self):
        """Test integer maximum value validation."""
        is_valid, error = validate_integer(100, max_value=50)
        
        assert is_valid is False
        assert 'must not exceed 50' in error
    
    def test_integer_range(self):
        """Test integer range validation."""
        is_valid, error = validate_integer(25, min_value=10, max_value=50)
        
        assert is_valid is True
        assert error is None


class TestSanitizeString:
    """Tests for string sanitization."""
    
    def test_sanitize_normal_string(self):
        """Test sanitization of normal string."""
        result = sanitize_string('Normal text')
        
        assert result == 'Normal text'
    
    def test_sanitize_html_tags(self):
        """Test that HTML tags are escaped."""
        result = sanitize_string('<script>alert("XSS")</script>')
        
        assert '<script>' not in result
        assert '&lt;script&gt;' in result
    
    def test_sanitize_special_chars(self):
        """Test that special characters are escaped."""
        result = sanitize_string('Text with & symbols < >')
        
        assert '&amp;' in result
        assert '&lt;' in result
        assert '&gt;' in result
    
    def test_sanitize_with_max_length(self):
        """Test string truncation."""
        long_text = 'A' * 100
        result = sanitize_string(long_text, max_length=50)
        
        assert len(result) == 50
    
    def test_sanitize_strips_whitespace(self):
        """Test that leading/trailing whitespace is removed."""
        result = sanitize_string('  text with spaces  ')
        
        assert result == 'text with spaces'
    
    def test_sanitize_empty_string(self):
        """Test sanitization of empty string."""
        result = sanitize_string('')
        
        assert result == ''
    
    def test_sanitize_none(self):
        """Test sanitization of None."""
        result = sanitize_string(None)
        
        assert result == ''
