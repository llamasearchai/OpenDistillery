"""
OpenDistillery Authentication Module
Comprehensive authentication and authorization system with MFA, JWT, and API key management.
"""

import hashlib
import secrets
import pyotp
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
import logging
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User role definitions"""
    ADMIN = "admin"
    USER = "user"
    ENTERPRISE = "enterprise"
    READONLY = "readonly"

@dataclass
class AuthenticationResult:
    """Result of authentication attempt"""
    success: bool
    user_id: Optional[str] = None
    username: Optional[str] = None
    role: Optional[UserRole] = None
    token: Optional[str] = None
    error_message: Optional[str] = None
    requires_mfa: bool = False

@dataclass
class User:
    """User data structure"""
    user_id: str
    username: str
    email: str
    password_hash: str
    role: UserRole
    is_active: bool = True
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    created_at: datetime = None
    updated_at: datetime = None

class TokenManager:
    """Manages JWT tokens"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def create_token(self, user_id: str, username: str, role: UserRole, expires_delta: timedelta = None) -> str:
        """Create JWT token"""
        if expires_delta is None:
            expires_delta = timedelta(hours=24)
        
        expire = datetime.utcnow() + expires_delta
        payload = {
            "user_id": user_id,
            "username": username,
            "role": role.value,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")

class APIKeyManager:
    """Manages API keys"""
    
    def __init__(self):
        self.api_keys: Dict[str, Dict[str, Any]] = {}
    
    def generate_api_key(self, user_id: str, name: str, permissions: List[str], expires_in_days: int = 90) -> str:
        """Generate new API key"""
        api_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        expires_at = datetime.now() + timedelta(days=expires_in_days)
        
        self.api_keys[key_hash] = {
            "user_id": user_id,
            "name": name,
            "permissions": permissions,
            "created_at": datetime.now(),
            "expires_at": expires_at,
            "is_active": True,
            "last_used": None
        }
        
        return api_key
    
    def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Verify API key and return key info"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        if key_hash not in self.api_keys:
            return None
        
        key_info = self.api_keys[key_hash]
        
        # Check if key is expired
        if datetime.now() > key_info["expires_at"]:
            return None
        
        # Check if key is active
        if not key_info["is_active"]:
            return None
        
        # Update last used
        key_info["last_used"] = datetime.now()
        
        return key_info

class MFAManager:
    """Manages Multi-Factor Authentication"""
    
    @staticmethod
    def generate_mfa_secret() -> str:
        """Generate MFA secret"""
        return pyotp.random_base32()
    
    @staticmethod
    def generate_qr_code_url(secret: str, username: str, issuer: str = "OpenDistillery") -> str:
        """Generate QR code URL for MFA setup"""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=username,
            issuer_name=issuer
        )
    
    @staticmethod
    def verify_mfa_token(secret: str, token: str) -> bool:
        """Verify MFA token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)

class AuthenticationManager:
    """Main authentication manager"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.token_manager = TokenManager(secret_key)
        self.api_key_manager = APIKeyManager()
        self.mfa_manager = MFAManager()
        self.users: Dict[str, User] = {}
    
    def hash_password(self, password: str) -> str:
        """Hash password"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_user(self, username: str, email: str, password: str, role: UserRole = UserRole.USER) -> User:
        """Create new user"""
        # Check if user already exists
        for user in self.users.values():
            if user.username == username or user.email == email:
                raise ValueError("User already exists")
        
        user_id = secrets.token_urlsafe(16)
        password_hash = self.hash_password(password)
        
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.users[user_id] = user
        logger.info(f"Created user {username} with role {role.value}")
        
        return user
    
    def authenticate_user(self, username: str, password: str, mfa_token: str = None) -> AuthenticationResult:
        """Authenticate user with username/password and optional MFA"""
        # Find user
        user = None
        for u in self.users.values():
            if u.username == username:
                user = u
                break
        
        if not user:
            logger.warning(f"Authentication failed: User {username} not found")
            return AuthenticationResult(success=False, error_message="Invalid credentials")
        
        # Check if account is locked
        if user.locked_until and datetime.now() < user.locked_until:
            logger.warning(f"Authentication failed: Account {username} is locked")
            return AuthenticationResult(success=False, error_message="Account is locked")
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Authentication failed: Account {username} is inactive")
            return AuthenticationResult(success=False, error_message="Account is inactive")
        
        # Verify password
        if not self.verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            
            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.now() + timedelta(hours=1)
                logger.warning(f"Account {username} locked due to too many failed attempts")
            
            logger.warning(f"Authentication failed: Invalid password for {username}")
            return AuthenticationResult(success=False, error_message="Invalid credentials")
        
        # Check MFA if enabled
        if user.mfa_enabled:
            if not mfa_token:
                return AuthenticationResult(
                    success=False, 
                    requires_mfa=True,
                    error_message="MFA token required"
                )
            
            if not self.mfa_manager.verify_mfa_token(user.mfa_secret, mfa_token):
                logger.warning(f"Authentication failed: Invalid MFA token for {username}")
                return AuthenticationResult(success=False, error_message="Invalid MFA token")
        
        # Reset failed login attempts on successful authentication
        user.failed_login_attempts = 0
        user.locked_until = None
        
        # Generate JWT token
        token = self.token_manager.create_token(user.user_id, user.username, user.role)
        
        logger.info(f"User {username} authenticated successfully")
        
        return AuthenticationResult(
            success=True,
            user_id=user.user_id,
            username=user.username,
            role=user.role,
            token=token
        )
    
    def authenticate_api_key(self, api_key: str) -> AuthenticationResult:
        """Authenticate using API key"""
        key_info = self.api_key_manager.verify_api_key(api_key)
        
        if not key_info:
            logger.warning("Authentication failed: Invalid API key")
            return AuthenticationResult(success=False, error_message="Invalid API key")
        
        # Get user
        user = self.users.get(key_info["user_id"])
        if not user or not user.is_active:
            logger.warning("Authentication failed: User associated with API key is inactive")
            return AuthenticationResult(success=False, error_message="User is inactive")
        
        logger.info(f"API key authentication successful for user {user.username}")
        
        return AuthenticationResult(
            success=True,
            user_id=user.user_id,
            username=user.username,
            role=user.role
        )
    
    def verify_token(self, token: str) -> AuthenticationResult:
        """Verify JWT token"""
        try:
            payload = self.token_manager.verify_token(token)
            
            user = self.users.get(payload["user_id"])
            if not user or not user.is_active:
                return AuthenticationResult(success=False, error_message="User is inactive")
            
            return AuthenticationResult(
                success=True,
                user_id=payload["user_id"],
                username=payload["username"],
                role=UserRole(payload["role"])
            )
            
        except ValueError as e:
            logger.warning(f"Token verification failed: {e}")
            return AuthenticationResult(success=False, error_message=str(e))
    
    def enable_mfa(self, user_id: str) -> str:
        """Enable MFA for user and return QR code URL"""
        user = self.users.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        secret = self.mfa_manager.generate_mfa_secret()
        user.mfa_secret = secret
        user.mfa_enabled = True
        
        qr_url = self.mfa_manager.generate_qr_code_url(secret, user.username)
        
        logger.info(f"MFA enabled for user {user.username}")
        
        return qr_url
    
    def disable_mfa(self, user_id: str):
        """Disable MFA for user"""
        user = self.users.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        user.mfa_enabled = False
        user.mfa_secret = None
        
        logger.info(f"MFA disabled for user {user.username}")
    
    def create_api_key(self, user_id: str, name: str, permissions: List[str], expires_in_days: int = 90) -> str:
        """Create API key for user"""
        user = self.users.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        api_key = self.api_key_manager.generate_api_key(user_id, name, permissions, expires_in_days)
        
        logger.info(f"API key '{name}' created for user {user.username}")
        
        return api_key
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    def update_user(self, user_id: str, **kwargs):
        """Update user information"""
        user = self.users.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        user.updated_at = datetime.now()
        
        logger.info(f"User {user.username} updated")
    
    def delete_user(self, user_id: str):
        """Delete user"""
        user = self.users.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        username = user.username
        del self.users[user_id]
        
        logger.info(f"User {username} deleted") 