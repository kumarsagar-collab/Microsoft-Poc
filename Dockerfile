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

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/mcp', timeout=2.0)" || exit 1

# Default command (can be overridden)
CMD ["mcp-fastmcp-server"]
