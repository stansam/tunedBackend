"""
Unit tests for password utilities.

Tests password hashing, verification, and strength checking with bcrypt.
"""
import pytest
from tuned.utils.auth.password import (
    hash_password,
    verify_password,
    check_password_strength,
    generate_temporary_password
)


class TestPasswordHashing:
    """Tests for password hashing with bcrypt."""
    
    def test_hash_password(self):
        """Test that password hashing works."""
        password = 'TestPassword123!'
        hashed = hash_password(password)
        
        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != password
        assert hashed.startswith('$2b$')  # Bcrypt format
    
    def test_hash_password_generates_different_hashes(self):
        """Test that same password generates different hashes (salt)."""
        password = 'SamePassword123!'
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2  # Different salts
    
    def test_verify_correct_password(self):
        """Test that correct password verification works."""
        password = 'CorrectPassword123!'
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_incorrect_password(self):
        """Test that incorrect password is rejected."""
        password = 'CorrectPassword123!'
        wrong_password = 'WrongPassword123!'
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_password_case_sensitive(self):
        """Test that password verification is case-sensitive."""
        password = 'CaseSensitive123!'
        hashed = hash_password(password)
        
        assert verify_password('casesensitive123!', hashed) is False
    
    def test_verify_password_with_invalid_hash(self):
        """Test that invalid hash returns False."""
        assert verify_password('test', 'invalid_hash') is False
    
    def test_verify_password_with_empty_password(self):
        """Test that empty password returns False."""
        hashed = hash_password('TestPassword123!')
        
        assert verify_password('', hashed) is False


class TestPasswordStrength:
    """Tests for password strength checking."""
    
    def test_strong_password(self):
        """Test that strong password passes."""
        is_valid, error = check_password_strength('StrongPass123!')
        
        assert is_valid is True
        assert error is None
    
    def test_weak_password_too_short(self):
        """Test that short password fails."""
        is_valid, error = check_password_strength('Short1!')
        
        assert is_valid is False
        assert error is not None
        assert '8 characters' in error
    
    def test_weak_password_no_uppercase(self):
        """Test that password without uppercase fails."""
        is_valid, error = check_password_strength('lowercase123!')
        
        assert is_valid is False
        assert 'uppercase' in error.lower()
    
    def test_weak_password_no_lowercase(self):
        """Test that password without lowercase fails."""
        is_valid, error = check_password_strength('UPPERCASE123!')
        
        assert is_valid is False
        assert 'lowercase' in error.lower()
    
    def test_weak_password_no_digit(self):
        """Test that password without digit fails."""
        is_valid, error = check_password_strength('NoDigitsHere!')
        
        assert is_valid is False
        assert 'digit' in error.lower()
    
    def test_weak_password_no_special(self):
        """Test that password without special character fails."""
        is_valid, error = check_password_strength('NoSpecial123')
        
        assert is_valid is False
        assert 'special character' in error.lower()


class TestTemporaryPassword:
    """Tests for temporary password generation."""
    
    def test_generate_temporary_password(self):
        """Test that temporary password is generated."""
        temp_pass = generate_temporary_password()
        
        assert temp_pass is not None
        assert isinstance(temp_pass, str)
        assert len(temp_pass) == 16  # Default length
    
    def test_temporary_password_strength(self):
        """Test that generated password meets strength requirements."""
        temp_pass = generate_temporary_password()
        is_valid, error = check_password_strength(temp_pass)
        
        assert is_valid is True
        assert error is None
    
    def test_temporary_password_custom_length(self):
        """Test temporary password with custom length."""
        temp_pass = generate_temporary_password(length=20)
        
        assert len(temp_pass) == 20
    
    def test_temporary_passwords_are_unique(self):
        """Test that generated passwords are unique."""
        passwords = [generate_temporary_password() for _ in range(50)]
        
        assert len(set(passwords)) == 50  # All unique
    
    def test_temporary_password_contains_all_character_types(self):
        """Test that password contains uppercase, lowercase, digit, special."""
        temp_pass = generate_temporary_password()
        
        assert any(c.isupper() for c in temp_pass)
        assert any(c.islower() for c in temp_pass)
        assert any(c.isdigit() for c in temp_pass)
        assert any(not c.isalnum() for c in temp_pass)
