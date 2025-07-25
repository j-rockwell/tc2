from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from json import dumps
from app.config import settings
import jwt

class Tokenizer:
    @staticmethod
    def create_access_token(id: str, additional_claims: Optional[Dict[str, Any]] = None):
        now = datetime.now(tz=timezone.utc)
        exp = now + timedelta(minutes=settings.access_token_ttl_minutes)
        payload = {
            "sub": id,
            "iat": now,
            "exp": exp,
            "type": "access"
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, settings.access_token_secret, algorithm="HS256")
    
    @staticmethod
    def create_refresh_token(id: str, additional_claims: Optional[Dict[str, Any]] = None):
        now = datetime.now(tz=timezone.utc)
        exp = now + timedelta(minutes=settings.refresh_token_ttl_minutes)
        payload = {
            "sub": id,
            "iat": now,
            "exp": exp,
            "type": "refresh"
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, settings.refresh_token_secret, algorithm="HS256")
    
    @staticmethod
    def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(
                token, 
                settings.access_token_secret, 
                algorithms=["HS256"]
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def decode_refresh_token(token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(
                token, 
                settings.refresh_token_secret, 
                algorithms=["HS256"]
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        result = Tokenizer.decode_access_token(token)
        if result:
            return result
        
        return Tokenizer.decode_refresh_token(token)
    
    @staticmethod
    def get_user_id_from_token(token: str) -> Optional[str]:
        payload = Tokenizer.decode_token(token)
        if payload:
            return payload.get("sub")
        return None