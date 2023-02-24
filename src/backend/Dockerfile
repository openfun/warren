# -- Base image --
FROM python:3.11-slim as base

# Upgrade pip to its latest release to speed up dependencies installation
RUN pip install --upgrade pip

# Upgrade system packages to install security updates
RUN apt-get update && \
    apt-get -y upgrade && \
    rm -rf /var/lib/apt/lists/*


# -- Builder --
FROM base as builder

WORKDIR /build

COPY . /build/

RUN apt-get update && \
    apt-get install -y \
        build-essential \
        gcc \
        libc6-dev \
        libffi-dev \
        python-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install .


# -- Core --
FROM base as core

COPY --from=builder /usr/local /usr/local

# Copy all sources, not only runtime-required files
COPY . /app/

WORKDIR /app


# -- Development --
FROM core as development

# Uninstall warren and re-install it in editable mode along with development
# dependencies
RUN pip uninstall -y warren
RUN pip install -e .[dev]

# Un-privileged user running the application
USER ${DOCKER_USER:-1000}


# -- Production --
FROM core as production

# Un-privileged user running the application
USER ${DOCKER_USER:-1000}

CMD ["uvicorn", \
     "warren.api:app", \
     "--proxy-headers", \
     "--host", \
     "0.0.0.0", \
     "--port", \
     "8000"]
