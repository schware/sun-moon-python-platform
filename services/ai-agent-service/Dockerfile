FROM python:3.12-slim
WORKDIR /app

RUN pip install --no-cache-dir uv

# Copy the whole workspace: uv needs to see libs/ to resolve the
# {workspace = true} sources declared in this service's pyproject.toml.
COPY pyproject.toml ./
COPY libs ./libs
COPY services/ai-agent-service ./services/ai-agent-service

RUN uv sync --package ai-agent-service --no-dev

EXPOSE 8082
CMD ["uv", "run", "--package", "ai-agent-service", "python", "-m", "ai_agent_service.main"]
