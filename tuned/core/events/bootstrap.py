import threading

_lock = threading.Lock()
_initialized = False

def init_events() -> None:
    global _initialized
    with _lock:
        if _initialized:
            return
        _initialized = True
    
    from tuned.core.events.registry import register_all_handlers
    register_all_handlers()