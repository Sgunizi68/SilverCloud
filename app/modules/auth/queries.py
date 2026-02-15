"""
Authentication Database Queries
Retrieves and validates user data, roles, and permissions.
Uses SQLAlchemy 2.0 style with eager loading for performance.
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.models import Kullanici, KullaniciRol, Rol, RolYetki, Yetki
from app.modules.auth.security import verify_password


def get_kullanici_by_username(db: Session, username: str) -> Optional[Kullanici]:
    """
    Get a user by username.
    Uses eager loading to get roles/permissions in single query.
    Case-insensitive search.
    
    Args:
        db: Database session
        username: Username to search for
    
    Returns:
        Kullanici object if found, None otherwise
    """
    stmt = (
        select(Kullanici)
        .where(Kullanici.Kullanici_Adi.ilike(username))
        .options(joinedload(Kullanici.kullanici_rolleri))
    )
    return db.scalars(stmt).unique().first()


def get_kullanici_by_id(db: Session, kullanici_id: int) -> Optional[Kullanici]:
    """
    Get a user by ID.
    
    Args:
        db: Database session
        kullanici_id: User ID
    
    Returns:
        Kullanici object if found, None otherwise
    """
    return db.get(Kullanici, kullanici_id)


def authenticate_user(
    db: Session,
    username: str,
    password: str
) -> Optional[Kullanici]:
    """
    Authenticate a user by username and password.
    
    Args:
        db: Database session
        username: Username
        password: Plain text password
    
    Returns:
        Kullanici object if credentials valid, None otherwise
    """
    user = get_kullanici_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.Password):
        return None
    return user


def get_user_permissions(
    db: Session,
    kullanici_id: int,
    sube_id: Optional[int] = None
) -> List[str]:
    """
    Get all permissions for a user, optionally filtered by branch (Sube).
    
    Admin users (username='admin' or assigned to 'Admin' role) get ALL permissions.
    Non-admin users get role-based permissions filtered by branch.
    
    Args:
        db: Database session
        kullanici_id: User ID
        sube_id: Optional branch ID to filter permissions by branch
    
    Returns:
        List of permission names (Yetki_Adi)
    """
    # Get user
    user = db.get(Kullanici, kullanici_id)
    if not user or not user.Aktif_Pasif:
        return []
    
    # Check if user is admin (by username or by Admin role)
    is_admin_by_username = user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin'
    
    is_admin_by_role = False
    if not is_admin_by_username:
        # Check if user has Admin role
        admin_role_stmt = (
            select(Rol.Rol_ID)
            .where(Rol.Rol_Adi.ilike('admin'))
            .limit(1)
        )
        admin_role_id = db.scalars(admin_role_stmt).first()
        
        if admin_role_id:
            admin_role_assigned_stmt = (
                select(KullaniciRol.Rol_ID)
                .where(
                    (KullaniciRol.Kullanici_ID == kullanici_id) &
                    (KullaniciRol.Rol_ID == admin_role_id) &
                    (KullaniciRol.Aktif_Pasif == True)
                )
            )
            if sube_id:
                admin_role_assigned_stmt = admin_role_assigned_stmt.where(
                    KullaniciRol.Sube_ID == sube_id
                )
            is_admin_by_role = db.scalars(admin_role_assigned_stmt).first() is not None
    
    # If admin, return ALL permissions
    if is_admin_by_username or is_admin_by_role:
        stmt = select(Yetki.Yetki_Adi).where(Yetki.Aktif_Pasif == True)
        return db.scalars(stmt).unique().all()
    
    # Otherwise, return role-based permissions
    stmt = (
        select(Yetki.Yetki_Adi)
        .join(RolYetki, Yetki.Yetki_ID == RolYetki.Yetki_ID)
        .join(Rol, RolYetki.Rol_ID == Rol.Rol_ID)
        .join(KullaniciRol, Rol.Rol_ID == KullaniciRol.Rol_ID)
        .where(
            (KullaniciRol.Kullanici_ID == kullanici_id) &
            (RolYetki.Aktif_Pasif == True) &
            (Rol.Aktif_Pasif == True) &
            (Yetki.Aktif_Pasif == True)
        )
    )
    
    # Add branch filter if provided
    if sube_id:
        stmt = stmt.where(KullaniciRol.Sube_ID == sube_id)
    
    return db.scalars(stmt).unique().all()


def get_user_roles(
    db: Session,
    kullanici_id: int,
    sube_id: Optional[int] = None
) -> List[str]:
    """
    Get all roles for a user, optionally filtered by branch (Sube).
    
    Args:
        db: Database session
        kullanici_id: User ID
        sube_id: Optional branch ID
    
    Returns:
        List of role names (Rol_Adi)
    """
    stmt = (
        select(Rol.Rol_Adi)
        .join(KullaniciRol, Rol.Rol_ID == KullaniciRol.Rol_ID)
        .where(
            (KullaniciRol.Kullanici_ID == kullanici_id) &
            (KullaniciRol.Aktif_Pasif == True) &
            (Rol.Aktif_Pasif == True)
        )
    )
    
    if sube_id:
        stmt = stmt.where(KullaniciRol.Sube_ID == sube_id)
    
    return db.scalars(stmt).unique().all()


def get_user_branches(db: Session, kullanici_id: int) -> List[int]:
    """
    Get all branch IDs (Sube_ID) that a user has roles in.
    
    Args:
        db: Database session
        kullanici_id: User ID
    
    Returns:
        List of Sube_ID values
    """
    stmt = (
        select(KullaniciRol.Sube_ID)
        .where(
            (KullaniciRol.Kullanici_ID == kullanici_id) &
            (KullaniciRol.Aktif_Pasif == True)
        )
        .distinct()
    )
    return db.scalars(stmt).all()


def has_permission(
    db: Session,
    kullanici_id: int,
    permission_name: str,
    sube_id: Optional[int] = None
) -> bool:
    """
    Check if user has a specific permission.
    
    Args:
        db: Database session
        kullanici_id: User ID
        permission_name: Permission name to check
        sube_id: Optional branch ID for permission scope
    
    Returns:
        True if user has permission, False otherwise
    """
    permissions = get_user_permissions(db, kullanici_id, sube_id)
    return permission_name in permissions


def get_kullanici_by_rol_name(
    db: Session,
    rol_adi: str,
    sube_id: Optional[int] = None
) -> List[Kullanici]:
    """
    Get all users with a specific role, optionally filtered by branch.
    
    Args:
        db: Database session
        rol_adi: Role name to search for
        sube_id: Optional branch ID
    
    Returns:
        List of Kullanici objects
    """
    stmt = (
        select(Kullanici)
        .join(KullaniciRol, Kullanici.Kullanici_ID == KullaniciRol.Kullanici_ID)
        .join(Rol, KullaniciRol.Rol_ID == Rol.Rol_ID)
        .where(
            (Rol.Rol_Adi == rol_adi) &
            (KullaniciRol.Aktif_Pasif == True) &
            (Rol.Aktif_Pasif == True)
        )
    )
    
    if sube_id:
        stmt = stmt.where(KullaniciRol.Sube_ID == sube_id)
    
    return db.scalars(stmt).unique().all()
