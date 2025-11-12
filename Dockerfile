# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml ./
COPY README.md ./
COPY FastMCPServer/ ./FastMCPServer/
COPY LowLevelMCPServer/ ./LowLevelMCPServer/

# Install dependencies
RUN uv pip install --system -e .

# Expose ports
EXPOSE 8000 3000

# Default command (can be overridden)
CMD ["mcp-fastmcp-server"]
