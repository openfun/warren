# -- General
SHELL := /bin/bash

# -- Docker
# Get the current user ID to use for docker run and docker exec commands
DOCKER_UID           = $(shell id -u)
DOCKER_GID           = $(shell id -g)
DOCKER_USER          = $(DOCKER_UID):$(DOCKER_GID)
COMPOSE              = DOCKER_USER=$(DOCKER_USER) docker compose
COMPOSE_RUN          = $(COMPOSE) run --rm --no-deps
COMPOSE_RUN_BACKEND  = $(COMPOSE_RUN) backend
COMPOSE_RUN_FRONTEND = $(COMPOSE_RUN) frontend

# -- Potsie
POTSIE_RELEASE = 0.6.0

# -- Elasticsearch
ES_PROTOCOL        = http
ES_HOST            = localhost
ES_COMPOSE_SERVICE = elasticsearch
ES_PORT            = 9200
ES_INDEX           = statements
ES_URL             = $(ES_PROTOCOL)://$(ES_HOST):$(ES_PORT)
ES_COMPOSE_URL     = $(ES_PROTOCOL)://$(ES_COMPOSE_SERVICE):$(ES_PORT)

# -- WARREN
WARREN_BACKEND_IMAGE_NAME          ?= warren-backend
WARREN_BACKEND_IMAGE_TAG           ?= development
WARREN_BACKEND_IMAGE_BUILD_TARGET  ?= development
WARREN_BACKEND_SERVER_PORT         ?= 8100
WARREN_FRONTEND_IMAGE_NAME         ?= warren-frontend
WARREN_FRONTEND_IMAGE_TAG          ?= development
WARREN_FRONTEND_IMAGE_BUILD_TARGET ?= development
WARREN_FRONTEND_SERVER_PORT        ?= 3000
WARREN_FRONTEND_DOCS_PORT          ?= 3001


# ==============================================================================
# RULES

default: help

.env:
	cp .env.dist .env

bin/patch_statements_date.py:
	curl \
		https://raw.githubusercontent.com/openfun/potsie/v$(POTSIE_RELEASE)/scripts/patch_statements_date.py \
		-o bin/patch_statements_date.py

data/statements.jsonl.gz:
	mkdir -p data
	curl \
		https://raw.githubusercontent.com/openfun/potsie/v$(POTSIE_RELEASE)/fixtures/elasticsearch/lrs.json.gz \
		-o data/statements.jsonl.gz

# -- Docker/compose
bootstrap: ## bootstrap the project for development
bootstrap: \
  .env \
  bin/patch_statements_date.py \
  data/statements.jsonl.gz \
  build \
  fixtures
.PHONY: bootstrap

build: ## build the app containers
build: \
  build-docker-backend \
  build-docker-frontend
.PHONY: build

build-docker-backend: ## build the backend container
build-docker-backend: .env
	WARREN_BACKEND_IMAGE_BUILD_TARGET=$(WARREN_BACKEND_IMAGE_BUILD_TARGET) \
	WARREN_BACKEND_IMAGE_NAME=$(WARREN_BACKEND_IMAGE_NAME) \
	WARREN_BACKEND_IMAGE_TAG=$(WARREN_BACKEND_IMAGE_TAG) \
	  $(COMPOSE) build backend
.PHONY: build-docker-backend

build-docker-frontend: ## build the frontend container
build-docker-frontend: .env
	WARREN_FRONTEND_IMAGE_BUILD_TARGET=$(WARREN_FRONTEND_IMAGE_BUILD_TARGET) \
	WARREN_FRONTEND_IMAGE_NAME=$(WARREN_FRONTEND_IMAGE_NAME) \
	WARREN_FRONTEND_IMAGE_TAG=$(WARREN_FRONTEND_IMAGE_TAG) \
	  $(COMPOSE) build frontend
	@$(COMPOSE_RUN_FRONTEND) yarn install
.PHONY: build-docker-frontend

build-frontend: ## build the frontend application
	@$(COMPOSE_RUN_FRONTEND) yarn build
.PHONY: build-frontend

down: ## stop and remove backend containers
	@$(COMPOSE) down
.PHONY: down

logs-backend: ## display backend logs (follow mode)
	@$(COMPOSE) logs -f backend
.PHONY: logs-backend

logs-frontend: ## display frontend logs (follow mode)
	@$(COMPOSE) logs -f frontend
.PHONY: logs-frontend

logs: ## display frontend/backend logs (follow mode)
	@$(COMPOSE) logs -f backend frontend
.PHONY: logs

run: ## run the whole stack
run: run-frontend
.PHONY: run

run-backend: ## run the backend server (development mode)
	@$(COMPOSE) up -d backend
	@echo "Waiting for backend to be up and running..."
	@$(COMPOSE_RUN) dockerize -wait tcp://$(ES_COMPOSE_SERVICE):$(ES_PORT) -timeout 60s
	@$(COMPOSE_RUN) dockerize -wait tcp://backend:$(WARREN_BACKEND_SERVER_PORT) -timeout 60s
.PHONY: run-backend

run-frontend: ## run the frontend server (development mode)
run-frontend: run-backend
	@$(COMPOSE) up -d frontend
	@echo "Waiting for frontend to be up and running..."
	@$(COMPOSE_RUN) dockerize -wait tcp://frontend:$(WARREN_FRONTEND_SERVER_PORT) -timeout 60s
	@$(COMPOSE_RUN) dockerize -wait tcp://frontend:$(WARREN_FRONTEND_DOCS_PORT) -timeout 60s
.PHONY: run-frontend

status: ## an alias for "docker compose ps"
	@$(COMPOSE) ps
.PHONY: status

stop: ## stop backend server
	@$(COMPOSE) stop
.PHONY: stop

# -- Provisioning
fixtures: ## load test data
fixtures: \
  bin/patch_statements_date.py \
  data/statements.jsonl.gz \
	run-backend
	curl -X DELETE "$(ES_URL)/$(ES_INDEX)?pretty" || true
	curl -X PUT "$(ES_URL)/$(ES_INDEX)?pretty"
	curl -X PUT $(ES_URL)/$(ES_INDEX)/_settings \
		-H 'Content-Type: application/json' \
		-d '{"index": {"number_of_replicas": 0}}'
	zcat < data/statements.jsonl.gz | \
		$(COMPOSE) exec -T backend python /opt/src/patch_statements_date.py | \
		sed "s/@timestamp/timestamp/g" | \
		$(COMPOSE_RUN) -T ralph ralph push \
	    --backend es \
	    --es-index "$(ES_INDEX)" \
	    --es-hosts "$(ES_COMPOSE_URL)" \
	    --chunk-size 300 \
	    --es-op-type create
.PHONY: fixtures


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
  lint-pydocstyle \
	lint-frontend
.PHONY: lint

### Backend ###

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

### Frontend ###

lint-frontend: ## lint frontend sources
	@echo 'lint:frontend started…'
	@$(COMPOSE_RUN_FRONTEND) yarn lint
.PHONY: lint-frontend

format-frontend: ## use prettier to format frontend sources
	@echo 'format:frontend started…'
	@$(COMPOSE_RUN_FRONTEND) yarn format
.PHONY: format-frontend

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
