from qubo_backend.config import Settings

def dwave_status(settings: Settings) -> str:
    try:
        import dwave.system  # noqa: F401
    except ImportError:
        return "not_installed"
    if not settings.dwave_api_token:
        return "missing_token"
    return "configured"
