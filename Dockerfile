# syntax=docker/dockerfile:1
# One image, two services:
#   laya-serve  — Jev HTTP decision API (default CMD), internal compose network
#   laya-mcp    — streamable-HTTP MCP tools (compose overrides `command`)
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    HF_HOME=/models \
    HF_HUB_OFFLINE=1 \
    TORCH_DISABLE_NATIVE_JIT=1 \
    OMP_NUM_THREADS=4 \
    LAYA_HOST=0.0.0.0 \
    LAYA_PORT=8090 \
    LAYA_MODELS=typed-decisions \
    LAYA_PRELOAD=1 \
    LAYA_SERVE_URL=http://laya-serve:8090 \
    LAYA_MODEL=typed-decisions \
    LAYA_REGISTRY=/app/models.yaml

# CPU-only torch first so CUDA wheels can never land; laya[serve] then finds
# torch already satisfied.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir "laya[serve]"

# Bake the typed-decisions checkpoint into the image: cold start works offline.
RUN HF_HUB_OFFLINE=0 python -c "from laya import Router; Router().preload(['typed-decisions'])"

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
COPY models.yaml ./models.yaml
RUN pip install --no-cache-dir .

EXPOSE 8090 8091
CMD ["laya-serve"]
