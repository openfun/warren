# -- Base image --
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1

# Upgrade pip to its latest release to speed up dependencies installation
RUN pip install --upgrade pip

# ---- Back-end builder image ----
FROM base AS builder

WORKDIR /builder

# Copy required python dependencies
COPY . /builder/

RUN mkdir /install && \
    pip install --prefix=/install .

# ---- Core application image ----
FROM base AS core

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

WORKDIR /app

# Collect static files
RUN DJANGO_CONFIGURATION=Build python manage.py collectstatic --noinput

# Prepare production run using gunicorn
RUN mkdir -p /usr/local/etc/gunicorn
COPY ./docker/files/usr/local/etc/gunicorn/warren.py /usr/local/etc/gunicorn/warren.py

# Un-privileged user running the application
ARG DOCKER_USER=1000
USER ${DOCKER_USER}

# ---- Development image ----
FROM core AS development

# Switch to privileged user to uninstall app
USER root:root

# Uninstall warren and re-install it in editable mode along with development
# dependencies
RUN pip uninstall -y warren
RUN pip install -e .[dev]

# Switch back to Un-privileged user to run the application
ARG DOCKER_USER=1000
USER ${DOCKER_USER}

# Run django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8090"]

# ---- Production image ----
FROM core AS production

# The default command runs gunicorn WSGI server
CMD ["gunicorn", "-c", "/usr/local/etc/gunicorn/warren.py", "warren.wsgi:application"]
