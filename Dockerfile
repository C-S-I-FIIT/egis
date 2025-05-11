FROM python:3.10-slim

WORKDIR /app

# Install dependencies required for WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY egis-app/ /app/

# Make main.py executable
RUN chmod +x main.py

# Expose port for web interface
EXPOSE 80

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the EGIS web interface via the main.py launcher
#CMD ["streamlit", "run", "homepage.py", "--server.port", "80"]