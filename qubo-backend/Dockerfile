FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir "dwave-ocean-sdk>=8.0.0" "qiskit>=2.3.0" "qiskit-algorithms>=0.3.0" "qiskit-optimization>=0.7.0" "qiskit-ibm-runtime>=0.43.0"

COPY . .

# Use a non-root user for security
RUN useradd -m -u 1000 appuser
USER appuser

ENV PATH="/home/appuser/.local/bin:${PATH}"

EXPOSE 8000

# Use healthcheck to ensure service is ready
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
