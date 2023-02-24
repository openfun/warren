# -- General
SHELL := /bin/bash

# -- Docker
# Get the current user ID to use for docker run and docker exec commands
DOCKER_UID           = $(shell id -u)
DOCKER_GID           = $(shell id -g)
DOCKER_USER          = $(DOCKER_UID):$(DOCKER_GID)
COMPOSE              = DOCKER_USER=$(DOCKER_USER) docker compose
COMPOSE_RUN          = $(COMPOSE) run --rm
COMPOSE_RUN_BACKEND  = $(COMPOSE_RUN) backend

# -- Elasticsearch
ES_PROTOCOL = http
ES_HOST     = localhost
ES_PORT     = 9200
ES_INDEX    = statements
ES_URL      = $(ES_PROTOCOL)://$(ES_HOST):$(ES_PORT)

# -- WARREN
WARREN_BACKEND_IMAGE_NAME         ?= warren-backend
WARREN_BACKEND_IMAGE_TAG          ?= development
WARREN_BACKEND_IMAGE_BUILD_TARGET ?= development
WARREN_BACKEND_SERVER_PORT        ?= 8100


# ==============================================================================
# RULES

default: help

.env:
	cp .env.dist .env


# -- Docker/compose
bootstrap: ## bootstrap the project for development
bootstrap: \
  .env \
  build
.PHONY: bootstrap

build: ## build the app container
build: .env
	WARREN_BACKEND_IMAGE_BUILD_TARGET=$(WARREN_BACKEND_IMAGE_BUILD_TARGET) \
	WARREN_BACKEND_IMAGE_NAME=$(WARREN_BACKEND_IMAGE_NAME) \
	WARREN_BACKEND_IMAGE_TAG=$(WARREN_BACKEND_IMAGE_TAG) \
	  $(COMPOSE) build backend
.PHONY: build

down: ## stop and remove backend containers
	@$(COMPOSE) down
.PHONY: down

logs-backend: ## display backend logs (follow mode)
	@$(COMPOSE) logs -f backend
.PHONY: logs-backend

run: ## run the whole stack
run: run-backend
.PHONY: run

run-backend: ## run the backend server (development mode)
	@$(COMPOSE) up -d backend
	@echo "Waiting for backend to be up and running..."
	@$(COMPOSE_RUN) dockerize -wait tcp://backend:$(WARREN_BACKEND_SERVER_PORT) -timeout 60s
.PHONY: run-backend

status: ## an alias for "docker compose ps"
	@$(COMPOSE) ps
.PHONY: status

stop: ## stop backend server
	@$(COMPOSE) stop
.PHONY: stop

# -- Linters
#
# Nota bene: Black should come after isort just in case they don't agree...
lint: ## lint backend python sources
lint: \
  lint-isort \
  lint-black \
  lint-flake8 \
  lint-pylint \
  lint-bandit \
  lint-pydocstyle
.PHONY: lint

lint-black: ## lint backend python sources with black
	@echo 'lint:black started…'
	@$(COMPOSE_RUN_BACKEND) black .
.PHONY: lint-black

lint-flake8: ## lint backend python sources with flake8
	@echo 'lint:flake8 started…'
	@$(COMPOSE_RUN_BACKEND) flake8
.PHONY: lint-flake8

lint-isort: ## automatically re-arrange python imports in backend code base
	@echo 'lint:isort started…'
	@$(COMPOSE_RUN_BACKEND) isort --atomic .
.PHONY: lint-isort

lint-pylint: ## lint backend python sources with pylint
	@echo 'lint:pylint started…'
	@$(COMPOSE_RUN_BACKEND) pylint warren tests
.PHONY: lint-pylint

lint-bandit: ## lint backend python sources with bandit
	@echo 'lint:bandit started…'
	@$(COMPOSE_RUN_BACKEND) bandit -qr warren
.PHONY: lint-bandit

lint-pydocstyle: ## lint Python docstrings with pydocstyle
	@echo 'lint:pydocstyle started…'
	@$(COMPOSE_RUN_BACKEND) pydocstyle
.PHONY: lint-pydocstyle

## -- Tests

test: ## run tests
test: test-backend
.PHONY: test

test-backend: ## run backend tests
test-backend: run-backend
	bin/pytest
.PHONY: test

# -- Misc
help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help
