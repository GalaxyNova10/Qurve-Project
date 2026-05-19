# 2026-Quantum-Inspired-QUBO-Portfolio-Optimization-Platform
https://idea.unisys.com/D9033

# Qurve - Quantum Portfolio Optimization Platform

A full-stack quantum computing portfolio optimization platform using QUBO (Quadratic Unconstrained Binary Optimization) solvers across multiple quantum backends (D-Wave, AWS Braket, IBM Qiskit).

## Architecture

- **Backend** (`qubo-backend/`): FastAPI-based Python backend with quantum solver integration
- **Frontend** (`app/`): React + Vite + TypeScript frontend with 3D visualizations
- **Braket Worker** (`qubo-braket-worker/`): AWS Braket job worker for quantum execution

## Prerequisites

- Python 3.10+
- Node.js 18+
- (Optional) AWS account for Braket execution

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/GalaxyNova10/Qurve-Project.git
cd Qurve-Project
```

### 2. Backend Setup

```bash
cd qubo-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Edit with your configuration
uvicorn app.main:app --reload
```

### 3. Frontend Setup

```bash
cd app
npm install
npm run dev
```

### 4. (Optional) Braket Worker

```bash
cd qubo-braket-worker
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Environment Configuration

Copy `.env.example` to `.env` in the root directory and fill in your AWS credentials and other configuration values. **Never commit `.env` files.**

## Tech Stack

- **Backend**: FastAPI, Pydantic, SQLAlchemy, Redis
- **Frontend**: React, TypeScript, Vite, Tailwind CSS, Three.js
- **Quantum**: D-Wave Ocean SDK, Qiskit, AWS Braket, PyQUBO, Simulated Bifurcation
