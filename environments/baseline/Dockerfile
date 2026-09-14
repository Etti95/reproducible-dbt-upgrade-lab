# Canonical build platform: linux/amd64 (pass --platform when building).
FROM python:3.12.11-slim-bookworm@sha256:c00fc7b44d844b6da22861ec24af43968a5200eac4ec607b4725d585165d6b49
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DBT_SEND_ANONYMOUS_USAGE_STATS=false \
    TZ=UTC \
    LAB_ENVIRONMENT=baseline
WORKDIR /workspace
COPY environments/baseline/requirements.txt /opt/lab/requirements.txt
RUN python -m pip install --no-cache-dir --require-hashes --only-binary=:all: -r /opt/lab/requirements.txt \
    && python -m pip check
COPY scripts/inventory.py /opt/lab/inventory.py
CMD ["python", "/opt/lab/inventory.py", "/evidence"]
