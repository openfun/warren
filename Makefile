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
COMPOSE_RUN_APP      = $(COMPOSE_RUN) app
MANAGE               = $(COMPOSE_RUN_APP) python manage.py

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

# -- Ralph
RALPH_COMPOSE_SERVICE = ralph
RALPH_RUNSERVER_PORT ?= 8200
RALPH_LRS_AUTH_USER_NAME  = ralph
RALPH_LRS_AUTH_USER_PWD   = secret
RALPH_LRS_AUTH_USER_SCOPE = ralph_scope

# -- Postgresql
DB_HOST            = postgresql
DB_PORT            = 5432

# -- WARREN
WARREN_APP_IMAGE_NAME          		 ?= warren-app
WARREN_APP_IMAGE_TAG           		 ?= development
WARREN_APP_IMAGE_BUILD_TARGET  		 ?= development
WARREN_APP_SERVER_PORT         		 ?= 8090
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

.ralph/auth.json:
	@$(COMPOSE_RUN) ralph ralph \
		auth \
		-u $(RALPH_LRS_AUTH_USER_NAME) \
		-p $(RALPH_LRS_AUTH_USER_PWD) \
		-s $(RALPH_LRS_AUTH_USER_SCOPE) \
		-w

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
  .ralph/auth.json \
  bin/patch_statements_date.py \
  data/statements.jsonl.gz \
  build \
  migrate-app \
  fixtures
.PHONY: bootstrap

build: ## build the app containers
build: \
  build-docker-app \
  build-docker-backend \
  build-docker-frontend
.PHONY: build

build-docker-app: ## build the app container
build-docker-app: .env
	WARREN_APP_IMAGE_BUILD_TARGET=$(WARREN_APP_IMAGE_BUILD_TARGET) \
	WARREN_APP_IMAGE_NAME=$(WARREN_APP_IMAGE_NAME) \
	WARREN_APP_IMAGE_TAG=$(WARREN_APP_IMAGE_TAG) \
	  $(COMPOSE) build app
.PHONY: build-docker-app

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
	@$(COMPOSE) logs -f app backend frontend
.PHONY: logs

run: ## run the whole stack
run: run-frontend
.PHONY: run

run-app: ## run the app server (development mode)
	@$(COMPOSE) up -d app
	@echo "Waiting for the app to be up and running..."
	@$(COMPOSE_RUN) dockerize -wait tcp://$(DB_HOST):$(DB_PORT) -timeout 60s
	@$(COMPOSE_RUN) dockerize -wait tcp://app:$(WARREN_APP_SERVER_PORT) -timeout 60s
.PHONY: run-app

run-backend: ## run the backend server (development mode)
	@$(COMPOSE) up -d backend
	@echo "Waiting for backend to be up and running..."
	@$(COMPOSE_RUN) dockerize -wait tcp://$(ES_COMPOSE_SERVICE):$(ES_PORT) -timeout 60s
	@$(COMPOSE_RUN) dockerize -wait http://$(RALPH_COMPOSE_SERVICE):$(RALPH_RUNSERVER_PORT)/__heartbeat__ -timeout 60s
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


migrate-app:  ## run django migration for the sandbox project.
	@echo "Running migrations..."
	@$(COMPOSE) up -d postgresql
	@$(COMPOSE_RUN) dockerize -wait tcp://$(DB_HOST):$(DB_PORT) -timeout 60s
	@$(MANAGE) migrate
.PHONY: migrate-app

# -- Linters
lint: ## lint backend, app and frontend sources
lint: \
  lint-backend \
  lint-app \
  lint-frontend
.PHONY: lint

### Backend ###

lint-backend: ## lint backend python sources
lint-backend: \
  lint-backend-black \
  lint-backend-ruff
.PHONY: lint-backend

lint-backend-black: ## lint backend python sources with black
	@echo 'lint-backend:black started…'
	@$(COMPOSE_RUN_BACKEND) black --config core/pyproject.toml core plugins
.PHONY: lint-backend-black

lint-backend-ruff: ## lint backend python sources with ruff
	@echo 'lint-backend:ruff started…'
	@$(COMPOSE_RUN_BACKEND) ruff --config core/pyproject.toml core plugins
.PHONY: lint-backend-ruff

lint-backend-ruff-fix: ## lint and fix backend python sources with ruff
	@echo 'lint-backend:ruff-fix started…'
	@$(COMPOSE_RUN_BACKEND) ruff --config core/pyproject.toml core plugins --fix
.PHONY: lint-backend-ruff-fix

### App ###

lint-app: ## lint app python sources
lint-app: \
  lint-app-black \
  lint-app-ruff
.PHONY: lint-app

lint-app-black: ## lint app python sources with black
	@echo 'lint-app:black started…'
	@$(COMPOSE_RUN_APP) black --config ./pyproject.toml apps warren manage.py
.PHONY: lint-app-black

lint-app-ruff: ## lint app python sources with ruff
	@echo 'lint-app:ruff started…'
	@$(COMPOSE_RUN_APP) ruff --config ./pyproject.toml apps warren manage.py
.PHONY: lint-app-ruff

lint-app-ruff-fix: ## lint and fix app python sources with ruff
	@echo 'lint-app:ruff-fix started…'
	@$(COMPOSE_RUN_APP) ruff --config ./pyproject.toml apps warren manage.py --fix
.PHONY: lint-app-ruff-fix

### Frontend ###

lint-frontend: ## lint frontend sources
	@echo 'lint-frontend:linter started…'
	@$(COMPOSE_RUN_FRONTEND) yarn lint
.PHONY: lint-frontend

format-frontend: ## use prettier to format frontend sources
	@echo 'format-frontend: started…'
	@$(COMPOSE_RUN_FRONTEND) yarn format
.PHONY: format-frontend

## -- Tests

test: ## run tests
test: \
  test-backend \
  test-app
.PHONY: test

test-backend: ## run backend tests
test-backend: run-backend
	@$(COMPOSE_RUN_BACKEND) pytest
.PHONY: test-backend

test-app: ## run app tests
test-app: run-app
	@$(COMPOSE_RUN_APP) pytest
.PHONY: test-app

# -- Misc
help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help

jupytext--to-md: ## convert local ipynb files into md
	bin/jupytext --to md work/**/*.ipynb
.PHONY: jupytext--to-md

jupytext--to-ipynb: ## convert remote md files into ipynb
	bin/jupytext --to ipynb work/**/*.md
.PHONY: jupytext--to-ipynb

