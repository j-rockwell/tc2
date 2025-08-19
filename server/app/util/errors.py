from dataclasses import dataclass
from typing import Dict, Any, Optional

class ServerError(Exception):
    code: str
    message: str
    http_status: int = 400
    context: Optional[Dict[str, Any]] = None

class PermissionDeniedError(ServerError):
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        self.code = "permission_denied"
        self.message = message
        self.http_status = 403
        self.context = context