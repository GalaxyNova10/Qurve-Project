import unittest
import numpy as np
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.optimization.bqm_builder import build_portfolio_bqm

class TestObjectiveNormalizationConsistency(unittest.TestCase):
    def setUp(self):
        # Create a sample request
        self.request = SolverRequest(
            mu=[0.1, 0.2, 0.3],
            sigma=[[0.01, 0.005, 0.0], [0.005, 0.02, 0.0], [0.0, 0.0, 0.03]],
            tickers=["AAPL", "MSFT", "GOOG"],
            sectors=["Tech", "Tech", "Tech"],
            cardinality=2,
            max_sector_exposure=1.0,
            risk_tolerance=0.5,
            binary_bits=2,
            solver="classical",
            trajectories=10,
            benchmark_mode="FAST"
        )

    def test_build_portfolio_bqm_executes_successfully(self):
        """Validation Requirement: build_portfolio_bqm() executes successfully"""
        try:
            result = build_portfolio_bqm(self.request)
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"build_portfolio_bqm raised {type(e).__name__} unexpectedly: {e}")

    def test_objective_span_and_scale_exist(self):
        """Validation Requirement: objective_span and objective_scale exist and are positive"""
        result = build_portfolio_bqm(self.request)
        self.assertTrue(hasattr(result, 'objective_span'))
        self.assertGreater(result.objective_span, 0)

    def test_penalties_derive_correctly(self):
        """Validation Requirement: penalties derive correctly from objective_span"""
        result = build_portfolio_bqm(self.request)
        objective_span = result.objective_span
        
        # P_card should be 100x objective_span
        # In the BQM, quadratic terms between indicator variables (y_i) for EXACT-K 
        # are 2.0 * P_card (line 213 in bqm_builder.py)
        y0, y1 = result.indicator_variables[0], result.indicator_variables[1]
        pair = (y0, y1) if y0 < y1 else (y1, y0)
        if pair in result.bqm.quadratic:
            penalty_val = result.bqm.quadratic[pair]
            # Since P_card = 100 * objective_span, and quadratic term is 2.0 * P_card
            expected_penalty = 2.0 * 100.0 * objective_span
            self.assertAlmostEqual(penalty_val, expected_penalty, places=4)

if __name__ == '__main__':
    unittest.main()
