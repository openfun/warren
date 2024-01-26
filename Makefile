# -- General
SHELL := /bin/bash

# -- Docker
COMPOSE              = bin/compose
COMPOSE_RUN          = $(COMPOSE) run --rm --no-deps
COMPOSE_RUN_API      = $(COMPOSE_RUN) api
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
RALPH_COMPOSE_SERVICE     = ralph
RALPH_RUNSERVER_PORT     ?= 8200
RALPH_LRS_AUTH_USER_NAME  = ralph
RALPH_LRS_AUTH_USER_PWD   = secret
RALPH_LRS_AUTH_USER_SCOPE = ralph_scope

# -- Postgresql
DB_HOST = postgresql
DB_PORT = 5432

# -- Warren
WARREN_APP_IMAGE_NAME              ?= warren
WARREN_APP_IMAGE_TAG               ?= app-development
WARREN_APP_IMAGE_BUILD_TARGET      ?= development
WARREN_APP_SERVER_PORT             ?= 8090
WARREN_API_IMAGE_NAME              ?= warren
WARREN_API_IMAGE_TAG               ?= api-development
WARREN_API_IMAGE_BUILD_TARGET      ?= development
WARREN_API_SERVER_PORT             ?= 8100
WARREN_API_TEST_DB_NAME            ?= test-warren-api
WARREN_FRONTEND_IMAGE_NAME         ?= warren
WARREN_FRONTEND_IMAGE_TAG          ?= frontend-development
WARREN_FRONTEND_IMAGE_BUILD_TARGET ?= development
WARREN_FRONTEND_IMAGE_BUILD_PATH   ?= app/staticfiles/warren/assets/index.js

# -- Documentation
WARREN_DOCS_SERVER_PORT = 8000
WARREN_DOCS_MIKE_PORT   = 8001
WARREN_DOCS_ENV         = \
													WARREN_DOCS_SERVER_PORT=$(WARREN_DOCS_SERVER_PORT) \
													WARREN_DOCS_MIKE_PORT=$(WARREN_DOCS_MIKE_PORT)
MKDOCS                  = $(WARREN_DOCS_ENV) $(COMPOSE_RUN) docs mkdocs
MIKE                    = $(WARREN_DOCS_ENV) $(COMPOSE_RUN) docs mike


# ==============================================================================
# RULES

default: help

.env:
	cp .env.dist .env

.git/hooks/pre-commit:
	ln -sf ../../bin/git-hook-pre-commit .git/hooks/pre-commit

git-hook-pre-commit:  ## Install git pre-commit hook
git-hook-pre-commit: .git/hooks/pre-commit
	@echo "Git pre-commit hook linked"
.PHONY: git-hook-pre-commit

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
  migrate-api \
  create-api-test-db \
  migrate-app \
  fixtures \
  seed-experience-index
.PHONY: bootstrap

build: ## build the app containers
build: \
  build-docker-app \
  build-docker-api \
  build-docker-docs \
  build-docker-frontend
.PHONY: build

build-docker-app: ## build the app container
build-docker-app: \
  .env \
  build-docker-frontend \
  build-frontend
	WARREN_APP_IMAGE_BUILD_TARGET=$(WARREN_APP_IMAGE_BUILD_TARGET) \
	WARREN_APP_IMAGE_NAME=$(WARREN_APP_IMAGE_NAME) \
	WARREN_APP_IMAGE_TAG=$(WARREN_APP_IMAGE_TAG) \
	  $(COMPOSE) build app
.PHONY: build-docker-app

build-docker-api: ## build the api container
build-docker-api: .env
	WARREN_API_IMAGE_BUILD_TARGET=$(WARREN_API_IMAGE_BUILD_TARGET) \
	WARREN_API_IMAGE_NAME=$(WARREN_API_IMAGE_NAME) \
	WARREN_API_IMAGE_TAG=$(WARREN_API_IMAGE_TAG) \
	  $(COMPOSE) build api
.PHONY: build-docker-api

build-docker-docs: ## build the docs container
	$(COMPOSE) build docs
.PHONY: build-docker-docs

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

down: ## stop and remove all containers
	@$(COMPOSE) down
.PHONY: down

logs-api: ## display api logs (follow mode)
	@$(COMPOSE) logs -f api
