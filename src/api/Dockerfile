# -- Base image --
FROM python:3.12-slim AS base

# Upgrade pip to its latest release to speed up dependencies installation
RUN pip install --upgrade pip

# Upgrade system packages to install security updates
RUN apt-get update && \
    apt-get -y upgrade && \
    rm -rf /var/lib/apt/lists/*


# -- Builder --
# Core builder (no plugins installed)
FROM base AS core-builder

WORKDIR /build

COPY . /build/

RUN apt-get update && \
    apt-get install -y \
        build-essential \
        gcc \
        libc6-dev \
        libffi-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install ./core

# Full distro builder (all official plugins installed)
FROM core-builder AS full-builder

RUN pip install ./plugins/*

# -- Core --
FROM base AS core

COPY --from=core-builder /usr/local /usr/local

# Copy only run-time required default configurations
COPY ./core/logging-config.prod.yaml /app/core/

WORKDIR /app

# -- Full --
FROM core AS full

COPY --from=full-builder /usr/local /usr/local


# -- Development --
FROM full AS development

# Copy all sources, not only runtime-required files
COPY . /app/

# Uninstall warren and re-install it in editable mode along with development
# dependencies
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN pip uninstall -y $(pip list | cut -f1 -d " " | grep warren)
RUN pip install -e ./core[dev] && \
    for plugin in ./plugins/*; do \
        pip install -e "${plugin}[dev]"; \
    done

# Un-privileged user running the application
ARG DOCKER_USER=1000
USER ${DOCKER_USER}


# -- Production --
# *** Core image ***
FROM core AS production-core

# Un-privileged user running the application
ARG DOCKER_USER=1000
USER ${DOCKER_USER}

CMD ["uvicorn", \
     "warren.api:app", \
     "--proxy-headers", \
     "--log-config", \
     "core/logging-config.prod.yaml", \
     "--host", \
     "0.0.0.0", \
     "--port", \
     "8000"]

# *** Full image ***
FROM full AS production-full

# Un-privileged user running the application
ARG DOCKER_USER=1000
USER ${DOCKER_USER}

CMD ["uvicorn", \
     "warren.api:app", \
     "--proxy-headers", \
     "--log-config", \
     "core/logging-config.prod.yaml", \
     "--host", \
     "0.0.0.0", \
     "--port", \
     "8000"]
