from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        return False


load_dotenv()


BASE_DIR = Path(__file__).resolve().parents[1]
_KNOWN_SECRETS: set[str] = set()


def _resolve_path(value: str, base: Path = BASE_DIR) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (base / path).resolve()


@dataclass(frozen=True)
class Settings:
    output_dir: Path
    checkpoint_dir: Path
    cors_origins: list[str]
    api_host: str
    api_port: int
    default_cardinality: int
    default_bits: int
    default_max_sector: float
    default_risk_tolerance: float
    default_solver: str
    default_trajectories: int
    jobs_dir: Path
    database_url: str
    artifact_backend: str
    quantum_enabled: bool
    dwave_api_token: str | None
    dwave_api_endpoint: str | None
    ibm_quantum_token: str | None
    ibm_quantum_apikey_file: Path | None
    qiskit_max_assets: int
    qiskit_max_binary_bits: int
    braket_max_assets: int
    braket_max_binary_bits: int
    braket_enabled: bool


def get_settings() -> Settings:
    output_dir = _resolve_path(os.getenv("OUTPUT_DIR", "../output"))
    checkpoint_dir = _resolve_path(os.getenv("CHECKPOINT_DIR", "./checkpoints"))
    jobs_dir = _resolve_path(os.getenv("JOBS_DIR", str(output_dir / "jobs")))
    cors_origins = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]
    ibm_key_file_value = os.getenv("IBM_QUANTUM_APIKEY_FILE", "").strip()
    ibm_key_file = _resolve_path(ibm_key_file_value) if ibm_key_file_value else None
    ibm_token = os.getenv("IBM_QUANTUM_TOKEN", "").strip() or _load_ibm_token_file(ibm_key_file)
    return Settings(
        output_dir=output_dir,
        checkpoint_dir=checkpoint_dir,
        cors_origins=cors_origins,
        api_host=os.getenv("API_HOST", "0.0.0.0"),
        api_port=int(os.getenv("API_PORT", "8000")),
        default_cardinality=int(os.getenv("DEFAULT_CARDINALITY", "3")),
        default_bits=int(os.getenv("DEFAULT_BITS", "1")),
        default_max_sector=float(os.getenv("DEFAULT_MAX_SECTOR", "0.7")),
        default_risk_tolerance=float(os.getenv("DEFAULT_RISK_TOLERANCE", "0.5")),
        default_solver=os.getenv("DEFAULT_SOLVER", "sb"),
        default_trajectories=int(os.getenv("DEFAULT_TRAJECTORIES", "256")),
        jobs_dir=jobs_dir,
        database_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./qubo_portfolio.db"),
        artifact_backend=os.getenv("ARTIFACT_BACKEND", "local"),
        quantum_enabled=os.getenv("QUANTUM_ENABLED", "false").lower() in {"1", "true", "yes"},
        dwave_api_token=os.getenv("DWAVE_API_TOKEN", "").strip() or None,
        dwave_api_endpoint=os.getenv("DWAVE_API_ENDPOINT", "").strip() or None,
        ibm_quantum_token=ibm_token,
        ibm_quantum_apikey_file=ibm_key_file,
        qiskit_max_assets=int(os.getenv("QISKIT_MAX_ASSETS", "10")),
        qiskit_max_binary_bits=int(os.getenv("QISKIT_MAX_BINARY_BITS", "3")),
        braket_max_assets=int(os.getenv("BRAKET_MAX_ASSETS", "8")),
        braket_max_binary_bits=int(os.getenv("BRAKET_MAX_BINARY_BITS", "3")),
        braket_enabled=os.getenv("BRAKET_ENABLED", "true").lower() in {"1", "true", "yes"},
    )


def _load_ibm_token_file(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    token = str(payload.get("apikey") or payload.get("token") or "").strip()
    if token:
        _KNOWN_SECRETS.add(token)
    return token or None


def redact_secret(value: object) -> str:
    text = str(value)
    for secret in (
        os.getenv("DWAVE_API_TOKEN", "").strip(),
        os.getenv("IBM_QUANTUM_TOKEN", "").strip(),
    ):
        if secret and secret in text:
            text = text.replace(secret, "[redacted]")
    for secret in _KNOWN_SECRETS:
        if secret and secret in text:
            text = text.replace(secret, "[redacted]")
    return text
