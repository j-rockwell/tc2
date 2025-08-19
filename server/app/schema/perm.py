from typing import List
from enum import Enum
from pydantic import BaseModel, Field
from bson import ObjectId

class Permission(str, Enum):
    ADMIN = "admin"                          # Full access to all system features
    MOD_USERS = "moderate_users"             # Perform moderation tasks on user accounts
    MOD_POSTS = "moderate_posts"             # Perform moderation tasks on posts
    MOD_EXERCISES = "moderate_exercises"     # Perform moderation tasks on exercise metadata
    VIEW_ROLES = "view_roles"                # View roles and permissions
    EDIT_ROLES = "edit_roles"                # Create, edit, or delete roles
    VIEW_AUDIT_LOG = "view_audit_log"        # View the audit log for actions taken in the system
    VIEW_PERMISSIONS = "view_permissions"    # View permissions assigned to roles and users
    BYPASS_PRIVACY = "bypass_privacy"        # Bypass privacy settings for users

class Role(BaseModel):
    name: str
    permissions: List[Permission] = []

class RoleInDB(Role):
    id: str = Field(alias="_id")

    class Config:
        allow_population_by_field_name = True
        json_encoders = { ObjectId: str }
        from_attributes = True