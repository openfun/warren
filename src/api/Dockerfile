# -- Base image --
FROM python:3.11-slim as base

# Upgrade pip to its latest release to speed up dependencies installation
RUN pip install --upgrade pip

# Upgrade system packages to install security updates
RUN apt-get update && \
    apt-get -y upgrade && \
    rm -rf /var/lib/apt/lists/*


# -- Builder --
# Core builder (no plugins installed)
FROM base as core-builder

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
FROM core-builder as full-builder

RUN pip install ./plugins/*

# -- Core --
FROM base as core

COPY --from=core-builder /usr/local /usr/local

# Copy all sources, not only runtime-required files
COPY . /app/

WORKDIR /app

# -- Full --
FROM core as full

COPY --from=full-builder /usr/local /usr/local


# -- Development --
FROM full as development

# Uninstall warren and re-install it in editable mode along with development
# dependencies
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN pip uninstall -y $(pip list | cut -f1 -d " " | grep warren)
RUN pip install -e ./core[dev] && \
    for plugin in ./plugins/*; do \
        pip install -e "${plugin}[dev]"; \
    done

# Un-privileged user running the application
USER ${DOCKER_USER:-1000}


# -- Production --
# *** Core image ***
FROM core as production-core

# Un-privileged user running the application
USER ${DOCKER_USER:-1000}

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
FROM full as production-full

# Un-privileged user running the application
USER ${DOCKER_USER:-1000}

CMD ["uvicorn", \
     "warren.api:app", \
     "--proxy-headers", \
     "--log-config", \
     "core/logging-config.prod.yaml", \
     "--host", \
     "0.0.0.0", \
     "--port", \
     "8000"]
