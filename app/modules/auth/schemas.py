"""
Authentication Request/Response Data
Simple dataclasses for validation (no external dependencies needed).
"""

from dataclasses import dataclass, asdict
from typing import Optional, List


@dataclass
class TokenRequest:
    """Login request with username and password"""
    username: str
    password: str


@dataclass
class UserInfo:
    """User information returned with token/session"""
    Kullanici_ID: int
    Adi_Soyadi: str
    Kullanici_Adi: str
    Email: Optional[str]
    Aktif_Pasif: bool
    branches: List[int]

    def to_dict(self):
        return asdict(self)


@dataclass
class LoginResponse:
    """Complete login response with token and user info"""
    access_token: str
    token_type: str
    user: dict  # UserInfo as dict
    permissions: List[str]

    def to_dict(self):
        return {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "user": self.user,
            "permissions": self.permissions,
        }


@dataclass
class UserPermissions:
    """User permissions and roles"""
    Kullanici_ID: int
    Kullanici_Adi: str
    permissions: List[str]
    roles: List[str]
    branches: List[int]

    def to_dict(self):
        return asdict(self)
