FROM python:3.12-slim

# uv: fast Python package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Keep the virtualenv OUTSIDE /app, so mounting your code doesn't hide it
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install dependencies first (cached unless pyproject.toml changes)
COPY pyproject.toml ./
RUN uv sync --no-install-project

# Copy the code (in development it's replaced by the mounted folder)
COPY . .

# Keep the container alive so you can exec into it
CMD ["sleep", "infinity"]
