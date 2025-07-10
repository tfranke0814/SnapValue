import json
import hashlib
import pickle
import gzip
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import threading

from app.core.config import settings
from app.utils.logging import get_logger
from app.utils.exceptions import ValidationError

logger = get_logger(__name__)

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    size_bytes: int = 0
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
    
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        return datetime.utcnow() > self.expires_at
    
    def access(self):
        """Record access to this entry"""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()

class ResultCache:
    """Advanced result caching system"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.tag_index: Dict[str, List[str]] = {}  # tag -> list of keys
        self.lock = threading.RLock()
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expired_removals': 0
        }
    
    def _generate_key(self, namespace: str, data: Dict) -> str:
        """Generate cache key from data"""
        try:
            # Create deterministic representation
            key_data = {
                'namespace': namespace,
                'data': self._normalize_data(data)
            }
            
            # Generate hash
            key_string = json.dumps(key_data, sort_keys=True)
            key_hash = hashlib.sha256(key_string.encode()).hexdigest()
            
            return f"{namespace}:{key_hash[:16]}"
            
        except Exception as e:
            logger.warning(f"Failed to generate cache key: {e}")
            return f"{namespace}:{datetime.utcnow().timestamp()}"
    
    def _normalize_data(self, data: Any) -> Any:
        """Normalize data for consistent hashing"""
        if isinstance(data, dict):
            # Sort dictionary and normalize values
            return {k: self._normalize_data(v) for k, v in sorted(data.items())}
        elif isinstance(data, list):
            # Normalize list elements
            return [self._normalize_data(item) for item in data]
        elif isinstance(data, float):
            # Round floats to reduce variations
            return round(data, 6)
        else:
            return data
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for storage"""
        try:
            # Use pickle for complex objects, compress for large data
            pickled = pickle.dumps(value)
            
            if len(pickled) > 1024:  # Compress if larger than 1KB
                return gzip.compress(pickled)
            else:
                return pickled
                
        except Exception as e:
            logger.error(f"Failed to serialize cache value: {e}")
            raise
    
    def _deserialize_value(self, data: bytes) -> Any:
        """Deserialize value from storage"""
        try:
            # Try decompression first
            try:
                decompressed = gzip.decompress(data)
                return pickle.loads(decompressed)
            except gzip.BadGzipFile:
                # Not compressed
                return pickle.loads(data)
                
        except Exception as e:
            logger.error(f"Failed to deserialize cache value: {e}")
            raise
    
    def _calculate_size(self, value: Any) -> int:
        """Calculate approximate size of value in bytes"""
        try:
            return len(self._serialize_value(value))
        except Exception:
            return 100  # Default size estimate
    
    def put(
        self,
        namespace: str,
        data: Dict,
        value: Any,
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Store value in cache
        
        Args:
            namespace: Cache namespace
            data: Data used to generate key
            value: Value to cache
            ttl: Time to live in seconds
            tags: Tags for categorization
            metadata: Additional metadata
            
        Returns:
            Cache key
        """
        with self.lock:
            try:
                key = self._generate_key(namespace, data)
                
                if ttl is None:
                    ttl = self.default_ttl
                
                # Create cache entry
                entry = CacheEntry(
                    key=key,
                    value=value,
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(seconds=ttl),
                    size_bytes=self._calculate_size(value),
                    tags=tags or [],
                    metadata=metadata or {}
                )
                
                # Store entry
                self.cache[key] = entry
                
                # Update tag index
                for tag in entry.tags:
                    if tag not in self.tag_index:
                        self.tag_index[tag] = []
                    if key not in self.tag_index[tag]:
                        self.tag_index[tag].append(key)
                
                # Cleanup if needed
                self._cleanup_if_needed()
                
                logger.debug(f"Cached value with key: {key}")
                
                return key
                
            except Exception as e:
                logger.error(f"Failed to cache value: {e}")
                raise
    
    def get(self, namespace: str, data: Dict) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            namespace: Cache namespace
            data: Data used to generate key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self.lock:
            try:
                key = self._generate_key(namespace, data)
                
                if key not in self.cache:
                    self.stats['misses'] += 1
                    return None
                
                entry = self.cache[key]
                
                # Check if expired
                if entry.is_expired():
                    self._remove_entry(key)
                    self.stats['misses'] += 1
                    self.stats['expired_removals'] += 1
                    return None
                
                # Record access and return value
                entry.access()
                self.stats['hits'] += 1
                
                logger.debug(f"Cache hit for key: {key}")
                
                return entry.value
                
            except Exception as e:
                logger.error(f"Failed to get cached value: {e}")
                self.stats['misses'] += 1
                return None
    
    def get_by_key(self, key: str) -> Optional[Any]:
        """Get value by exact key"""
        with self.lock:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            
            if entry.is_expired():
                self._remove_entry(key)
                return None
            
            entry.access()
            return entry.value
    
    def invalidate(self, namespace: str, data: Dict) -> bool:
        """Invalidate specific cache entry"""
        with self.lock:
            try:
                key = self._generate_key(namespace, data)
                
                if key in self.cache:
                    self._remove_entry(key)
                    logger.debug(f"Invalidated cache key: {key}")
                    return True
                
                return False
                
            except Exception as e:
                logger.error(f"Failed to invalidate cache: {e}")
                return False
    
    def invalidate_by_tag(self, tag: str) -> int:
        """Invalidate all entries with a specific tag"""
        with self.lock:
            count = 0
            
            if tag in self.tag_index:
                keys_to_remove = self.tag_index[tag].copy()
                
                for key in keys_to_remove:
                    if key in self.cache:
                        self._remove_entry(key)
                        count += 1
                
                logger.info(f"Invalidated {count} cache entries with tag: {tag}")
            
            return count
    
    def invalidate_namespace(self, namespace: str) -> int:
        """Invalidate all entries in a namespace"""
        with self.lock:
            count = 0
            prefix = f"{namespace}:"
            
            keys_to_remove = [key for key in self.cache.keys() if key.startswith(prefix)]
            
            for key in keys_to_remove:
                self._remove_entry(key)
                count += 1
            
            logger.info(f"Invalidated {count} cache entries in namespace: {namespace}")
            
            return count
    
    def _remove_entry(self, key: str):
        """Remove entry and update indexes"""
        if key not in self.cache:
            return
        
        entry = self.cache[key]
        
        # Remove from tag index
        for tag in entry.tags:
            if tag in self.tag_index and key in self.tag_index[tag]:
                self.tag_index[tag].remove(key)
                
                # Clean up empty tag lists
                if not self.tag_index[tag]:
                    del self.tag_index[tag]
        
        # Remove from cache
        del self.cache[key]
    
    def _cleanup_if_needed(self):
        """Clean up cache if it exceeds size limits"""
        if len(self.cache) <= self.max_size:
            return
        
        # Remove expired entries first
        expired_keys = [key for key, entry in self.cache.items() if entry.is_expired()]
        
        for key in expired_keys:
            self._remove_entry(key)
            self.stats['expired_removals'] += 1
        
        # If still over limit, remove least recently used
        if len(self.cache) > self.max_size:
            # Sort by last accessed time (None values last)
            sorted_entries = sorted(
                self.cache.items(),
                key=lambda x: x[1].last_accessed or datetime.min
            )
            
            # Remove oldest entries
            excess_count = len(self.cache) - self.max_size
            
            for key, _ in sorted_entries[:excess_count]:
                self._remove_entry(key)
                self.stats['evictions'] += 1
        
        logger.debug(f"Cache cleanup completed. Current size: {len(self.cache)}")
    
    def cleanup_expired(self):
        """Remove all expired entries"""
        with self.lock:
            expired_keys = [key for key, entry in self.cache.items() if entry.is_expired()]
            
            for key in expired_keys:
                self._remove_entry(key)
                self.stats['expired_removals'] += 1
            
            if expired_keys:
                logger.info(f"Removed {len(expired_keys)} expired cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            total_size = sum(entry.size_bytes for entry in self.cache.values())
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hit_rate_percent': round(hit_rate, 2),
                'total_hits': self.stats['hits'],
                'total_misses': self.stats['misses'],
                'evictions': self.stats['evictions'],
                'expired_removals': self.stats['expired_removals'],
                'total_size_bytes': total_size,
                'tags_count': len(self.tag_index)
            }
    
    def get_entries_by_tag(self, tag: str) -> List[CacheEntry]:
        """Get all cache entries with a specific tag"""
        with self.lock:
            if tag not in self.tag_index:
                return []
            
            entries = []
            for key in self.tag_index[tag]:
                if key in self.cache:
                    entries.append(self.cache[key])
            
            return entries
    
    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.tag_index.clear()
            
            # Reset stats
            self.stats = {
                'hits': 0,
                'misses': 0,
                'evictions': 0,
                'expired_removals': 0
            }
            
            logger.info("Cache cleared")

# Global cache instances
appraisal_cache = ResultCache(max_size=500, default_ttl=settings.CACHE_TTL)
market_cache = ResultCache(max_size=1000, default_ttl=settings.CACHE_TTL * 2)  # Longer TTL for market data
ai_cache = ResultCache(max_size=300, default_ttl=settings.CACHE_TTL * 3)  # Even longer for AI results

# Utility functions
def cache_appraisal_result(
    appraisal_data: Dict,
    result: Any,
    ttl: Optional[int] = None,
    tags: Optional[List[str]] = None
) -> str:
    """Cache appraisal result"""
    return appraisal_cache.put(
        namespace="appraisal",
        data=appraisal_data,
        value=result,
        ttl=ttl,
        tags=tags or ["appraisal"]
    )

def get_cached_appraisal(appraisal_data: Dict) -> Optional[Any]:
    """Get cached appraisal result"""
    return appraisal_cache.get("appraisal", appraisal_data)

def cache_market_analysis(
    market_data: Dict,
    result: Any,
    ttl: Optional[int] = None,
    tags: Optional[List[str]] = None
) -> str:
    """Cache market analysis result"""
    return market_cache.put(
        namespace="market",
        data=market_data,
        value=result,
        ttl=ttl,
        tags=tags or ["market"]
    )

def get_cached_market_analysis(market_data: Dict) -> Optional[Any]:
    """Get cached market analysis result"""
    return market_cache.get("market", market_data)

def cache_ai_analysis(
    ai_data: Dict,
    result: Any,
    ttl: Optional[int] = None,
    tags: Optional[List[str]] = None
) -> str:
    """Cache AI analysis result"""
    return ai_cache.put(
        namespace="ai",
        data=ai_data,
        value=result,
        ttl=ttl,
        tags=tags or ["ai"]
    )

def get_cached_ai_analysis(ai_data: Dict) -> Optional[Any]:
    """Get cached AI analysis result"""
    return ai_cache.get("ai", ai_data)

def invalidate_user_cache(user_id: str):
    """Invalidate all cache entries for a user"""
    count = 0
    count += appraisal_cache.invalidate_by_tag(f"user_{user_id}")
    count += market_cache.invalidate_by_tag(f"user_{user_id}")
    count += ai_cache.invalidate_by_tag(f"user_{user_id}")
    
    logger.info(f"Invalidated {count} cache entries for user {user_id}")

def cleanup_all_caches():
    """Clean up expired entries in all caches"""
    appraisal_cache.cleanup_expired()
    market_cache.cleanup_expired()
    ai_cache.cleanup_expired()

def get_all_cache_stats() -> Dict[str, Any]:
    """Get statistics for all caches"""
    return {
        'appraisal_cache': appraisal_cache.get_stats(),
        'market_cache': market_cache.get_stats(),
        'ai_cache': ai_cache.get_stats()
    }

def clear_all_caches():
    """Clear all caches"""
    appraisal_cache.clear()
    market_cache.clear()
    ai_cache.clear()
    
    logger.info("All caches cleared")

# Cache decorator for functions
def cached_result(
    cache_instance: ResultCache,
    namespace: str,
    ttl: Optional[int] = None,
    tags: Optional[List[str]] = None,
    key_args: Optional[List[str]] = None
):
    """Decorator for caching function results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key from specified arguments
            cache_data = {}
            
            if key_args:
                for i, arg_name in enumerate(key_args):
                    if i < len(args):
                        cache_data[arg_name] = args[i]
                    elif arg_name in kwargs:
                        cache_data[arg_name] = kwargs[arg_name]
            else:
                # Use all arguments
                cache_data = {f"arg_{i}": arg for i, arg in enumerate(args)}
                cache_data.update(kwargs)
            
            # Try to get from cache
            cached_value = cache_instance.get(namespace, cache_data)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache_instance.put(namespace, cache_data, result, ttl, tags)
            
            return result
        
        return wrapper
    return decorator