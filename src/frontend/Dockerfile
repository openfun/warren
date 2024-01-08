# -- Base image --
FROM node:21.5.0-slim as base

# Upgrade npm to its latest release to speed up dependencies installation
RUN npm update -g npm

# Upgrade system packages to install security updates
RUN apt-get update && \
    apt-get -y upgrade && \
    rm -rf /var/lib/apt/lists/*


# -- Builder --
FROM base as builder

WORKDIR /build

COPY . /build/

RUN yarn install


# -- Core --
FROM base as core

COPY --from=builder /build/node_modules /app/node_modules

# Copy all sources, not only runtime-required files
COPY . /app/

WORKDIR /app


# -- Development --
FROM core as development

# Install Git (required for changeset)
RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

# Un-privileged user running the application
USER ${DOCKER_USER:-1000}


# -- Production --
FROM core as production

# Un-privileged user running the application
USER ${DOCKER_USER:-1000}
