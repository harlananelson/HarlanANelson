#!/bin/bash
set -e
QUARTO_VERSION="1.8.26"
curl -fsSL "https://github.com/quarto-dev/quarto-cli/releases/download/v${QUARTO_VERSION}/quarto-${QUARTO_VERSION}-linux-amd64.tar.gz" | tar xz
export PATH="$PWD/quarto-${QUARTO_VERSION}/bin:$PATH"
quarto render
