# Containerfile for CNC Design Studio
# Build: podman build -t cnc-studio .
# Run: podman run -p 5000:5000 -v $(pwd):/app/data:Z cnc-studio

FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    gfortran \
    libgl1 \
    libglu1-mesa \
    libxrender1 \
    libxext6 \
    libsm6 \
    libice6 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY pyproject.toml* ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    'build123d>=0.7.0' \
    'ocp-vscode>=2.7.0' \
    'flask>=3.0' \
    'ocp-tessellate>=3.2.2' \
    'py-lib3mf>=2.3.1' && \
    ln -s /usr/local/lib/python3.12/site-packages/lib3mf /usr/local/lib/python3.12/site-packages/py_lib3mf

# Copy application code
COPY lib/ ./lib/
COPY parts/ ./parts/
COPY webapp/ ./webapp/
COPY exports/ ./exports/

# Create necessary directories
RUN mkdir -p /app/exports /app/data

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=webapp/app.py
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/parts')"

# Run the application
CMD ["python", "webapp/app.py"]
