FROM python:3.14.6-slim
WORKDIR /app
RUN pip install --no-cache-dir uv==0.12.0
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY . .
