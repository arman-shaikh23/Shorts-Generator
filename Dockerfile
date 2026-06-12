FROM python:3.10-slim AS builder

RUN apt-get update && apt-get install -y curl
WORKDIR /app

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
RUN apt-get install -y nodejs

# Build frontend
COPY frontend ./frontend
WORKDIR /app/frontend
RUN npm install
RUN npm run build

# Final Stage
FROM python:3.10-slim

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Setup Python backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend

# Copy built frontend
COPY --from=builder /app/frontend/dist ./backend/static

WORKDIR /app/backend
# Expose port (Railway passes PORT env var)
EXPOSE 8000

CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
