# Use Python slim image
FROM python:3.12-slim

# Install necessary packages
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app
ENV PERSISTENT_DATA_PATH=/data

# Create persistent data directory
RUN mkdir -p /data

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Upgrade pip
RUN pip install --upgrade pip

# Install dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Add environment secret expansion script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set entrypoint to handle secrets before running the main command
ENTRYPOINT ["/entrypoint.sh"]

# Ensure the application runs as expected
CMD ["python3", "-u", "/app/run.py"]
