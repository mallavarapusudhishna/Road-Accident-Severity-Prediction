# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir helps to keep the docker image size small
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
# This includes backend, frontend, models, etc.
COPY . .

# Expose port 8000 to the outside world
EXPOSE 8000

# Command to run the unified application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
