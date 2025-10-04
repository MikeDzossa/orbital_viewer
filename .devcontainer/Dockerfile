# Base image with Python and Node.js
FROM mcr.microsoft.com/devcontainers/python:3.11

# Install Node.js and npm
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs

# Ensure .ssh directory exists for root user
RUN mkdir -p /home/root/.ssh && \
    chown root:root /home/root/.ssh && \
    chmod 700 /home/root/.ssh

# Set working directory
WORKDIR /workspace

# Install Python dependencies
COPY backend/requirements.txt /workspace/backend/requirements.txt
RUN pip install --upgrade pip && pip install -r /workspace/backend/requirements.txt

# Install Node.js dependencies
COPY frontend/package.json frontend/package-lock.json* /workspace/frontend/
WORKDIR /workspace/frontend
RUN npm install

# Return to the workspace root
WORKDIR /workspace