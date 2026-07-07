FROM python:3.11-slim

# Copy the official Deno binary into our container for YouTube JS challenge solving
COPY --from=denoland/deno:bin /deno /usr/local/bin/deno

# Install system dependencies: ffmpeg (for merging audio/video)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directories for downloads, cache, and cookies
RUN mkdir -p /app/downloads /app/cookies /root/.cache/yt-dlp

# Copy application source code
COPY . .

# Expose FastAPI port
EXPOSE 38282

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "38282"]