.PHONY: logs-api

logs-frontend: ## display frontend logs (follow mode)
	@$(COMPOSE) logs -f frontend
.PHONY: logs-frontend

logs: ## display frontend/api logs (follow mode)
	@$(COMPOSE) logs -f app api frontend
.PHONY: logs

run: ## run the whole stack
run: run-app
.PHONY: run

run-app: ## run the app server (development mode)
	@$(COMPOSE) up -d app
	@echo "Waiting for the app to be up and running..."
	@$(COMPOSE_RUN) dockerize -wait tcp://$(DB_HOST):$(DB_PORT) -timeout 60s
	@$(COMPOSE_RUN) dockerize -wait tcp://app:$(WARREN_APP_SERVER_PORT) -timeout 60s
	@$(COMPOSE_RUN) dockerize -wait file:///$(WARREN_FRONTEND_IMAGE_BUILD_PATH) -timeout 60s
.PHONY: run-app

run-api: ## run the api server (development mode)
	@$(COMPOSE) up -d api
	@echo "Waiting for api to be up and running..."
	@$(COMPOSE_RUN) dockerize -wait tcp://$(DB_HOST):$(DB_PORT) -timeout 60s
	@$(COMPOSE_RUN) dockerize -wait http://$(RALPH_COMPOSE_SERVICE):$(RALPH_RUNSERVER_PORT)/__heartbeat__ -timeout 60s
	@$(COMPOSE_RUN) dockerize -wait tcp://api:$(WARREN_API_SERVER_PORT) -timeout 60s
.PHONY: run-api

status: ## an alias for "docker compose ps"
	@$(COMPOSE) ps
.PHONY: status

stop: ## stop all servers
	@$(COMPOSE) stop
.PHONY: stop

# -- Provisioning
create-api-test-db: ## create API test database
	@$(COMPOSE) exec postgresql bash -c 'psql "postgresql://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@$(DB_HOST):$(DB_PORT)/postgres" -c "create database \"$(WARREN_API_TEST_DB_NAME)\";"' || echo "Duly noted, skipping database creation."
.PHONY: create-api-test-db

drop-api-test-db: ## drop API test database
	@$(COMPOSE) exec postgresql bash -c 'psql "postgresql://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@$(DB_HOST):$(DB_PORT)/postgres" -c "drop database \"$(WARREN_API_TEST_DB_NAME)\";"' || echo "Duly noted, skipping database deletion."
.PHONY: drop-api-test-db

fixtures: ## load test data
fixtures: \
  bin/patch_statements_date.py \
  data/statements.jsonl.gz \
	run-api
	curl -X DELETE "$(ES_URL)/$(ES_INDEX)?pretty" || true
	curl -X PUT "$(ES_URL)/$(ES_INDEX)?pretty"
	curl -X PUT $(ES_URL)/$(ES_INDEX)/_settings \
		-H 'Content-Type: application/json' \
		-d '{"index": {"number_of_replicas": 0}}'
	zcat < data/statements.jsonl.gz | \
		$(COMPOSE) exec -T api python /opt/src/patch_statements_date.py | \
		sed "s/@timestamp/timestamp/g" | \
		$(COMPOSE_RUN) -T ralph ralph push \
	    --backend es \
	    --es-index "$(ES_INDEX)" \
	    --es-hosts "$(ES_COMPOSE_URL)" \
	    --chunk-size 300 \
	    --es-op-type create
.PHONY: fixtures

seed-experience-index:  ## seed the experience index with test data
	@echo "Seeding the experience index…"
	@$(COMPOSE) exec -T api python /opt/src/seed_experience_index.py
.PHONY: seed-experience-index

migrate-api:  ## run alembic database migrations for the api service
	@echo "Running api service database engine…"
	@$(COMPOSE) up -d postgresql
	@$(COMPOSE_RUN) dockerize -wait tcp://$(DB_HOST):$(DB_PORT) -timeout 60s
	@echo "Create api service database…"
	@$(COMPOSE) exec postgresql bash -c 'psql "postgresql://$${POSTGRES_USER}:$${POSTGRES_PASSWORD}@$(DB_HOST):$(DB_PORT)/postgres" -c "create database \"warren-api\";"' || echo "Duly noted, skipping database creation."
	@echo "Running migrations for api service…"
	@bin/alembic upgrade head
