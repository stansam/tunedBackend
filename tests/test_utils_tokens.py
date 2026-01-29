"""
Unit tests for token utilities.

Tests token generation, verification, and expiration using itsdangerous.
"""
import pytest
from tuned.utils.tokens import (
    generate_verification_token,
    verify_verification_token,
    generate_password_reset_token,
    verify_password_reset_token,
    generate_referral_code,
    generate_secure_random_string
)
import time


class TestVerificationToken:
    """Tests for email verification token generation and validation."""
    
    def test_generate_verification_token(self, app):
        """Test verification token generation."""
        with app.app_context():
            token = generate_verification_token(1, 'test@example.com')
            
            assert token is not None
            assert isinstance(token, str)
            assert len(token) > 20  # Tokens should be reasonably long
    
    def test_verify_valid_verification_token(self, app):
        """Test verification of a valid token."""
        with app.app_context():
            token = generate_verification_token(123, 'test@example.com')
            data = verify_verification_token(token)
            
            assert data is not None
            assert data['user_id'] == 123
            assert data['email'] == 'test@example.com'
    
    def test_verify_invalid_verification_token(self, app):
        """Test verification of an invalid token."""
        with app.app_context():
            data = verify_verification_token('invalid_token_string')
            
            assert data is None
    
    def test_verify_expired_verification_token(self, app, mocker):
        """Test verification of an expired token."""
        with app.app_context():
            # Mock the verification to simulate expired token
            mocker.patch(
                'tuned.utils.tokens.verify_token',
                return_value=None
            )
            
            token = generate_verification_token(1, 'test@example.com')
            data = verify_verification_token(token)
            
            assert data is None
    
    def test_token_contains_correct_data(self, app):
        """Test that token contains the expected data."""
        with app.app_context():
            user_id = 456
            email = 'user@example.com'
            
            token = generate_verification_token(user_id, email)
            data = verify_verification_token(token)
            
            assert data['user_id'] == user_id
            assert data['email'] == email


class TestPasswordResetToken:
    """Tests for password reset token generation and validation."""
    
    def test_generate_password_reset_token(self, app):
        """Test password reset token generation."""
        with app.app_context():
            token = generate_password_reset_token(1, 'test@example.com')
            
            assert token is not None
            assert isinstance(token, str)
            assert len(token) > 20
    
    def test_verify_valid_password_reset_token(self, app):
        """Test verification of a valid reset token."""
        with app.app_context():
            token = generate_password_reset_token(789, 'reset@example.com')
            data = verify_password_reset_token(token)
            
            assert data is not None
            assert data['user_id'] == 789
            assert data['email'] == 'reset@example.com'
    
    def test_verify_invalid_password_reset_token(self, app):
        """Test verification of an invalid reset token."""
        with app.app_context():
            data = verify_password_reset_token('invalid_reset_token')
            
            assert data is None
    
    def test_different_tokens_for_different_purposes(self, app):
        """Test that verification and reset tokens use different salts."""
        with app.app_context():
            user_id = 100
            email = 'test@example.com'
            
            verify_token = generate_verification_token(user_id, email)
            reset_token = generate_password_reset_token(user_id, email)
            
            # Tokens should be different even with same data
            assert verify_token != reset_token
            
            # Verification token shouldn't validate as reset token
            assert verify_password_reset_token(verify_token) is None
            assert verify_verification_token(reset_token) is None


class TestReferralCode:
    """Tests for referral code generation."""
    
    def test_generate_referral_code_default_length(self):
        """Test referral code generation with default length."""
        code = generate_referral_code()
        
        assert code is not None
        assert isinstance(code, str)
        assert len(code) == 8
        assert code.isalnum()
        assert code.isupper()
    
    def test_generate_referral_code_custom_length(self):
        """Test referral code generation with custom length."""
        code = generate_referral_code(length=12)
        
        assert len(code) == 12
        assert code.isalnum()
    
    def test_referral_codes_are_unique(self):
        """Test that generated referral codes are unique."""
        codes = [generate_referral_code() for _ in range(100)]
        
        # Should have 100 unique codes
        assert len(set(codes)) == 100
    
    def test_referral_code_no_ambiguous_characters(self):
        """Test that referral code excludes ambiguous characters."""
        codes = [generate_referral_code() for _ in range(50)]
        
        for code in codes:
            # Should not contain 0, O, I, 1
            assert '0' not in code
            assert 'O' not in code
            assert 'I' not in code
            assert '1' not in code


class TestSecureRandomString:
    """Tests for secure random string generation."""
    
    def test_generate_secure_random_string(self):
        """Test secure random string generation."""
        random_str = generate_secure_random_string(32)
        
        assert random_str is not None
        assert isinstance(random_str, str)
        assert len(random_str) == 32
    
    def test_random_strings_are_unique(self):
        """Test that generated random strings are unique."""
        strings = [generate_secure_random_string(32) for _ in range(50)]
        
        assert len(set(strings)) == 50
    
    def test_random_string_custom_length(self):
        """Test random string with custom length."""
        random_str = generate_secure_random_string(64)
        
        assert len(random_str) == 64
