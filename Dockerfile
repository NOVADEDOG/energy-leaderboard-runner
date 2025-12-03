# Use Python 3.10 slim base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# - sudo: Required for powermetrics on macOS (if running in a macOS container)
# - procps: Provides ps command for process management
RUN apt-get update && apt-get install -y \
    sudo \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY ./src /app/src

# Copy data files
COPY ./src/data /app/src/data

# Copy automation script
COPY run_all_tests.py /app/run_all_tests.py

# Create results directory
RUN mkdir -p /app/results

# Set Python path
ENV PYTHONPATH=/app

# Set entrypoint to the main CLI script
ENTRYPOINT ["python", "src/main.py"]

# Default command (can be overridden)
CMD ["--help"]
