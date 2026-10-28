DEV_HUB ?= $(abspath $(CURDIR)/../dev-hub)
-include $(DEV_HUB)/make/product.mk

SHELL := /bin/bash

.PHONY: local.up local.down local.ps local.logs dev prod

local.up:
	bash scripts/docker-up.sh dev up -d --build

local.down:
	bash scripts/docker-up.sh dev down

local.ps:
	bash scripts/docker-up.sh dev ps

local.logs:
	bash scripts/docker-up.sh dev logs --tail=100

dev: local.up

prod:
	bash scripts/docker-up.sh prod up -d --build
