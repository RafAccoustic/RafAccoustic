# Use the official Python image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app
COPY . .
    
# Expose port (must match your app's internal port)
EXPOSE 5000

# Set the environment variable for Flask to find the app
ENV FLASK_APP=app.py

# Run the Flask app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]

