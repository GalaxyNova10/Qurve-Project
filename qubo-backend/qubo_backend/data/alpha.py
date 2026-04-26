from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class AlphaData:
    mu: np.ndarray
    sigma: np.ndarray
    tickers: list[str]
    sectors: list[str]


def load_alpha_data(output_dir: Path) -> AlphaData:
    path = output_dir / "alpha_data.npz"
    if not path.exists():
        raise FileNotFoundError(f"Missing alpha data artifact: {path}")

    data = np.load(path, allow_pickle=True)
    mu = np.asarray(data["mu"], dtype=float)
    sigma = np.asarray(data["sigma"], dtype=float)
    tickers = [str(item) for item in data["tickers"].tolist()]
    sectors = [str(item) for item in data["sectors"].tolist()]

    if sigma.shape != (len(mu), len(mu)):
        raise ValueError(f"Covariance shape {sigma.shape} does not match mu length {len(mu)}")
    if len(tickers) != len(mu) or len(sectors) != len(mu):
        raise ValueError("Ticker/sector metadata does not match alpha vector length")

    return AlphaData(mu=mu, sigma=sigma, tickers=tickers, sectors=sectors)

