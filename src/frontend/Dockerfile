# -- Base image --
FROM node:21.5.0-slim AS base

# Upgrade npm to its latest release to speed up dependencies installation
RUN npm update -g npm

# Upgrade system packages to install security updates
RUN apt-get update && \
    apt-get -y upgrade && \
    rm -rf /var/lib/apt/lists/*


# -- Builder --
FROM base AS builder

WORKDIR /build

COPY . /build/

RUN yarn install


# -- Core --
FROM base AS core

COPY --from=builder /build/node_modules /app/node_modules

# Copy all sources, not only runtime-required files
COPY . /app/

WORKDIR /app


# -- Development --
FROM core AS development

# Install Git (required for changeset)
RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

# Un-privileged user running the application
ARG DOCKER_USER=1000
USER ${DOCKER_USER}


# -- Production --
FROM core AS production

# Un-privileged user running the application
ARG DOCKER_USER=1000
USER ${DOCKER_USER}
