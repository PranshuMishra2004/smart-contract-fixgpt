FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/root/.foundry/bin:${PATH}"

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        git \
        ca-certificates \
        build-essential \
        libssl-dev \
        pkg-config && \
    rm -rf /var/lib/apt/lists/*

# Install Foundry
RUN curl -L https://foundry.paradigm.xyz | bash && \
    /root/.foundry/bin/foundryup

# Install Python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Solidity security tooling
RUN pip install --no-cache-dir \
    slither-analyzer \
    solc-select

# Pre-install commonly used Solidity versions.
# FixGPT can install additional versions at runtime
# when a contract requires them.
RUN solc-select install 0.8.24 && \
    solc-select install 0.8.28 && \
    solc-select install 0.8.33 && \
    solc-select use 0.8.33

# Copy application
COPY analyzer ./analyzer
COPY backend ./backend
COPY contracts ./contracts
COPY frontend ./frontend
COPY .env.example ./
COPY README.md ./

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-10000}"]