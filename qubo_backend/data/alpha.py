from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AlphaData:
    mu: np.ndarray
    sigma: np.ndarray
    tickers: list[str]
    sectors: list[str]


def load_alpha_data(output_dir: Path) -> AlphaData:
    path = output_dir / "alpha_data.npz"
    if not path.exists():
        logger.warning("Alpha data file missing: %s", path)
        logger.info("Attempting to generate alpha data automatically...")
        try:
            from generate_alpha import generate_nifty50_alpha
            generated_path = generate_nifty50_alpha(output_dir=output_dir, force=False)
            logger.info("Alpha data generated successfully: %s", generated_path)
        except ImportError:
            logger.error("Cannot import generate_alpha module for auto-generation")
            raise FileNotFoundError(f"Missing alpha data artifact: {path}")
        except Exception as e:
            logger.error("Auto-generation of alpha data failed: %s", e)
            raise FileNotFoundError(f"Missing alpha data artifact: {path}. Auto-generation failed: {e}")

    data = np.load(path, allow_pickle=True)
    mu = np.asarray(data["mu"], dtype=float)
    sigma = np.asarray(data["sigma"], dtype=float)
    tickers = [str(item) for item in data["tickers"].tolist()]
    sectors = [str(item) for item in data["sectors"].tolist()]

    if sigma.shape != (len(mu), len(mu)):
        raise ValueError(f"Covariance shape {sigma.shape} does not match mu length {len(mu)}")
    if len(tickers) != len(mu) or len(sectors) != len(mu):
        raise ValueError("Ticker/sector metadata does not match alpha vector length")

    logger.info("Alpha data loaded: %d assets from %s", len(mu), path)
    return AlphaData(mu=mu, sigma=sigma, tickers=tickers, sectors=sectors)

