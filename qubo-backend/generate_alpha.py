"""Alpha data generation pipeline for QUBO Portfolio Optimizer.

Generates synthetic NIFTY 50 alpha vectors and covariance matrices
for benchmark and optimization workflows.

Usage:
    python generate_alpha.py              # Generate with defaults
    python generate_alpha.py --force      # Regenerate even if exists
    python generate_alpha.py --output /custom/path  # Custom output dir
"""

import logging
import argparse
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

# NIFTY 50 universe
NIFTY50_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "HUL.NS",
    "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "BAJFINANCE.NS", "LICINDIA.NS", "KOTAKBANK.NS",
    "LT.NS", "HCLTECH.NS", "ASIANPAINT.NS", "AXISBANK.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "TITAN.NS", "BAJAJFINSV.NS", "ULTRACEMCO.NS", "ONGC.NS", "WIPRO.NS", "NTPC.NS",
    "NESTLEIND.NS", "POWERGRID.NS", "M&M.NS", "ADANIENT.NS", "TATASTEEL.NS", "TATAMOTORS.NS",
    "HINDALCO.NS", "JSWSTEEL.NS", "TECHM.NS", "GRASIM.NS", "SBILIFE.NS", "HDFCLIFE.NS",
    "INDUSINDBK.NS", "DIVISLAB.NS", "DRREDDY.NS", "CIPLA.NS", "BPCL.NS", "BRITANNIA.NS",
    "EICHERMOT.NS", "COALINDIA.NS", "APOLLOHOSP.NS", "HEROMOTOCO.NS", "UPL.NS", "BAJAJ-AUTO.NS",
    "TATACONSUM.NS", "LTIM.NS"
]

NIFTY50_SECTORS = [
    "Energy", "IT", "Financials", "IT", "Financials", "Consumer Staples",
    "Consumer Staples", "Financials", "Telecommunication", "Financials", "Financials", "Financials",
    "Industrials", "IT", "Materials", "Financials", "Consumer Discretionary", "Healthcare",
    "Consumer Discretionary", "Financials", "Materials", "Energy", "IT", "Utilities",
    "Consumer Staples", "Utilities", "Consumer Discretionary", "Industrials", "Materials", "Consumer Discretionary",
    "Materials", "Materials", "IT", "Materials", "Financials", "Financials",
    "Financials", "Healthcare", "Healthcare", "Healthcare", "Energy", "Consumer Staples",
    "Consumer Discretionary", "Energy", "Healthcare", "Consumer Discretionary", "Materials", "Consumer Discretionary",
    "Consumer Staples", "IT"
]


def generate_nifty50_alpha(output_dir: Path | None = None, seed: int = 42, force: bool = False) -> Path:
    """Generate synthetic NIFTY 50 alpha data and save to NPZ file.

    Args:
        output_dir: Directory to save the file. Defaults to project output/
        seed: Random seed for reproducibility
        force: If True, regenerate even if file exists

    Returns:
        Path to the generated alpha_data.npz file
    """
    if output_dir is None:
        output_dir = Path(__file__).resolve().parent.parent / "output"

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "alpha_data.npz"

    if output_path.exists() and not force:
        logger.info("Alpha data already exists at %s (use --force to regenerate)", output_path)
        return output_path

    logger.info("Generating synthetic NIFTY 50 alpha data...")
    logger.info("Universe: %d assets", len(NIFTY50_TICKERS))

    tickers = NIFTY50_TICKERS
    sectors = NIFTY50_SECTORS
    n = len(tickers)

    np.random.seed(seed)

    # Generate synthetic expected returns (mu) between -5% and +25%
    mu = np.random.uniform(-0.05, 0.25, n)
    logger.info("Expected returns range: [%.4f, %.4f]", mu.min(), mu.max())

    # Generate synthetic covariance matrix (sigma)
    # Start with a random positive semi-definite matrix
    A = np.random.randn(n, n)
    sigma = A @ A.T

    # Scale the covariance matrix so volatilities are between 10% and 40%
    # Volatility is sqrt(variance), so variance is between 0.01 and 0.16
    vars_target = np.random.uniform(0.01, 0.16, n)
    d = np.sqrt(vars_target / np.diag(sigma))
    D = np.diag(d)
    sigma = D @ sigma @ D

    # Validate output
    assert mu.shape == (n,), f"Mu shape mismatch: {mu.shape} != ({n},)"
    assert sigma.shape == (n, n), f"Sigma shape mismatch: {sigma.shape} != ({n}, {n})"
    assert len(tickers) == n, f"Tickers length mismatch: {len(tickers)} != {n}"
    assert len(sectors) == n, f"Sectors length mismatch: {len(sectors)} != {n}"

    # Check positive semi-definiteness
    eigenvalues = np.linalg.eigvalsh(sigma)
    assert eigenvalues.min() >= -1e-10, f"Sigma is not PSD: min eigenvalue = {eigenvalues.min()}"

    # Save to npz
    np.savez(str(output_path), mu=mu, sigma=sigma, tickers=tickers, sectors=sectors)

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info("Successfully generated synthetic alpha data at: %s (%.2f MB)", output_path, file_size_mb)
    logger.info("Schema: mu=%s, sigma=%s, tickers=%d, sectors=%d", mu.shape, sigma.shape, len(tickers), len(sectors))

    return output_path


def validate_alpha_data(path: Path) -> bool:
    """Validate that an alpha data file has the correct schema.

    Args:
        path: Path to the NPZ file

    Returns:
        True if valid, False otherwise
    """
    if not path.exists():
        logger.warning("Alpha data file does not exist: %s", path)
        return False

    try:
        data = np.load(str(path), allow_pickle=True)

        required_keys = {"mu", "sigma", "tickers", "sectors"}
        missing = required_keys - set(data.files)
        if missing:
            logger.error("Missing required keys in alpha data: %s", missing)
            return False

        mu = np.asarray(data["mu"], dtype=float)
        sigma = np.asarray(data["sigma"], dtype=float)
        tickers = [str(item) for item in data["tickers"].tolist()]
        sectors = [str(item) for item in data["sectors"].tolist()]

        if sigma.shape != (len(mu), len(mu)):
            logger.error("Covariance shape %s does not match mu length %d", sigma.shape, len(mu))
            return False

        if len(tickers) != len(mu) or len(sectors) != len(mu):
            logger.error("Ticker/sector metadata does not match alpha vector length")
            return False

        logger.info("Alpha data validation passed: %d assets", len(mu))
        return True

    except Exception as e:
        logger.error("Alpha data validation failed: %s", e)
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    parser = argparse.ArgumentParser(description="Generate synthetic NIFTY 50 alpha data")
    parser.add_argument("--output", type=str, default=None, help="Output directory (default: ../output)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--force", action="store_true", help="Force regeneration even if file exists")
    args = parser.parse_args()

    output_dir = Path(args.output) if args.output else None
    path = generate_nifty50_alpha(output_dir=output_dir, seed=args.seed, force=args.force)

    if validate_alpha_data(path):
        print(f"Alpha data generation complete: {path}")
    else:
        print(f"ERROR: Alpha data validation failed at {path}")
        exit(1)
