# Use a multi-stage build to install dependencies and build wheels
FROM python:3.10-slim as builder

# Set the working directory for the builder
WORKDIR /install

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++

# Install pip dependencies and build wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Use the official Python Alpine image as a base for a smaller image size
FROM python:3.10-alpine

# Set the working directory for the container
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copy installed packages from the builder stage
COPY --from=builder /install /usr/local

# Copy the application code to the container
COPY . .

# Expose the port that the app will run on
EXPOSE 8000

# Start the application using Gunicorn with the Uvicorn worker class
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000"]

