# backend/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy startup script
COPY start.sh .
RUN chmod +x start.sh

# Expose port
EXPOSE 8000

# Use startup script instead of direct python command
CMD ["./start.sh"]