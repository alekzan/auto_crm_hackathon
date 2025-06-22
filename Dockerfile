# Stage 1: Build the React frontend
FROM node:20-slim AS builder
WORKDIR /app

# Copy package.json and package-lock.json first to leverage Docker cache
COPY frontend/package.json frontend/package-lock.json ./frontend/

# Install dependencies, ignoring peer dependency conflicts
RUN npm install --prefix frontend --legacy-peer-deps

# Copy the rest of the frontend code
COPY frontend/ ./frontend/

# Build the frontend
RUN npm run build --prefix frontend

# Stage 2: Create the final Python application
FROM python:3.11-slim
WORKDIR /app

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code
COPY . .

# Copy the built frontend from the builder stage, overwriting the source
COPY --from=builder /app/frontend/dist ./frontend/dist

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"] 