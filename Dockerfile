# Dockerfile

# 1. Base Image
FROM python:3.13-slim

# 2. Set Environment Variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

# 3. Set Working Directory
WORKDIR /app

# 4. Install uv
RUN pip install uv

# 5. Copy dependency files and install dependencies
COPY pyproject.toml uv.lock* ./
RUN uv pip install --system --no-cache .

# 6. Copy application code
COPY . /app

# 7. Expose port
EXPOSE 8000

# 8. Command to run the app
CMD ["uvicorn", "app.create_app:create_app", "--host", "0.0.0.0", "--port", "8000"]
