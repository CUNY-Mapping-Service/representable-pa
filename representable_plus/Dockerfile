FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

RUN apt-get update && \
    apt-get install -y curl unzip --no-install-recommends && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://bun.sh/install | bash
ENV PATH="$PATH:/root/.bun/bin"

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY uv.lock /app/uv.lock

RUN uv sync

COPY ./vue-project /app/vue-project
WORKDIR /app/vue-project
RUN bun install

WORKDIR /app

ENTRYPOINT ["bash"]