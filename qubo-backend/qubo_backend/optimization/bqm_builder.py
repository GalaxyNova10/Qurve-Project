from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil, log2
from typing import Iterable

import numpy as np

from .contracts import SolverRequest


Variable = str
Pair = tuple[Variable, Variable]


def _ordered_pair(a: Variable, b: Variable) -> Pair:
    return (a, b) if a <= b else (b, a)


def _sector_key(sector: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in sector.lower()).strip("_") or "unknown"


@dataclass
class PortfolioBQM:
    """Small BQM abstraction that can become dimod when Ocean is installed."""

    linear: dict[Variable, float] = field(default_factory=dict)
    quadratic: dict[Pair, float] = field(default_factory=dict)
    offset: float = 0.0
    variables: set[Variable] = field(default_factory=set)

    @property
    def vartype(self) -> str:
        return "BINARY"

    def add_variable(self, name: Variable) -> None:
        self.variables.add(name)
        self.linear.setdefault(name, 0.0)

    def add_linear(self, name: Variable, bias: float) -> None:
        self.add_variable(name)
        self.linear[name] = self.linear.get(name, 0.0) + float(bias)

    def add_quadratic(self, left: Variable, right: Variable, bias: float) -> None:
        if left == right:
            self.add_linear(left, bias)
            return
        self.add_variable(left)
        self.add_variable(right)
        pair = _ordered_pair(left, right)
        self.quadratic[pair] = self.quadratic.get(pair, 0.0) + float(bias)

    def add_square_penalty(self, coeffs: dict[Variable, float], rhs: float, penalty: float) -> None:
        """Add penalty * (sum(coeffs[v] * v) - rhs)^2 for binary variables."""
        self.offset += penalty * rhs * rhs
        items = list(coeffs.items())
        for var, coeff in items:
            self.add_linear(var, penalty * (coeff * coeff - 2.0 * rhs * coeff))
        for i, (left, left_coeff) in enumerate(items):
            for right, right_coeff in items[i + 1 :]:
                self.add_quadratic(left, right, penalty * 2.0 * left_coeff * right_coeff)

    def to_dimod(self):
        try:
            import dimod
        except ImportError as exc:
            raise RuntimeError("dimod is not installed; install dwave-ocean-sdk or dimod") from exc
        return dimod.BinaryQuadraticModel(self.linear, self.quadratic, self.offset, dimod.BINARY)


@dataclass(frozen=True)
class BQMBuildResult:
    bqm: PortfolioBQM
    variable_order: list[str]
    weight_variables: list[list[str]]
    indicator_variables: list[str]
    slack_variables: dict[str, list[str]]
    denominator: int


def x_var(i: int, bit: int) -> str:
    return f"x_{i}_{bit}"


def y_var(i: int) -> str:
    return f"y_{i}"


def build_portfolio_bqm(request: SolverRequest) -> BQMBuildResult:
    mu = np.asarray(request.mu, dtype=float)
    sigma = np.asarray(request.sigma, dtype=float)
    n_assets = len(mu)
    if sigma.shape != (n_assets, n_assets):
        raise ValueError("sigma must be square and match mu length")
    if len(request.tickers) != n_assets or len(request.sectors) != n_assets:
        raise ValueError("tickers and sectors must match mu length")
    if request.cardinality > n_assets:
        raise ValueError("cardinality cannot exceed number of assets")

    bqm = PortfolioBQM()
    denominator = (2**request.binary_bits) - 1
    weight_vars = [[x_var(i, bit) for bit in range(request.binary_bits)] for i in range(n_assets)]
    indicator_vars = [y_var(i) for i in range(n_assets)]
    for row in weight_vars:
        for name in row:
            bqm.add_variable(name)
    for name in indicator_vars:
        bqm.add_variable(name)

    def weight_coeffs(i: int) -> dict[str, float]:
        return {weight_vars[i][bit]: (2**bit) / denominator for bit in range(request.binary_bits)}

    # Markowitz objective: minimize risk - risk_tolerance * return.
    for i in range(n_assets):
        for bit_i, var_i in enumerate(weight_vars[i]):
            coeff_i = (2**bit_i) / denominator
            bqm.add_linear(var_i, -request.risk_tolerance * mu[i] * coeff_i)
            for bit_j, var_j in enumerate(weight_vars[i]):
                coeff_j = (2**bit_j) / denominator
                bqm.add_quadratic(var_i, var_j, sigma[i, i] * coeff_i * coeff_j)
        for j in range(i + 1, n_assets):
            for bit_i, var_i in enumerate(weight_vars[i]):
                coeff_i = (2**bit_i) / denominator
                for bit_j, var_j in enumerate(weight_vars[j]):
                    coeff_j = (2**bit_j) / denominator
                    bqm.add_quadratic(var_i, var_j, 2.0 * sigma[i, j] * coeff_i * coeff_j)

    objective_scale = max(1.0, float(np.max(np.abs(mu))) + float(np.max(np.abs(sigma))))
    budget_penalty = 100.0 * objective_scale
    cardinality_penalty = 40.0 * objective_scale
    link_penalty = 20.0 * objective_scale
    sector_penalty = 60.0 * objective_scale

    budget_coeffs: dict[str, float] = {}
    for i in range(n_assets):
        budget_coeffs.update(weight_coeffs(i))
    bqm.add_square_penalty(budget_coeffs, rhs=1.0, penalty=budget_penalty)

    bqm.add_square_penalty({name: 1.0 for name in indicator_vars}, rhs=float(request.cardinality), penalty=cardinality_penalty)

    # Link weight bits to indicator variables: x[i,k] can only be 1 when y[i] is 1.
    for i in range(n_assets):
        y = indicator_vars[i]
        for var in weight_vars[i]:
            bqm.add_linear(var, link_penalty)
            bqm.add_quadratic(var, y, -link_penalty)
        # Encourage selected assets to carry at least one active bit.
        bqm.add_linear(y, link_penalty)
        for var in weight_vars[i]:
            bqm.add_quadratic(y, var, -link_penalty / request.binary_bits)

    slack_variables: dict[str, list[str]] = {}
    unique_sectors = sorted(set(request.sectors))
    slack_bits = max(1, ceil(log2(denominator + 1)))
    for sector in unique_sectors:
        key = _sector_key(sector)
        slack = [f"slack_{key}_{bit}" for bit in range(slack_bits)]
        slack_variables[sector] = slack
        sector_coeffs: dict[str, float] = {}
        for i, asset_sector in enumerate(request.sectors):
            if asset_sector == sector:
                sector_coeffs.update(weight_coeffs(i))
        for bit, var in enumerate(slack):
            sector_coeffs[var] = request.max_sector_exposure * (2**bit) / ((2**slack_bits) - 1)
        bqm.add_square_penalty(
            sector_coeffs,
            rhs=request.max_sector_exposure,
            penalty=sector_penalty,
        )

    variable_order = list(_iter_variables(weight_vars, indicator_vars, slack_variables))
    return BQMBuildResult(
        bqm=bqm,
        variable_order=variable_order,
        weight_variables=weight_vars,
        indicator_variables=indicator_vars,
        slack_variables=slack_variables,
        denominator=denominator,
    )


def _iter_variables(
    weight_vars: list[list[str]],
    indicator_vars: list[str],
    slack_variables: dict[str, list[str]],
) -> Iterable[str]:
    for row in weight_vars:
        yield from row
    yield from indicator_vars
    for sector in sorted(slack_variables):
        yield from slack_variables[sector]

