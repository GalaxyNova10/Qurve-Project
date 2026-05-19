import numpy as np
import os
from pathlib import Path

def generate_nifty50_alpha():
    # Define NIFTY 50 universe
    tickers = [
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

    sectors = [
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

    n = len(tickers)
    np.random.seed(42)

    # Generate synthetic expected returns (mu) between -5% and +25%
    mu = np.random.uniform(-0.05, 0.25, n)

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

    # Define output path
    output_dir = Path(__file__).resolve().parent.parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "alpha_data.npz"

    # Save to npz
    np.savez(output_path, mu=mu, sigma=sigma, tickers=tickers, sectors=sectors)
    print(f"Successfully generated synthetic alpha data at: {output_path}")

if __name__ == "__main__":
    generate_nifty50_alpha()
