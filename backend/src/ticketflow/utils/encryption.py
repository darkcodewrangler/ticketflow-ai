#!/usr/bin/env python3
"""
Encryption utilities for securely storing sensitive configuration data

Provides AES encryption/decryption for sensitive settings like API tokens,
passwords, and other secrets stored in the database.
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)

class EncryptionManager:
    """
    Manages encryption and decryption of sensitive configuration data
    
    Uses AES encryption via Fernet (symmetric encryption) with a key derived
    from a master password/key stored in environment variables.
    """
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize encryption manager
        
        Args:
            master_key: Master encryption key. If None, will try to get from env var ENCRYPTION_KEY
        """
        self._fernet = None
        self._initialize_encryption(master_key)
    
    def _initialize_encryption(self, master_key: Optional[str] = None) -> None:
        """
        Initialize the encryption system with a master key
        
        Args:
            master_key: Master key for encryption. If None, generates or gets from env
        """
        try:
            if master_key:
                key = master_key.encode()
            else:
                # Try to get from environment variable
                env_key = os.getenv('TICKETFLOW_ENCRYPTION_KEY')
                if env_key:
                    key = env_key.encode()
                else:
                    # Generate a new key and warn user to save it
                    key = self._generate_master_key()
                    logger.warning(
                        "No encryption key found. Generated new key. "
                        "Please save this key to TICKETFLOW_ENCRYPTION_KEY environment variable: %s",
                        key.decode()
                    )
            
            # Derive a Fernet key from the master key
            fernet_key = self._derive_fernet_key(key)
            self._fernet = Fernet(fernet_key)
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise
    
    def _generate_master_key(self) -> bytes:
        """
        Generate a new master key for encryption
        
        Returns:
            Base64 encoded master key
        """
        # Generate a random 32-byte key and encode it
        key = os.urandom(32)
        return base64.urlsafe_b64encode(key)
    
    def _derive_fernet_key(self, master_key: bytes) -> bytes:
        """
        Derive a Fernet-compatible key from the master key
        
        Args:
            master_key: The master key bytes
            
        Returns:
            Fernet-compatible key
        """
        # Use a fixed salt for consistency (in production, you might want to store this separately)
        salt = b'ticketflow_salt_2024'
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(master_key))
        return key
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string
        
        Args:
            plaintext: The string to encrypt
            
        Returns:
            Base64 encoded encrypted string
            
        Raises:
            ValueError: If encryption is not initialized
            Exception: If encryption fails
        """
        if not self._fernet:
            raise ValueError("Encryption not initialized")
        
        try:
            # Convert string to bytes, encrypt, then encode as base64 string
            encrypted_bytes = self._fernet.encrypt(plaintext.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_text: str) -> str:
        """
        Decrypt an encrypted string
        
        Args:
            encrypted_text: Base64 encoded encrypted string
            
        Returns:
            Decrypted plaintext string
            
        Raises:
            ValueError: If encryption is not initialized
            Exception: If decryption fails
        """
        if not self._fernet:
            raise ValueError("Encryption not initialized")
        
        try:
            # Decode base64, decrypt, then convert back to string
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_text.encode('utf-8'))
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def is_encrypted(self, text: str) -> bool:
        """
        Check if a string appears to be encrypted (basic heuristic)
        
        Args:
            text: String to check
            
        Returns:
            True if the string appears to be encrypted
        """
        try:
            # Try to decode as base64 and check if it looks like encrypted data
            decoded = base64.urlsafe_b64decode(text.encode('utf-8'))
            # Encrypted data should be at least 45 bytes (Fernet overhead)
            return len(decoded) >= 45
        except:
            return False
    
    def encrypt_if_needed(self, text: str) -> str:
        """
        Encrypt text only if it's not already encrypted
        
        Args:
            text: Text to potentially encrypt
            
        Returns:
            Encrypted text (or original if already encrypted)
        """
        if self.is_encrypted(text):
            return text
        return self.encrypt(text)
    
    def decrypt_if_needed(self, text: str) -> str:
        """
        Decrypt text only if it appears to be encrypted
        
        Args:
            text: Text to potentially decrypt
            
        Returns:
            Decrypted text (or original if not encrypted)
        """
        if not self.is_encrypted(text):
            return text
        return self.decrypt(text)

# Global encryption manager instance
_encryption_manager: Optional[EncryptionManager] = None

def get_encryption_manager() -> EncryptionManager:
    """
    Get the global encryption manager instance
    
    Returns:
        EncryptionManager instance
    """
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager

def encrypt_value(value: str) -> str:
    """
    Convenience function to encrypt a value
    
    Args:
        value: Value to encrypt
        
    Returns:
        Encrypted value
    """
    return get_encryption_manager().encrypt(value)

def decrypt_value(encrypted_value: str) -> str:
    """
    Convenience function to decrypt a value
    
    Args:
        encrypted_value: Encrypted value to decrypt
        
    Returns:
        Decrypted value
    """
    return get_encryption_manager().decrypt(encrypted_value)

def encrypt_if_needed(value: str) -> str:
    """
    Convenience function to encrypt a value only if needed
    
    Args:
        value: Value to potentially encrypt
        
    Returns:
        Encrypted value (or original if already encrypted)
    """
    return get_encryption_manager().encrypt_if_needed(value)

def decrypt_if_needed(value: str) -> str:
    """
    Convenience function to decrypt a value only if needed
    
    Args:
        value: Value to potentially decrypt
        
    Returns:
        Decrypted value (or original if not encrypted)
    """
    return get_encryption_manager().decrypt_if_needed(value)