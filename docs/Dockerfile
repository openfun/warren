# -- Base image --
FROM python:3.12-slim as base

# Upgrade pip to its latest release to speed up dependencies installation
RUN pip install --upgrade pip

# Upgrade system packages to install security updates
RUN apt-get update && \
    apt-get -y upgrade && \
    rm -rf /var/lib/apt/lists/*


# -- Builder --
FROM base as builder

WORKDIR /build

COPY pyproject.toml /build/

# RUN apt-get update && \
#     apt-get install -y \
#         build-essential \
#         gcc \
#         libc6-dev \
#         libffi-dev && \
#     rm -rf /var/lib/apt/lists/*

RUN pip install .

# -- Core --
FROM base as core

COPY --from=builder /usr/local /usr/local

WORKDIR /app
