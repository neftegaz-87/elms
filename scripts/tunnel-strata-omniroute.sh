#!/usr/bin/env bash
set -euo pipefail
pkill -f "ssh .* -L 0.0.0.0:18080:127.0.0.1:8080 vps-deploy" 2>/dev/null || true
sleep 1
ssh -fN -o BatchMode=yes -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -L 0.0.0.0:18080:127.0.0.1:8080 vps-deploy
ss -ltn | grep 18080
echo "tunnel OK: host:18080 -> vps-deploy:8080 (OmniRoute uses http://172.17.0.1:18080/v1)"
