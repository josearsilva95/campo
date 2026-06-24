#!/usr/bin/env bash
set -e
pip install -r requirements.txt
# Grava o hash do commit atual para cache-busting de CSS/JS em produção
git rev-parse --short HEAD > static/version.txt
echo "Build concluído. Versão: $(cat static/version.txt)"
