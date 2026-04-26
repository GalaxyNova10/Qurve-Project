from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .bqm_builder import BQMBuildResult, build_portfolio_bqm
from .contracts import SolverRequest


@dataclass(frozen=True)
class QuboModel:
    request: SolverRequest
    build: BQMBuildResult

    @property
    def variable_order(self) -> list[str]:
        return self.build.variable_order

    @property
    def variable_count(self) -> int:
        return len(self.build.variable_order)


def build_qubo_model(request: SolverRequest) -> QuboModel:
    return QuboModel(request=request, build=build_portfolio_bqm(request))


def to_dimod_bqm(model: QuboModel):
    return model.build.bqm.to_dimod()


def to_qubo_matrix(model: QuboModel) -> tuple[np.ndarray, list[str], float]:
    """Return upper-triangular QUBO matrix Q where E=x'Qx+offset."""
    order = model.variable_order
    index = {name: pos for pos, name in enumerate(order)}
    q = np.zeros((len(order), len(order)), dtype=float)
    for var, bias in model.build.bqm.linear.items():
        q[index[var], index[var]] += float(bias)
    for (left, right), bias in model.build.bqm.quadratic.items():
        i = index[left]
        j = index[right]
        if i <= j:
            q[i, j] += float(bias)
        else:
            q[j, i] += float(bias)
    return q, order, float(model.build.bqm.offset)


def decode_sample_to_weights(model: QuboModel, sample: dict[str, int | float | bool]) -> np.ndarray:
    weights = np.zeros(len(model.request.tickers), dtype=float)
    for i, row in enumerate(model.build.weight_variables):
        units = 0
        for bit, var in enumerate(row):
            units += int(round(float(sample.get(var, 0)))) * (2**bit)
        weights[i] = units / model.build.denominator
    return weights


def to_qiskit_quadratic_program(model: QuboModel):
    try:
        from qiskit_optimization import QuadraticProgram
    except ImportError as exc:
        raise RuntimeError("qiskit-optimization is not installed") from exc

    qp = QuadraticProgram("qubo_portfolio")
    for variable in model.variable_order:
        qp.binary_var(variable)
    qp.minimize(
        constant=float(model.build.bqm.offset),
        linear={name: float(bias) for name, bias in model.build.bqm.linear.items()},
        quadratic={(left, right): float(bias) for (left, right), bias in model.build.bqm.quadratic.items()},
    )
    return qp
