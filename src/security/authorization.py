"""
Enterprise Authorization and Access Control
Role-based access control (RBAC) with fine-grained permissions
"""

from typing import List, Dict, Set, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

class PermissionLevel(Enum):
    """Permission levels for actions"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

@dataclass
class Permission:
    """Individual permission for a resource"""
    resource: str
    action: str
    level: PermissionLevel
    conditions: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self):
        return f"{self.resource}:{self.action}:{self.level.value}"

@dataclass
class Role:
    """User role with associated permissions"""
    name: str
    description: str
    permissions: Set[Permission] = field(default_factory=set)
    inherits_from: List[str] = field(default_factory=list)
    
    def add_permission(self, permission: Permission):
        """Add permission to role"""
        self.permissions.add(permission)
    
    def has_permission(self, resource: str, action: str, level: PermissionLevel = None) -> bool:
        """Check if role has specific permission"""
        for perm in self.permissions:
            if perm.resource == resource and perm.action == action:
                if level is None or perm.level.value >= level.value:
                    return True
        return False

class RoleBasedAccessControl:
    """Role-based access control system"""
    
    def __init__(self):
        self.roles: Dict[str, Role] = {}
        self.user_roles: Dict[str, Set[str]] = {}
        self._init_default_roles()
    
    def _init_default_roles(self):
        """Initialize default system roles"""
        # Admin role
        admin_role = Role(
            name="admin",
            description="System administrator with full access"
        )
        admin_role.add_permission(Permission("*", "*", PermissionLevel.ADMIN))
        self.roles["admin"] = admin_role
        
        # User role
        user_role = Role(
            name="user",
            description="Regular user with basic access"
        )
        user_role.add_permission(Permission("models", "read", PermissionLevel.READ))
        user_role.add_permission(Permission("tasks", "create", PermissionLevel.WRITE))
        self.roles["user"] = user_role
        
        # API role
        api_role = Role(
            name="api_user",
            description="API access with limited permissions"
        )
        api_role.add_permission(Permission("api", "call", PermissionLevel.EXECUTE))
        self.roles["api_user"] = api_role
    
    def create_role(self, role: Role) -> bool:
        """Create new role"""
        if role.name in self.roles:
            return False
        self.roles[role.name] = role
        logger.info(f"Created role: {role.name}")
        return True
    
    def assign_role(self, user_id: str, role_name: str) -> bool:
        """Assign role to user"""
        if role_name not in self.roles:
            return False
        
        if user_id not in self.user_roles:
            self.user_roles[user_id] = set()
        
        self.user_roles[user_id].add(role_name)
        logger.info(f"Assigned role {role_name} to user {user_id}")
        return True
    
    def check_permission(self, user_id: str, resource: str, action: str, level: PermissionLevel = None) -> bool:
        """Check if user has permission for action"""
        if user_id not in self.user_roles:
            return False
        
        for role_name in self.user_roles[user_id]:
            if role_name in self.roles:
                role = self.roles[role_name]
                if role.has_permission(resource, action, level):
                    return True
        
        return False

class AuthorizationManager:
    """Central authorization management"""
    
    def __init__(self):
        self.rbac = RoleBasedAccessControl()
        self.policies: Dict[str, Any] = {}
    
    def authorize(self, user_id: str, resource: str, action: str, context: Dict[str, Any] = None) -> bool:
        """Authorize user action"""
        # Check RBAC permissions
        if self.rbac.check_permission(user_id, resource, action):
            return True
        
        # Check custom policies
        return self._check_policies(user_id, resource, action, context)
    
    def _check_policies(self, user_id: str, resource: str, action: str, context: Dict[str, Any] = None) -> bool:
        """Check custom authorization policies"""
        # Placeholder for custom policy evaluation
        return False
    
    def add_policy(self, name: str, policy: Dict[str, Any]):
        """Add custom authorization policy"""
        self.policies[name] = policy
        logger.info(f"Added authorization policy: {name}")
    
    def get_user_permissions(self, user_id: str) -> List[str]:
        """Get all permissions for user"""
        permissions = []
        if user_id in self.rbac.user_roles:
            for role_name in self.rbac.user_roles[user_id]:
                if role_name in self.rbac.roles:
                    role = self.rbac.roles[role_name]
                    for perm in role.permissions:
                        permissions.append(str(perm))
        return permissions 