.PHONY: migrate-api

migrate-app:  ## run django database migrations for the app service
	@echo "Running app service database engine…"
	@$(COMPOSE) up -d postgresql
	@$(COMPOSE_RUN) dockerize -wait tcp://$(DB_HOST):$(DB_PORT) -timeout 60s
	@echo "Running migrations for app service…"
	@$(MANAGE) migrate
.PHONY: migrate-app

check-django:  ## Run the Django "check" command
	@echo "Checking django…"
	@$(MANAGE) check
.PHONY: check-django

create-superuser:  ## Create a new superuser
	@echo "Creating superuser…"
	@$(MANAGE) createsuperuser
.PHONY: create-superuser

make-migrations:  ## Generate potential migrations
	@echo "Generating potential migrations…"
	@$(MANAGE) makemigrations
.PHONY: make-migrations

check-migrations:  ## Check that all needed migrations exist
	@echo "Checking migrations…"
	@$(MANAGE) makemigrations --check --dry-run
.PHONY: check-migrations

# -- Linters
lint: ## lint api, app and frontend sources
lint: \
  lint-api \
  lint-app \
  lint-frontend \
  lint-docs
.PHONY: lint

### API ###

lint-api: ## lint api python sources
lint-api: \
  lint-api-black \
  lint-api-ruff \
  lint-api-mypy
.PHONY: lint-api

lint-api-black: ## lint api python sources with black
	@echo 'lint-api:black started…'
	@$(COMPOSE_RUN_API) black --config core/pyproject.toml core plugins
.PHONY: lint-api-black

lint-api-ruff: ## lint api python sources with ruff
	@echo 'lint-api:ruff started…'
	@$(COMPOSE_RUN_API) ruff --config core/pyproject.toml core plugins
.PHONY: lint-api-ruff

lint-api-ruff-fix: ## lint and fix api python sources with ruff
	@echo 'lint-api:ruff-fix started…'
	@$(COMPOSE_RUN_API) ruff --config core/pyproject.toml core plugins --fix
.PHONY: lint-api-ruff-fix

lint-api-mypy: ## lint api python sources with mypy
	@echo 'lint-api:mypy started…'
	@$(COMPOSE_RUN_API) mypy --config-file core/pyproject.toml core plugins
.PHONY: lint-api-mypy

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

clean-frontend: ## clean node_modules and old build
	cd src/frontend && find . -name node_modules | xargs rm -fr
.PHONY: clean-frontend

## -- Tests

test: ## run tests
test: \
  test-api \
  test-app
.PHONY: test

test-api: ## run api tests
test-api: \
  run-api \
  create-api-test-db
	bin/pytest
.PHONY: test-api

test-app: ## run app tests
test-app: run-app
	PYTEST_SERVICE=app bin/pytest
.PHONY: test-app

## -- Docs
docs-build: ## build documentation site
	$(MKDOCS) build
.PHONY: docs-build

docs-deploy: ## build and deploy documentation site for all versions
	@echo "Deploying docs with version main to gh-pages"
	@$(MIKE) deploy main
.PHONY: docs-deploy

lint-docs: ## lint the documentation sources
	$(COMPOSE_RUN) prettier -c docs/**/*.md
.PHONY: docs-lint

lint-docs-fix: ## fix linter issues for documentation sources
	$(COMPOSE_RUN) prettier -w docs/**/*.md
.PHONY: docs-lint

docs-serve: ## run mkdocs live server for dev docs
	$(WARREN_DOCS_ENV) $(COMPOSE) up docs
.PHONY: docs-serve

docs-serve-pages: ## run mike live server for versioned docs
	$(WARREN_DOCS_ENV) $(COMPOSE) up mike
.PHONY: docs-serve-pages


# -- Misc
help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help

clean: ## restore repository state as it was freshly cloned
	git clean -idx
.PHONY: clean

jupytext--to-md: ## convert local ipynb files into md
	bin/jupytext --to md work/*.ipynb
.PHONY: jupytext--to-md

jupytext--to-ipynb: ## convert remote md files into ipynb
	bin/jupytext --to ipynb work/*.md
.PHONY: jupytext--to-ipynb

