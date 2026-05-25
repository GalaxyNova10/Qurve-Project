from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from qubo_backend.storage.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String)
    hashed_password = Column(String, nullable=False)
    disabled = Column(Boolean, default=False)
    profile = Column(JSON)
    settings = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class OptimizationRun(Base):
    __tablename__ = "optimization_runs"

    id = Column(String, primary_key=True, index=True)
    solver = Column(String, nullable=False)
    execution_time_ms = Column(Float)
    energy = Column(Float)
    strict_ratio = Column(Float)
    feasible_ratio = Column(Float)
    topology_density = Column(Float)
    scientific_status = Column(String)
    isolation_status = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    optimization_id = Column(String, ForeignKey("optimization_runs.id"))
    total_return = Column(Float)
    volatility = Column(Float)
    sharpe_ratio = Column(Float)
    sortino_ratio = Column(Float)
    max_drawdown = Column(Float)
    alpha = Column(Float)
    scientific_status = Column(String)
    feasible = Column(Boolean)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    optimization_run = relationship("OptimizationRun")
    allocations = relationship("Allocation", back_populates="portfolio")


class Allocation(Base):
    __tablename__ = "allocations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(String, ForeignKey("portfolios.id"), nullable=False)
    asset = Column(String, nullable=False)
    sector = Column(String)
    weight = Column(Float, nullable=False)
    expected_return = Column(Float)
    risk_contribution = Column(Float)
    
    portfolio = relationship("Portfolio", back_populates="allocations")


class TelemetrySnapshot(Base):
    __tablename__ = "telemetry_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gpu_name = Column(String)
    gpu_utilization = Column(Float)
    memory_used = Column(Float)
    memory_total = Column(Float)
    temperature = Column(Float)
    power_draw = Column(Float)
    fan_speed = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
