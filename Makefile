DEV_HUB ?= $(shell \
  if [ -f .dev-hub ]; then sed -n '1p' .dev-hub | tr -d '[:space:]'; \
  elif [ -x ../dev-hub/bin/loop.py ]; then printf '%s' "../dev-hub"; \
  else printf ''; fi)

ifeq ($(strip $(DEV_HUB)),)
$(error DEV_HUB not found. Set DEV_HUB=/path/to/dev-hub, create .dev-hub, or use sibling ../dev-hub)
endif

include $(DEV_HUB)/make/product.mk

SHELL := /bin/bash

.PHONY: local.up local.restart local.down local.build local.rebuild local.ps local.logs docker.restart docker.build docker.rebuild keycloak.seed dev prod prod.up prod.down prod.ps prod.logs prod.smoke prod.edge prod.edge.up prod.edge.down prod.edge.ps prod.edge.logs

local.up:
	bash scripts/docker-up.sh dev up -d --build

docker.build:
	bash scripts/docker-up.sh dev build

docker.rebuild:
	bash scripts/docker-up.sh dev up -d --build --force-recreate

local.build: docker.build
local.rebuild: docker.rebuild

docker.restart:
	bash scripts/docker-up.sh dev restart backend websocket queue-short queue-long scheduler frontend
	bash scripts/docker-up.sh dev exec -T backend bench --site elms.localhost migrate
	bash scripts/docker-up.sh dev exec -T backend bench --site elms.localhost clear-cache

local.restart: docker.restart

local.down:
	bash scripts/docker-up.sh dev down

local.ps:
	bash scripts/docker-up.sh dev ps

local.logs:
	bash scripts/docker-up.sh dev logs --tail=100

keycloak.seed:
	bash scripts/keycloak-seed-users.sh

dev: local.up

prod.up:
	bash scripts/docker-up.sh prod up -d --build

prod.down:
	bash scripts/docker-up.sh prod down

prod.ps:
	bash scripts/docker-up.sh prod ps

prod.logs:
	bash scripts/docker-up.sh prod logs --tail=100

prod: prod.up

prod.smoke:
	bash scripts/infra/compose_smoke.sh --profile staged --dry-run

prod.edge.up:
	@test "$(ELMS_EDGE_APPROVED)" = "1" || (echo "set ELMS_EDGE_APPROVED=1 for owner-approved edge switch" >&2; exit 1)
	@test -n "$(ELMS_EDGE_EVIDENCE)" || (echo "ELMS_EDGE_EVIDENCE must point to fresh predecessor evidence" >&2; exit 1)
	python3 scripts/infra/edge_cutover.py --root . --env-file docker/.env.prod switch --approved --execute --predecessor-evidence "$(ELMS_EDGE_EVIDENCE)"

prod.edge.down:
	@test "$(ELMS_EDGE_APPROVED)" = "1" || (echo "set ELMS_EDGE_APPROVED=1 for owner-approved edge rollback" >&2; exit 1)
	@test -n "$(ELMS_EDGE_EVIDENCE)" || (echo "ELMS_EDGE_EVIDENCE must point to fresh predecessor evidence" >&2; exit 1)
	python3 scripts/infra/edge_cutover.py --root . --env-file docker/.env.prod rollback --approved --execute --predecessor-evidence "$(ELMS_EDGE_EVIDENCE)"

prod.edge.ps:
	bash scripts/docker-up.sh prod-edge ps

prod.edge.logs:
	bash scripts/docker-up.sh prod-edge logs --tail=100

prod.edge: prod.edge.up

copy.ssh: ssh-copy-id -i ~/.ssh/id_rsa.pub root@
