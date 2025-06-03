"""
Enterprise Encryption and Data Protection
Advanced encryption, key management, and data classification
"""

import os
import base64
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)

class DataClassification:
    """Data classification levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

class EncryptionManager:
    """Enterprise-grade encryption manager"""
    
    def __init__(self, master_key: Optional[bytes] = None):
        if master_key:
            self.key = master_key
        else:
            self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        encrypted_data = self.cipher.encrypt(data.encode())
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        decoded_data = base64.b64decode(encrypted_data.encode())
        decrypted_data = self.cipher.decrypt(decoded_data)
        return decrypted_data.decode()
    
    def generate_key_from_password(self, password: str, salt: bytes = None) -> bytes:
        """Generate encryption key from password"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

class SecureStorage:
    """Secure storage with classification-based encryption"""
    
    def __init__(self):
        self.encryption_manager = EncryptionManager()
        self.storage: Dict[str, Dict[str, Any]] = {}
    
    def store(self, key: str, data: Any, classification: str = DataClassification.INTERNAL) -> bool:
        """Store data with encryption based on classification"""
        try:
            if classification in [DataClassification.CONFIDENTIAL, DataClassification.RESTRICTED]:
                # Encrypt sensitive data
                encrypted_data = self.encryption_manager.encrypt(str(data))
                self.storage[key] = {
                    "data": encrypted_data,
                    "classification": classification,
                    "encrypted": True
                }
            else:
                # Store less sensitive data without encryption
                self.storage[key] = {
                    "data": data,
                    "classification": classification,
                    "encrypted": False
                }
            return True
        except Exception as e:
            logger.error(f"Failed to store data: {e}")
            return False
    
    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve and decrypt data"""
        if key not in self.storage:
            return None
        
        stored_item = self.storage[key]
        try:
            if stored_item.get("encrypted", False):
                return self.encryption_manager.decrypt(stored_item["data"])
            else:
                return stored_item["data"]
        except Exception as e:
            logger.error(f"Failed to retrieve data: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Securely delete data"""
        if key in self.storage:
            del self.storage[key]
            return True
        return False 