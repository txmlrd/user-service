# Gunakan image Python
FROM python:3.10

# Set work directory
WORKDIR /app

# Copy semua file
COPY . .

# Install dependency
RUN pip install -r requirements.txt

# Jalankan database.py untuk create tabel terlebih dahulu
RUN python app/database.py

# Jalankan Flask app
CMD ["python", "app/app.py"]
