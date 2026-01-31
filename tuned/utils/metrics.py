"""
Performance metrics tracking utility.

Provides decorators and utilities for tracking:
- Request/response metrics
- Cache hit/miss rates
- Search query analytics
- Error rates
"""
from functools import wraps
from time import time
from flask import g, request
from tuned.redis_client import redis_client
import json
from datetime import datetime, timezone


class MetricsCollector:
    """Collects and stores application metrics"""
    
    @staticmethod
    def track_request(endpoint):
        """
        Decorator to track request metrics for an endpoint.
        
        Usage:
            @metrics.track_request('/api/blogs')
            def get_blogs():
                ...
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                start_time = time()
                
                try:
                    response = f(*args, **kwargs)
                    duration_ms = (time() - start_time) * 1000
                    
                    # Track successful request
                    MetricsCollector._record_request(
                        endpoint=endpoint,
                        method=request.method,
                        status_code=getattr(response, 'status_code', 200),
                        duration_ms=duration_ms,
                        success=True
                    )
                    
                    return response
                except Exception as e:
                    duration_ms = (time() - start_time) * 1000
                    
                    # Track failed request
                    MetricsCollector._record_request(
                        endpoint=endpoint,
                        method=request.method,
                        status_code=500,
                        duration_ms=duration_ms,
                        success=False,
                        error=str(e)
                    )
                    
                    raise
            
            return decorated_function
        return decorator
    
    @staticmethod
    def _record_request(endpoint, method, status_code, duration_ms, success, error=None):
        """Record request metrics in Redis"""
        try:
            if not redis_client:
                return
            
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            hour = datetime.now(timezone.utc).strftime('%H')
            
            # Increment request counter
            redis_client.hincrby(f'metrics:requests:{today}', endpoint, 1)
            redis_client.hincrby(f'metrics:requests:{today}:method', f'{endpoint}:{method}', 1)
            redis_client.hincrby(f'metrics:requests:{today}:status', f'{endpoint}:{status_code}', 1)
            
            # Track response times (store in list, limit to last 100)
            redis_client.lpush(f'metrics:duration:{endpoint}', duration_ms)
            redis_client.ltrim(f'metrics:duration:{endpoint}', 0, 99)
            
            # Track errors
            if not success:
                redis_client.hincrby(f'metrics:errors:{today}', endpoint, 1)
                if error:
                    redis_client.lpush(f'metrics:error_log:{endpoint}', json.dumps({
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'error': error,
                        'status_code': status_code
                    }))
                    redis_client.ltrim(f'metrics:error_log:{endpoint}', 0, 49)  # Keep last 50
            
            # Set expiry on daily keys (7 days)
            redis_client.expire(f'metrics:requests:{today}', 604800)
            redis_client.expire(f'metrics:errors:{today}', 604800)
            
        except Exception as e:
            # Silently fail - metrics shouldn't break the app
            print(f"Error recording metrics: {str(e)}")
    
    @staticmethod
    def track_cache_hit(cache_key):
        """Track cache hit"""
        try:
            if not redis_client:
                return
            
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            redis_client.hincrby(f'metrics:cache:{today}', 'hits', 1)
            redis_client.expire(f'metrics:cache:{today}', 604800)
        except:
            pass
    
    @staticmethod
    def track_cache_miss(cache_key):
        """Track cache miss"""
        try:
            if not redis_client:
                return
            
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            redis_client.hincrby(f'metrics:cache:{today}', 'misses', 1)
            redis_client.expire(f'metrics:cache:{today}', 604800)
        except:
            pass
    
    @staticmethod
    def track_search(query, search_type, result_count):
        """Track search query analytics"""
        try:
            if not redis_client:
                return
            
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            
            # Increment search counter
            redis_client.hincrby(f'metrics:search:{today}', 'total', 1)
            
            # Track by type
            if search_type:
                redis_client.hincrby(f'metrics:search:{today}:type', search_type, 1)
            
            # Track zero-result searches
            if result_count == 0:
                redis_client.hincrby(f'metrics:search:{today}', 'zero_results', 1)
                redis_client.zincrby(f'metrics:search:zero_queries', 1, query.lower())
            
            # Track popular queries (sorted set with scores)
            redis_client.zincrby(f'metrics:search:popular', 1, query.lower())
            
            # Set expiry
            redis_client.expire(f'metrics:search:{today}', 604800)
            redis_client.expire(f'metrics:search:{today}:type', 604800)
            
        except:
            pass
    
    @staticmethod
    def get_endpoint_metrics(endpoint, days=7):
        """Get metrics for a specific endpoint"""
        try:
            if not redis_client:
                return None
            
            from datetime import timedelta
            
            metrics = {
                'endpoint': endpoint,
                'requests': {},
                'errors': {},
                'avg_duration_ms': 0
            }
            
            # Collect data for last N days
            for i in range(days):
                date = (datetime.now(timezone.utc) - timedelta(days=i)).strftime('%Y-%m-%d')
                
                # Get request count
                count = redis_client.hget(f'metrics:requests:{date}', endpoint)
                if count:
                    metrics['requests'][date] = int(count)
                
                # Get error count
                errors = redis_client.hget(f'metrics:errors:{date}', endpoint)
                if errors:
                    metrics['errors'][date] = int(errors)
            
            # Get average duration
            durations = redis_client.lrange(f'metrics:duration:{endpoint}', 0, -1)
            if durations:
                avg_duration = sum(float(d) for d in durations) / len(durations)
                metrics['avg_duration_ms'] = round(avg_duration, 2)
            
            return metrics
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def get_cache_metrics(days=7):
        """Get cache hit/miss statistics"""
        try:
            if not redis_client:
                return None
            
            from datetime import timedelta
            
            metrics = {
                'daily': {},
                'total_hits': 0,
                'total_misses': 0,
                'hit_rate': 0
            }
            
            for i in range(days):
                date = (datetime.now(timezone.utc) - timedelta(days=i)).strftime('%Y-%m-%d')
                
                hits = redis_client.hget(f'metrics:cache:{date}', 'hits')
                misses = redis_client.hget(f'metrics:cache:{date}', 'misses')
                
                if hits or misses:
                    hits = int(hits) if hits else 0
                    misses = int(misses) if misses else 0
                    
                    metrics['daily'][date] = {
                        'hits': hits,
                        'misses': misses,
                        'hit_rate': round((hits / (hits + misses) * 100), 2) if (hits + misses) > 0 else 0
                    }
                    
                    metrics['total_hits'] += hits
                    metrics['total_misses'] += misses
            
            # Calculate overall hit rate
            total = metrics['total_hits'] + metrics['total_misses']
            if total > 0:
                metrics['hit_rate'] = round((metrics['total_hits'] / total * 100), 2)
            
            return metrics
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def get_search_analytics(days=7, top_n=20):
        """Get search analytics"""
        try:
            if not redis_client:
                return None
            
            from datetime import timedelta
            
            metrics = {
                'daily_totals': {},
                'popular_queries': [],
                'zero_result_queries': []
            }
            
            # Get daily totals
            for i in range(days):
                date = (datetime.now(timezone.utc) - timedelta(days=i)).strftime('%Y-%m-%d')
                
                total = redis_client.hget(f'metrics:search:{date}', 'total')
                zero_results = redis_client.hget(f'metrics:search:{date}', 'zero_results')
                
                if total:
                    metrics['daily_totals'][date] = {
                        'total': int(total),
                        'zero_results': int(zero_results) if zero_results else 0
                    }
            
            # Get popular queries
            popular = redis_client.zrevrange(f'metrics:search:popular', 0, top_n - 1, withscores=True)
            metrics['popular_queries'] = [
                {'query': query.decode('utf-8') if isinstance(query, bytes) else query, 'count': int(score)}
                for query, score in popular
            ]
            
            # Get zero-result queries
            zero_queries = redis_client.zrevrange(f'metrics:search:zero_queries', 0, top_n - 1, withscores=True)
            metrics['zero_result_queries'] = [
                {'query': query.decode('utf-8') if isinstance(query, bytes) else query, 'count': int(score)}
                for query, score in zero_queries
            ]
            
            return metrics
            
        except Exception as e:
            return {'error': str(e)}


# Create global instance
metrics = MetricsCollector()
