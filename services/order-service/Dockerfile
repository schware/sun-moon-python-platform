FROM python:3.12-slim
WORKDIR /app

RUN pip install --no-cache-dir uv

# Copy the whole workspace: uv needs to see libs/ to resolve the
# {workspace = true} sources declared in this service's pyproject.toml.
COPY pyproject.toml ./
COPY libs ./libs
COPY services/order-service ./services/order-service

RUN uv sync --package order-service --no-dev

EXPOSE 8081 8090
CMD ["uv", "run", "--package", "order-service", "python", "-m", "order_service.main"]
