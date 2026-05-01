from functools import wraps
from time import time
from flask import g, request
from tuned.redis_client import redis_client
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Optional, Dict, List, Union, Callable, cast


class MetricsCollector:
    @staticmethod
    def track_request(endpoint: str) -> Callable[..., Any]:
        def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(f)
            def decorated_function(*args: Any, **kwargs: Any) -> Any:
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
    def _record_request(endpoint: str, method: str, status_code: int, duration_ms: float, success: bool, error: Optional[str] = None) -> None:
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
            redis_client.lpush(f'metrics:duration:{endpoint}', float(duration_ms))
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
    def track_cache_hit(cache_key: str) -> None:
        try:
            if not redis_client:
                return
            
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            redis_client.hincrby(f'metrics:cache:{today}', 'hits', 1)
            redis_client.expire(f'metrics:cache:{today}', 604800)
        except:
            pass
    
    @staticmethod
    def track_cache_miss(cache_key: str) -> None:
        try:
            if not redis_client:
                return
            
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            redis_client.hincrby(f'metrics:cache:{today}', 'misses', 1)
            redis_client.expire(f'metrics:cache:{today}', 604800)
        except:
            pass
    
    @staticmethod
    def track_search(query: str, search_type: str, result_count: int) -> None:
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
    def get_endpoint_metrics(endpoint: str, days: int = 7) -> Optional[Dict[str, Any]]:
        try:
            if not redis_client:
                return None
            
            metrics_data: Dict[str, Any] = {
                'endpoint': endpoint,
                'requests': {},
                'errors': {},
                'avg_duration_ms': 0.0
            }
            
            # Collect data for last N days
            for i in range(days):
                date = (datetime.now(timezone.utc) - timedelta(days=i)).strftime('%Y-%m-%d')
                
                # Get request count
                count = cast(Any, redis_client.hget(f'metrics:requests:{date}', endpoint))
                if count:
                    metrics_data['requests'][date] = int(count)
                
                # Get error count
                errors = cast(Any, redis_client.hget(f'metrics:errors:{date}', endpoint))
                if errors:
                    metrics_data['errors'][date] = int(errors)
            
            # Get average duration
            durations: List[Any] = cast(Any, redis_client.lrange(f'metrics:duration:{endpoint}', 0, -1))
            if durations:
                avg_duration = sum(float(d) for d in durations) / len(durations)
                metrics_data['avg_duration_ms'] = round(avg_duration, 2)
            
            return metrics_data
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def get_cache_metrics(days: int = 7) -> Optional[Dict[str, Any]]:
        try:
            if not redis_client:
                return None
            
            metrics_data: Dict[str, Any] = {
                'daily': {},
                'total_hits': 0,
                'total_misses': 0,
                'hit_rate': 0.0
            }
            
            for i in range(days):
                date = (datetime.now(timezone.utc) - timedelta(days=i)).strftime('%Y-%m-%d')
                
                hits_raw = cast(Any, redis_client.hget(f'metrics:cache:{date}', 'hits'))
                misses_raw = cast(Any, redis_client.hget(f'metrics:cache:{date}', 'misses'))
                
                if hits_raw or misses_raw:
                    hits: int = int(hits_raw) if hits_raw else 0
                    misses: int = int(misses_raw) if misses_raw else 0
                    
                    metrics_data['daily'][date] = {
                        'hits': hits,
                        'misses': misses,
                        'hit_rate': round((hits / (hits + misses) * 100), 2) if (hits + misses) > 0 else 0
                    }
                    
                    metrics_data['total_hits'] += hits
                    metrics_data['total_misses'] += misses
            
            # Calculate overall hit rate
            total = metrics_data['total_hits'] + metrics_data['total_misses']
            if total > 0:
                metrics_data['hit_rate'] = round((metrics_data['total_hits'] / total * 100), 2)
            
            return metrics_data
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def get_search_analytics(days: int = 7, top_n: int = 20) -> Optional[Dict[str, Any]]:
        try:
            if not redis_client:
                return None
            
            metrics_data: Dict[str, Any] = {
                'daily_totals': {},
                'popular_queries': [],
                'zero_result_queries': []
            }
            
            for i in range(days):
                date = (datetime.now(timezone.utc) - timedelta(days=i)).strftime('%Y-%m-%d')
                
                total = cast(Any, redis_client.hget(f'metrics:search:{date}', 'total'))
                zero_results = cast(Any, redis_client.hget(f'metrics:search:{date}', 'zero_results'))
                
                if total:
                    metrics_data['daily_totals'][date] = {
                        'total': int(total),
                        'zero_results': int(zero_results) if zero_results else 0
                    }
            
            popular = cast(Any, redis_client.zrevrange(f'metrics:search:popular', 0, top_n - 1, withscores=True))
            metrics_data['popular_queries'] = [
                {'query': query.decode('utf-8') if isinstance(query, bytes) else query, 'count': int(score)}
                for query, score in popular
            ]
            
            zero_queries = cast(Any, redis_client.zrevrange(f'metrics:search:zero_queries', 0, top_n - 1, withscores=True))
            metrics_data['zero_result_queries'] = [
                {'query': query.decode('utf-8') if isinstance(query, bytes) else query, 'count': int(score)}
                for query, score in zero_queries
            ]
            
            return metrics_data
            
        except Exception as e:
            return {'error': str(e)}

metrics = MetricsCollector()
