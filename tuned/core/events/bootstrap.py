_initialized = False

def init_events():
    global _initialized
    if _initialized:
        return

    from tuned.core.events.registry import register_all_handlers
    register_all_handlers()
    _initialized = True