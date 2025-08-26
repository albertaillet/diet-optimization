# ---- Debian debian:bookworm-slim (with or without uv)
# FROM debian:bookworm-slim
FROM ghcr.io/astral-sh/uv:bookworm-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates wget make unzip esbuild \
    && rm -rf /var/lib/apt/lists/*

# ---- Install duckdb ----
# From https://github.com/data-catering/duckdb-docker/blob/d425cf4c70ca532586d6cb2579e9148d17745832/Dockerfile
# arm64 or amd64
ARG DUCKDB_ARCH=arm64
ARG DUCKDB_VERSION=v1.3.2
RUN wget -O duckdb_cli.zip \
    "https://github.com/duckdb/duckdb/releases/download/${DUCKDB_VERSION}/duckdb_cli-linux-${DUCKDB_ARCH}.zip" \
    && unzip duckdb_cli.zip -d /bin \
    && rm duckdb_cli.zip

WORKDIR /app

# ---- Copy project files ----
COPY ./Makefile .
COPY ./dietdashboard ./dietdashboard
COPY ./queries ./queries

# ---- Install all python dependencies ----
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=./uv.lock,target=uv.lock,ro,z \
    --mount=type=bind,source=./pyproject.toml,target=pyproject.toml,ro,z \
    uv sync --frozen --no-editable --no-dev

# ---- Copy data files ----
COPY ./data ./data
RUN ln -s /app/data/data.db.build_context /app/data/data.db

# ---- Install pnpm ----
RUN wget -qO- https://get.pnpm.io/install.sh | ENV="$HOME/.shrc" SHELL="$(which sh)" sh -
ENV PATH="/root/.local/share/pnpm:$PATH"
