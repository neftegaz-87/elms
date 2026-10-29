DEV_HUB ?= $(abspath $(CURDIR)/../dev-hub)
-include $(DEV_HUB)/make/product.mk

SHELL := /bin/bash

.PHONY: local.up local.down local.ps local.logs dev prod prod.up prod.down prod.ps prod.logs

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
