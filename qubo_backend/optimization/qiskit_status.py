from qubo_backend.config import Settings

def qiskit_status(settings: Settings) -> str:
    try:
        import qiskit_optimization  # noqa: F401
    except ImportError:
        return "not_installed"
    return "available_with_ibm_token" if settings.ibm_quantum_token else "available_local"
