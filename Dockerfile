# Share the Wealth — API + static UI (SQLite warehouse under WAREHOUSE_PATH)
FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY share_the_wealth ./share_the_wealth
COPY static ./static
COPY api.py main.py ./

RUN pip install --no-cache-dir pip -U && pip install --no-cache-dir -e .

ENV WAREHOUSE_PATH=/data/warehouse.db
ENV READ_FROM_WAREHOUSE=true
EXPOSE 8007

CMD ["uvicorn", "share_the_wealth.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8007"]
