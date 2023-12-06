# -- Base image --
FROM python:3.12-slim as base

ENV PYTHONUNBUFFERED=1

# Upgrade pip to its latest release to speed up dependencies installation
RUN pip install --upgrade pip

# ---- Back-end builder image ----
FROM base as builder

WORKDIR /builder

# Copy required python dependencies
COPY . /builder/

RUN mkdir /install && \
    pip install --prefix=/install .

# ---- Core application image ----
FROM base as core

# Install gettext
RUN apt-get update && \
    apt-get install -y \
    gettext && \
    rm -rf /var/lib/apt/lists/*

# Copy installed python dependencies
COPY --from=builder /install /usr/local

# Copy runtime-required files
COPY . /app/

# Clean up frontend static files
# Nota bene: it requires that the frontend application to be already built
RUN rm -fr /app/staticfiles/warren/* && mkdir -p /app/staticfiles/warren/assets/
COPY ./staticfiles/warren/assets/index.js \
        ./staticfiles/warren/assets/index-*.js \
        ./staticfiles/warren/assets/index.css \
        /app/staticfiles/warren/assets/

# Prepare production run using gunicorn
RUN mkdir -p /usr/local/etc/gunicorn
COPY ./docker/files/usr/local/etc/gunicorn/warren.py /usr/local/etc/gunicorn/warren.py

WORKDIR /app

# Un-privileged user running the application
USER ${DOCKER_USER:-1000}

# ---- Development image ----
FROM core as development

# Switch to privileged user to uninstall app
USER root:root

# Uninstall warren and re-install it in editable mode along with development
# dependencies
RUN pip uninstall -y warren
RUN pip install -e .[dev]

# Switch back to Un-privileged user to run the application
USER ${DOCKER_USER:-1000}

# Run django development server
CMD python manage.py runserver 0.0.0.0:${WARREN_APP_SERVER_PORT:-8090}

# ---- Production image ----
from core as production

# The default command runs gunicorn WSGI server
CMD gunicorn -c /usr/local/etc/gunicorn/warren.py warren.wsgi:application
