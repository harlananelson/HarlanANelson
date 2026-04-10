#!/bin/bash
set -e
QUARTO_VERSION="1.8.26"
QUARTO_DIR="/tmp/quarto-install"
mkdir -p "$QUARTO_DIR"
curl -fsSL "https://github.com/quarto-dev/quarto-cli/releases/download/v${QUARTO_VERSION}/quarto-${QUARTO_VERSION}-linux-amd64.tar.gz" | tar xz -C "$QUARTO_DIR"
export PATH="$QUARTO_DIR/quarto-${QUARTO_VERSION}/bin:$PATH"
quarto render
