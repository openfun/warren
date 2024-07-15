# -- Base image --
FROM python:3.12-slim AS base

ARG DOCKER_GID
ARG DOCKER_UID

# Upgrade pip to its latest release to speed up dependencies installation
RUN pip install --upgrade pip

# Upgrade system packages to install security updates
RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get install -y \
        git && \
    rm -rf /var/lib/apt/lists/*

# -- Builder --
FROM base AS builder

WORKDIR /build

COPY pyproject.toml /build/

RUN pip install .

# -- Core --
FROM base AS core

COPY --from=builder /usr/local /usr/local

# Create group (if not already present) and user
RUN getent group ${DOCKER_GID} || addgroup --gid ${DOCKER_GID} docs && \
      adduser --uid ${DOCKER_UID} --gid ${DOCKER_GID} --disabled-login docs

USER docs

ENV HOME=/home/docs

WORKDIR /app
