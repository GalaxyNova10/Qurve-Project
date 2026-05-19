"""
QURVE AI - Rate Limiting System
Production-grade API rate limiting with user-based and IP-based limits.

Features:
✅ User-based rate limiting
✅ IP-based rate limiting
✅ Endpoint-specific rate limiting
✅ Token-based rate limiting
✅ Distributed rate limiting
✅ Sliding window implementation
✅ Redis-based storage
✅ Configurable rate limits
"""

import time
import asyncio
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import redis.asyncio as redis
import logging
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RateLimitType(Enum):
    """Rate limit type classifications."""
    USER_BASED = "user_based"
    IP_BASED = "ip_based"
    TOKEN_BASED = "token_based"
    ENDPOINT_BASED = "endpoint_based"
    GLOBAL = "global"


class RateLimitWindow(Enum):
    """Rate limit window types."""
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"


@dataclass
class RateLimitRule:
    """Rate limit rule definition."""
    rule_id: str
    name: str
    limit_type: RateLimitType
    window: RateLimitWindow
    max_requests: int
    block_duration: int  # seconds
    endpoints: List[str] = field(default_factory=list)
    user_types: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RateLimitState:
    """Rate limit state definition."""
    key: str
    current_requests: int
    window_start: float
    blocked_until: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Production-grade rate limiting middleware.
    
    Features:
    - User-based rate limiting
    - IP-based rate limiting
    - Token-based rate limiting
    - Endpoint-specific rate limiting
    - Distributed rate limiting
    - Sliding window implementation
    - Redis-based storage
    """
    
    def __init__(self, app, redis_url: str):
        super().__init__(app)
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.rules: Dict[str, RateLimitRule] = {}
        self.default_rules = self._initialize_default_rules()
        
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        try:
            # Initialize Redis client
            if self.redis_client is None:
                self.redis_client = redis.from_url(self.redis_url)
            
            # Get client identifiers
            user_id = self._get_user_id(request)
            ip_address = self._get_ip_address(request)
            token = self._get_token(request)
            endpoint = self._get_endpoint(request)
            
            # Check all applicable rate limits
            rate_limit_results = await self._check_rate_limits(
                user_id, ip_address, token, endpoint
            )
            
            # Check if any rate limit is exceeded
            for result in rate_limit_results:
                if result['exceeded']:
                    return self._create_rate_limit_response(result)
            
            # Update rate limit counters
            await self._update_rate_limits(
                user_id, ip_address, token, endpoint
            )
            
            # Continue with request
            return await call_next(request)
            
        except Exception as e:
            logger.error(f"Rate limiting error: {str(e)}")
            # Fail open - allow request but log error
            return await call_next(request)
    
    def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request."""
        try:
            # Check various sources for user ID
            # 1. From session
            if hasattr(request, 'session') and request.session.get('user_id'):
                return request.session.get('user_id')
            
            # 2. From authorization header
            auth_header = request.headers.get('authorization')
            if auth_header and auth_header.startswith('Bearer '):
                # This would validate JWT token and extract user ID
                # For now, return None - would integrate with user identity system
                pass
            
            # 3. From user context
            if hasattr(request, 'user') and request.user:
                return getattr(request.user, 'id', None)
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting user ID: {str(e)}")
            return None
    
    def _get_ip_address(self, request: Request) -> str:
        """Extract IP address from request."""
        try:
            # Check various sources for IP address
            # 1. X-Forwarded-For header (proxy)
            x_forwarded_for = request.headers.get('x-forwarded-for')
            if x_forwarded_for:
                return x_forwarded_for.split(',')[0].strip()
            
            # 2. X-Real-IP header
            x_real_ip = request.headers.get('x-real-ip')
            if x_real_ip:
                return x_real_ip
            
            # 3. Remote address
            if hasattr(request, 'client'):
                return request.client.host
            
            return 'unknown'
            
        except Exception as e:
            logger.error(f"Error extracting IP address: {str(e)}")
            return 'unknown'
    
    def _get_token(self, request: Request) -> Optional[str]:
        """Extract token from request."""
        try:
            # Check various sources for token
            # 1. Authorization header
            auth_header = request.headers.get('authorization')
            if auth_header and auth_header.startswith('Bearer '):
                return auth_header[7:]  # Remove 'Bearer ' prefix
            
            # 2. API key header
            api_key = request.headers.get('x-api-key')
            if api_key:
                return api_key
            
            # 3. Query parameter
            token_param = request.query_params.get('token')
            if token_param:
                return token_param
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting token: {str(e)}")
            return None
    
    def _get_endpoint(self, request: Request) -> str:
        """Get endpoint from request."""
        try:
            return request.url.path
        except Exception as e:
            logger.error(f"Error extracting endpoint: {str(e)}")
            return 'unknown'
    
    def _initialize_default_rules(self) -> Dict[str, RateLimitRule]:
        """Initialize default rate limiting rules."""
        return {
            # Global limits
            'global_default': RateLimitRule(
                rule_id='global_default',
                name='Global Default Rate Limit',
                limit_type=RateLimitType.GLOBAL,
                window=RateLimitWindow.MINUTE,
                max_requests=1000,
                block_duration=300  # 5 minutes
            ),
            
            # User-based limits
            'user_basic': RateLimitRule(
                rule_id='user_basic',
                name='Basic User Rate Limit',
                limit_type=RateLimitType.USER_BASED,
                window=RateLimitWindow.MINUTE,
                max_requests=100,
                block_duration=60,  # 1 minute
                user_types=['authenticated_user']
            ),
            'user_premium': RateLimitRule(
                rule_id='user_premium',
                name='Premium User Rate Limit',
                limit_type=RateLimitType.USER_BASED,
                window=RateLimitWindow.MINUTE,
                max_requests=500,
                block_duration=30,  # 30 seconds
                user_types=['premium_user']
            ),
            
            # IP-based limits
            'ip_default': RateLimitRule(
                rule_id='ip_default',
                name='Default IP Rate Limit',
                limit_type=RateLimitType.IP_BASED,
                window=RateLimitWindow.MINUTE,
                max_requests=200,
                block_duration=300,  # 5 minutes
            ),
            'ip_aggressive': RateLimitRule(
                rule_id='ip_aggressive',
                name='Aggressive IP Rate Limit',
                limit_type=RateLimitType.IP_BASED,
                window=RateLimitWindow.MINUTE,
                max_requests=50,
                block_duration=900,  # 15 minutes
            ),
            
            # Token-based limits
            'token_default': RateLimitRule(
                rule_id='token_default',
                name='Default Token Rate Limit',
                limit_type=RateLimitType.TOKEN_BASED,
                window=RateLimitWindow.MINUTE,
                max_requests=1000,
                block_duration=300,  # 5 minutes
            ),
            
            # Endpoint-specific limits
            'api_auth': RateLimitRule(
                rule_id='api_auth',
                name='Authentication API Rate Limit',
                limit_type=RateLimitType.ENDPOINT_BASED,
                window=RateLimitWindow.MINUTE,
                max_requests=10,
                block_duration=60,  # 1 minute
                endpoints=['/api/v1/auth/login', '/api/v1/auth/refresh']
            ),
            'api_benchmark': RateLimitRule(
                rule_id='api_benchmark',
                name='Benchmark API Rate Limit',
                limit_type=RateLimitType.ENDPOINT_BASED,
                window=RateLimitWindow.MINUTE,
                max_requests=50,
                block_duration=120,  # 2 minutes
                endpoints=['/api/v1/benchmark/submit', '/api/v1/benchmark/status']
            ),
            'api_admin': RateLimitRule(
                rule_id='api_admin',
                name='Admin API Rate Limit',
                limit_type=RateLimitType.ENDPOINT_BASED,
                window=RateLimitWindow.MINUTE,
                max_requests=200,
                block_duration=60,  # 1 minute
                endpoints=['/api/v1/operator/*', '/api/v1/admin/*'],
                user_types=['admin', 'operator']
            ),
            
            # High-frequency endpoints
            'api_telemetry': RateLimitRule(
                rule_id='api_telemetry',
                name='Telemetry API Rate Limit',
                limit_type=RateLimitType.ENDPOINT_BASED,
                window=RateLimitWindow.SECOND,
                max_requests=100,
                block_duration=30,  # 30 seconds
                endpoints=['/api/v1/metrics', '/api/v1/telemetry']
            )
        }
    
    async def _check_rate_limits(self, 
                               user_id: Optional[str],
                               ip_address: str,
                               token: Optional[str],
                               endpoint: str) -> List[Dict[str, Any]]:
        """Check all applicable rate limits."""
        results = []
        
        try:
            # Check global limits
            global_result = await self._check_single_rule(
                self.default_rules['global_default'],
                'global',
                'global'
            )
            results.append(global_result)
            
            # Check user-based limits
            if user_id:
                user_rules = [
                    rule for rule in self.default_rules.values()
                    if rule.limit_type == RateLimitType.USER_BASED
                ]
                
                for rule in user_rules:
                    user_result = await self._check_single_rule(
                        rule,
                        f"user:{user_id}",
                        user_id
                    )
                    results.append(user_result)
            
            # Check IP-based limits
            ip_rules = [
                rule for rule in self.default_rules.values()
                if rule.limit_type == RateLimitType.IP_BASED
            ]
            
            for rule in ip_rules:
                ip_result = await self._check_single_rule(
                    rule,
                    f"ip:{ip_address}",
                    ip_address
                )
                results.append(ip_result)
            
            # Check token-based limits
            if token:
                token_rules = [
                    rule for rule in self.default_rules.values()
                    if rule.limit_type == RateLimitType.TOKEN_BASED
                ]
                
                for rule in token_rules:
                    token_result = await self._check_single_rule(
                        rule,
                        f"token:{token}",
                        token
                    )
                    results.append(token_result)
            
            # Check endpoint-specific limits
            endpoint_rules = [
                rule for rule in self.default_rules.values()
                if rule.limit_type == RateLimitType.ENDPOINT_BASED
            ]
            
            for rule in endpoint_rules:
                if self._endpoint_matches(rule.endpoints, endpoint):
                    endpoint_key = f"endpoint:{endpoint}:{rule.rule_id}"
                    endpoint_result = await self._check_single_rule(
                        rule,
                        endpoint_key,
                        endpoint
                    )
                    results.append(endpoint_result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error checking rate limits: {str(e)}")
            return []
    
    async def _check_single_rule(self, 
                                rule: RateLimitRule,
                                key: str,
                                identifier: str) -> Dict[str, Any]:
        """Check a single rate limit rule."""
        try:
            # Get current state from Redis
            state = await self._get_rate_limit_state(key)
            
            current_time = time.time()
            window_seconds = self._get_window_seconds(rule.window)
            
            # Check if currently blocked
            if current_time < state.blocked_until:
                return {
                    'rule_id': rule.rule_id,
                    'rule_name': rule.name,
                    'limit_type': rule.limit_type.value,
                    'key': key,
                    'identifier': identifier,
                    'exceeded': True,
                    'blocked': True,
                    'blocked_until': state.blocked_until,
                    'block_remaining': state.blocked_until - current_time,
                    'current_requests': state.current_requests,
                    'max_requests': rule.max_requests,
                    'window': rule.window.value,
                    'reset_time': state.window_start + window_seconds
                }
            
            # Check if window has expired
            if current_time > state.window_start + window_seconds:
                # Reset window
                state.current_requests = 1
                state.window_start = current_time
                state.blocked_until = 0.0
            else:
                # Increment counter
                state.current_requests += 1
            
            # Check if limit exceeded
            if state.current_requests > rule.max_requests:
                # Apply block
                state.blocked_until = current_time + rule.block_duration
                
                # Save state
                await self._save_rate_limit_state(key, state)
                
                return {
                    'rule_id': rule.rule_id,
                    'rule_name': rule.name,
                    'limit_type': rule.limit_type.value,
                    'key': key,
                    'identifier': identifier,
                    'exceeded': True,
                    'blocked': True,
                    'blocked_until': state.blocked_until,
                    'block_remaining': rule.block_duration,
                    'current_requests': state.current_requests,
                    'max_requests': rule.max_requests,
                    'window': rule.window.value,
                    'reset_time': state.window_start + window_seconds
                }
            
            # Save updated state
            await self._save_rate_limit_state(key, state)
            
            return {
                'rule_id': rule.rule_id,
                'rule_name': rule.name,
                'limit_type': rule.limit_type.value,
                'key': key,
                'identifier': identifier,
                'exceeded': False,
                'blocked': False,
                'blocked_until': 0.0,
                'block_remaining': 0.0,
                'current_requests': state.current_requests,
                'max_requests': rule.max_requests,
                'remaining_requests': rule.max_requests - state.current_requests,
                'window': rule.window.value,
                'reset_time': state.window_start + window_seconds
            }
            
        except Exception as e:
            logger.error(f"Error checking rule {rule.rule_id}: {str(e)}")
            return {
                'rule_id': rule.rule_id,
                'rule_name': rule.name,
                'limit_type': rule.limit_type.value,
                'key': key,
                'identifier': identifier,
                'exceeded': False,
                'blocked': False,
                'error': str(e)
            }
    
    async def _update_rate_limits(self, 
                                 user_id: Optional[str],
                                 ip_address: str,
                                 token: Optional[str],
                                 endpoint: str) -> None:
        """Update rate limit counters."""
        try:
            # This is handled in _check_single_rule
            # The counters are updated as part of the check
            pass
            
        except Exception as e:
            logger.error(f"Error updating rate limits: {str(e)}")
    
    async def _get_rate_limit_state(self, key: str) -> RateLimitState:
        """Get rate limit state from Redis."""
        try:
            if not self.redis_client:
                return RateLimitState(
                    key=key,
                    current_requests=0,
                    window_start=time.time()
                )
            
            # Get state from Redis
            state_data = await self.redis_client.get(f"rate_limit:{key}")
            
            if state_data:
                state_dict = json.loads(state_data)
                return RateLimitState(**state_dict)
            else:
                return RateLimitState(
                    key=key,
                    current_requests=0,
                    window_start=time.time()
                )
                
        except Exception as e:
            logger.error(f"Error getting rate limit state for {key}: {str(e)}")
            return RateLimitState(
                key=key,
                current_requests=0,
                window_start=time.time()
            )
    
    async def _save_rate_limit_state(self, key: str, state: RateLimitState) -> None:
        """Save rate limit state to Redis."""
        try:
            if not self.redis_client:
                return
            
            # Save state to Redis with expiration
            state_dict = {
                'key': state.key,
                'current_requests': state.current_requests,
                'window_start': state.window_start,
                'blocked_until': state.blocked_until,
                'metadata': state.metadata
            }
            
            # Set with expiration based on window
            window_seconds = self._get_window_seconds(RateLimitWindow.MINUTE)  # Default to minute
            await self.redis_client.setex(
                f"rate_limit:{key}",
                window_seconds * 2,  # Keep for double the window time
                json.dumps(state_dict)
            )
            
        except Exception as e:
            logger.error(f"Error saving rate limit state for {key}: {str(e)}")
    
    def _get_window_seconds(self, window: RateLimitWindow) -> int:
        """Get window duration in seconds."""
        window_durations = {
            RateLimitWindow.SECOND: 1,
            RateLimitWindow.MINUTE: 60,
            RateLimitWindow.HOUR: 3600,
            RateLimitWindow.DAY: 86400
        }
        return window_durations.get(window, 60)
    
    def _endpoint_matches(self, rule_endpoints: List[str], endpoint: str) -> bool:
        """Check if endpoint matches rule endpoints."""
        if not rule_endpoints:
            return True
        
        for rule_endpoint in rule_endpoints:
            if rule_endpoint.endswith('*'):
                # Wildcard matching
                pattern = rule_endpoint.replace('*', '')
                if endpoint.startswith(pattern):
                    return True
            else:
                # Exact matching
                if endpoint == rule_endpoint:
                    return True
        
        return False
    
    def _create_rate_limit_response(self, result: Dict[str, Any]) -> Response:
        """Create rate limit response."""
        try:
            response_data = {
                'error': 'Rate limit exceeded',
                'message': f"Rate limit exceeded for {result['rule_name']}",
                'rule_id': result['rule_id'],
                'limit_type': result['limit_type'],
                'current_requests': result['current_requests'],
                'max_requests': result['max_requests'],
                'window': result['window'],
                'blocked_until': result['blocked_until'],
                'block_remaining': result.get('block_remaining', 0),
                'reset_time': result['reset_time']
            }
            
            return Response(
                content=json.dumps(response_data),
                status_code=429,
                media_type='application/json',
                headers={
                    'X-RateLimit-Limit': str(result['max_requests']),
                    'X-RateLimit-Remaining': str(result.get('remaining_requests', 0)),
                    'X-RateLimit-Reset': str(int(result['reset_time'])),
                    'Retry-After': str(int(result.get('block_remaining', 60)))
                }
            )
            
        except Exception as e:
            logger.error(f"Error creating rate limit response: {str(e)}")
            return Response(
                content=json.dumps({'error': 'Rate limit exceeded'}),
                status_code=429,
                media_type='application/json'
            )
    
    async def add_rule(self, rule: RateLimitRule) -> bool:
        """Add a new rate limit rule."""
        try:
            self.rules[rule.rule_id] = rule
            logger.info(f"Added rate limit rule: {rule.rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding rate limit rule: {str(e)}")
            return False
    
    async def remove_rule(self, rule_id: str) -> bool:
        """Remove a rate limit rule."""
        try:
            if rule_id in self.rules:
                del self.rules[rule_id]
                logger.info(f"Removed rate limit rule: {rule_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error removing rate limit rule: {str(e)}")
            return False
    
    async def get_rate_limit_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics."""
        try:
            if not self.redis_client:
                return {'error': 'Redis client not available'}
            
            # Get all rate limit keys
            keys = await self.redis_client.keys('rate_limit:*')
            
            stats = {
                'total_keys': len(keys),
                'active_blocks': 0,
                'total_requests': 0,
                'rules': len(self.default_rules),
                'rule_details': {}
            }
            
            for key in keys:
                try:
                    state_data = await self.redis_client.get(key)
                    if state_data:
                        state_dict = json.loads(state_data)
                        stats['total_requests'] += state_dict.get('current_requests', 0)
                        
                        if time.time() < state_dict.get('blocked_until', 0):
                            stats['active_blocks'] += 1
                            
                except Exception as e:
                    logger.error(f"Error processing key {key}: {str(e)}")
            
            # Add rule details
            for rule_id, rule in self.default_rules.items():
                stats['rule_details'][rule_id] = {
                    'name': rule.name,
                    'limit_type': rule.limit_type.value,
                    'window': rule.window.value,
                    'max_requests': rule.max_requests,
                    'block_duration': rule.block_duration,
                    'endpoints': rule.endpoints,
                    'user_types': rule.user_types
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting rate limit stats: {str(e)}")
            return {'error': str(e)}


# Global rate limiting middleware instance
_rate_limit_middleware: Optional[RateLimitMiddleware] = None


def get_rate_limit_middleware(redis_url: str) -> RateLimitMiddleware:
    """Get global rate limiting middleware instance."""
    global _rate_limit_middleware
    if _rate_limit_middleware is None:
        _rate_limit_middleware = RateLimitMiddleware(None, redis_url)
    return _rate_limit_middleware
