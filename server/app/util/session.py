from fastapi import Request
from typing import Optional, Dict, Any, List
from app.db.redis import Redis
from datetime import datetime, timezone, timedelta
from app.config import settings
from json import dumps, loads
import logging

logger = logging.getLogger(__name__)

def get_client_info(request: Request) -> dict:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        ip = forwarded_for.split(",")[0].strip()
    else:
        ip = request.headers.get("X-Real-IP") or str(request.client.host)
    
    user_agent = request.headers.get("User-Agent", "")
    
    return {"ip": ip, "user_agent": user_agent}

class Sessions:
    @staticmethod
    async def create(
        redis: Redis,
        account_id: str,
        session_type: str,
        username: str,
        email: str,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        try:
            now = datetime.now(tz=timezone.utc)
            data = {
                "account_id": account_id,
                "username": username,
                "email": email,
                "session_type": session_type,
                "created_at": now.isoformat(),
                "last_active": now.isoformat(),
                "ip_address": ip,
                "user_agent": user_agent,
                "device_info": device_info or {},
                "is_active": True
            }
            
            key = f"session:{session_type}:{account_id}"
            ttl = (settings.access_token_ttl_minutes if session_type == 'access'
                   else settings.refresh_token_ttl_minutes) * 60
            
            await redis.setex(key, ttl, dumps(data))
            await Sessions._add(redis, account_id, session_type, data)
            
            logger.info(f"Session created for user {username} ({session_type})")
            return data
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    @staticmethod
    async def get(
        redis: Redis,
        account_id: str,
        session_type: str
    ) -> Optional[Dict[str, Any]]:
        try:
            key = f"session:{session_type}:{account_id}"
            data = await redis.get(key, decode_json=True)
            return data
        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return None
    
    @staticmethod
    async def update(
        redis: Redis,
        account_id: str,
        session_type: str,
        ip: Optional[str] = None
    ) -> bool:
        try:
            key = f"session:{session_type}:{account_id}"
            data = await redis.get(key, decode_json=True)
            
            if not data:
                return False
            
            now = datetime.now(tz=timezone.utc)
            data["last_active"] = now.isoformat()
            
            if ip and ip != data.get("ip_address"):
                data["ip_address"] = ip
                logger.warning(f"IP changed for user {data.get('username')}: {ip}")
            
            ttl = (settings.access_token_ttl_minutes if session_type == 'access'
                   else settings.refresh_token_ttl_minutes) * 60
            
            await redis.setex(key, ttl, dumps(data))
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session: {e}")
            return False
    
    @staticmethod
    async def invalidate(
        redis: Redis,
        account_id: str,
        session_type: str
    ) -> bool:
        try:
            key = f"session:{session_type}:{account_id}"
            data = await redis.get(key, decode_json=True)
            
            if data:
                data["is_active"] = False
                data["invalidated_at"] = datetime.now(tz=timezone.utc).isoformat()
                
                inv_key = f"invalidated_session:{session_type}:{account_id}:{int(datetime.now().timestamp())}"
                await redis.setex(inv_key, 3600, dumps(data))
            
            result = await redis.delete(key)
            await Sessions._rem(redis, account_id, session_type)
            
            logger.info(f"Session invalidated for account {account_id} ({session_type})")
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to invalidate session: {e}")
            return False
    
    @staticmethod
    async def invalidate_all(
        redis: Redis,
        account_id: str
    ) -> bool:
        try:
            success = True
            
            for session_type in ['access', 'refresh']:
                result = await Sessions.invalidate(redis, account_id, session_type)
                success = success and result
            
            await redis.delete(f"user:{account_id}")
            await redis.delete(f"active_sessions:{account_id}")
            
            logger.info(f"All sessions invalidated for account {account_id}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to invalidate all sessions: {e}")
            return False
    
    @staticmethod
    async def get_active(
        redis: Redis,
        account_id: str
    ) -> List[Dict[str, Any]]:
        try:
            sessions = []
            
            for session_type in ['access', 'refresh']:
                data = await Sessions.get(redis, account_id, session_type)
                if data and data.get("is_active", True):
                    sessions.append(data)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get active sessions: {e}")
            return []
    
    @staticmethod
    async def cleanup_exp(redis: Redis) -> int:
        try:
            cleaned = 0
            client = redis.get_client()
            
            # Get all session keys
            keys = []
            async for key in client.scan_iter(match="session:*"):
                keys.append(key)
            
            for key in keys:
                if not await redis.exists(key):
                    cleaned += 1
                    continue
                
                data = await redis.get(key, decode_json=True)
                if data:
                    last_active = datetime.fromisoformat(data.get("last_active", ""))
                    if datetime.now(tz=timezone.utc) - last_active > timedelta(hours=24):
                        await redis.delete(key)
                        cleaned += 1
            
            logger.info(f"Cleaned up {cleaned} expired sessions")
            return cleaned
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0
    
    @staticmethod
    async def get_stats(
        redis: Redis,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            stats = {
                "total_active": 0,
                "access_sessions": 0,
                "refresh_sessions": 0,
                "unique_users": 0
            }
            
            if account_id:
                sessions = await Sessions.get_active(redis, account_id)
                stats["total_active"] = len(sessions)
                stats["access_sessions"] = len([s for s in sessions if s.get("session_type") == "access"])
                stats["refresh_sessions"] = len([s for s in sessions if s.get("session_type") == "refresh"])
                stats["unique_users"] = 1 if sessions else 0
            else:
                client = redis.get_client()
                users = set()
                
                async for key in client.scan_iter(match="session:*"):
                    key_str = key.decode() if isinstance(key, bytes) else key
                    parts = key_str.split(":")
                    if len(parts) >= 3:
                        session_type = parts[1]
                        user_id = parts[2]
                        
                        stats["total_active"] += 1
                        users.add(user_id)
                        
                        if session_type == "access":
                            stats["access_sessions"] += 1
                        elif session_type == "refresh":
                            stats["refresh_sessions"] += 1
                
                stats["unique_users"] = len(users)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return {"error": str(e)}
    
    @staticmethod
    async def is_valid(
        redis: Redis,
        account_id: str,
        session_type: str
    ) -> bool:
        try:
            data = await Sessions.get(redis, account_id, session_type)
            
            if not data:
                return False
            
            if not data.get("is_active", True):
                return False
            
            last_active = datetime.fromisoformat(data.get("last_active", ""))
            max_inactive = timedelta(hours=24)
            
            if datetime.now(tz=timezone.utc) - last_active > max_inactive:
                await Sessions.invalidate(redis, account_id, session_type)
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate session: {e}")
            return False
    
    @staticmethod
    async def _add(
        redis: Redis,
        account_id: str,
        session_type: str,
        data: Dict[str, Any]
    ):
        try:
            key = f"active_sessions:{account_id}"
            info = {
                "type": session_type,
                "created_at": data["created_at"],
                "ip_address": data.get("ip_address"),
                "user_agent": data.get("user_agent")
            }
            
            await redis.sadd(key, dumps(info))
            await redis.expire(key, settings.refresh_token_ttl_minutes * 60)
            
        except Exception as e:
            logger.error(f"Failed to add to active sessions: {e}")
    
    @staticmethod
    async def _rem(
        redis: Redis,
        account_id: str,
        session_type: str
    ):
        try:
            key = f"active_sessions:{account_id}"
            members = await redis.smembers(key)
            
            for member in members:
                try:
                    info = loads(member)
                    if info.get("type") == session_type:
                        await redis.srem(key, member)
                        break
                except Exception:
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to remove from active sessions: {e}")

class SessionSecurity:
    @staticmethod
    async def detect_suspicious(
        redis: Redis,
        account_id: str,
        current_ip: str,
        current_ua: str
    ) -> Dict[str, Any]:
        try:
            score = 0
            alerts = []
            
            sessions = await Sessions.get_active(redis, account_id)
            
            if not sessions:
                return {"score": 0, "alerts": []}
            
            ips = {current_ip}
            user_agents = {current_ua}
            
            for session in sessions:
                if session.get("ip_address"):
                    ips.add(session["ip_address"])
                if session.get("user_agent"):
                    user_agents.add(session["user_agent"])
            
            if len(ips) > 2:
                score += 30
                alerts.append(f"Multiple IPs: {len(ips)}")
            
            if len(user_agents) > 3:
                score += 20
                alerts.append(f"Multiple user agents: {len(user_agents)}")
            
            recent_key = f"recent_sessions:{account_id}"
            recent_count = await redis.get(recent_key)
            
            if recent_count and int(recent_count) > 5:
                score += 40
                alerts.append("Rapid session creation")
            
            private_prefixes = ["192.168.", "10.", "172.16.", "127."]
            public_ips = [ip for ip in ips if not any(ip.startswith(p) for p in private_prefixes)]
            
            if len(public_ips) > 1:
                score += 25
                alerts.append("Multiple public IPs")
            
            return {
                "score": score,
                "alerts": alerts,
                "unique_ips": len(ips),
                "unique_uas": len(user_agents)
            }
            
        except Exception as e:
            logger.error(f"Failed to detect suspicious activity: {e}")
            return {"score": 0, "alerts": [], "error": str(e)}
    
    @staticmethod
    async def should_challenge(
        redis: Redis,
        account_id: str,
        ip: str,
        user_agent: str
    ) -> bool:
        try:
            activity = await SessionSecurity.detect_suspicious(redis, account_id, ip, user_agent)
            
            if activity["score"] > 50:
                return True
            
            trusted_key = f"trusted_ips:{account_id}"
            trusted_ips = await redis.smembers(trusted_key)
            
            if ip not in trusted_ips:
                recent_key = f"recent_ips:{account_id}"
                recent_ips = await redis.smembers(recent_key)
                
                if len(recent_ips) > 0 and ip not in recent_ips:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check if should challenge: {e}")
            return False
    
    @staticmethod
    async def add_trusted_ip(
        redis: Redis,
        account_id: str,
        ip: str
    ):
        try:
            trusted_key = f"trusted_ips:{account_id}"
            await redis.sadd(trusted_key, ip)
            await redis.expire(trusted_key, 30 * 24 * 3600)  # 30 days
            
            recent_key = f"recent_ips:{account_id}"
            await redis.sadd(recent_key, ip)
            await redis.expire(recent_key, 7 * 24 * 3600)  # 7 days
            
        except Exception as e:
            logger.error(f"Failed to add trusted IP: {e}")
    
    @staticmethod
    async def log_event(
        redis: Redis,
        account_id: str,
        event_type: str,
        details: Dict[str, Any],
        ip: Optional[str] = None
    ):
        try:
            event = {
                "account_id": account_id,
                "event_type": event_type,
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                "ip_address": ip,
                "details": details
            }
            
            user_log_key = f"security_log:{account_id}"
            await redis.lpush(user_log_key, dumps(event))
            await redis.ltrim(user_log_key, 0, 99)  # Keep last 100
            await redis.expire(user_log_key, 30 * 24 * 3600)  # 30 days
            
            global_log_key = "global_security_events"
            await redis.lpush(global_log_key, dumps(event))
            await redis.ltrim(global_log_key, 0, 999)  # Keep last 1000
            await redis.expire(global_log_key, 7 * 24 * 3600)  # 7 days
            
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")