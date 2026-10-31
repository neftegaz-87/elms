DEV_HUB ?= $(abspath $(CURDIR)/../dev-hub)
-include $(DEV_HUB)/make/product.mk

SHELL := /bin/bash

.PHONY: local.up local.down local.ps local.logs dev prod prod.up prod.down prod.ps prod.logs prod.smoke prod.edge prod.edge.up prod.edge.down prod.edge.ps prod.edge.logs

local.up:
	bash scripts/docker-up.sh dev up -d --build

local.down:
	bash scripts/docker-up.sh dev down

local.ps:
	bash scripts/docker-up.sh dev ps

local.logs:
	bash scripts/docker-up.sh dev logs --tail=100

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
