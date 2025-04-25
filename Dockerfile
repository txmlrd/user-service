# Gunakan image Python
FROM python:3.10

# Set work directory
WORKDIR /app

# Copy semua file
COPY . .

# Install dependency Python
RUN pip install -r requirements.txt

# Install netcat buat cek koneksi DB
RUN apt-get update && apt-get install -y netcat-openbsd

# Default command kalau nggak override dari docker-compose
CMD ["python", "app/app.py"]
