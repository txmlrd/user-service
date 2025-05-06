# Gunakan image Python
FROM python:3.10-slim

ENV PYTHONPATH=/app

# Set working directory
WORKDIR /app

RUN pip install redis

# Install netcat dan clean up cache
RUN apt-get update && apt-get install -y --no-install-recommends netcat-openbsd && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy semua file ke dalam container
COPY . /app/

# Install dependency Python
RUN pip install --no-cache-dir -r requirements.txt

# Default command

CMD ["python","app/run.py"]
