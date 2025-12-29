FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

RUN apt-get update

RUN apt-get install -y curl unzip \
     --no-install-recommends && \
    apt-get clean -y

RUN curl -fsSL https://bun.sh/install | bash

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY uv.lock /app/uv.lock

RUN uv sync

COPY ./vue-project /app/vue-project
WORKDIR /app/vue-project
RUN bun install
RUN bun run build

ENTRYPOINT ["bash"]