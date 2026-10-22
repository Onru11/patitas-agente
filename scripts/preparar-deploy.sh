#!/usr/bin/env bash
# Copia a dist/ solo lo que debe ser público.
set -e
cd "$(dirname "$0")/.."
rm -rf dist && mkdir -p dist/data
cp index.html robots.txt sitemap.xml og-image.png dist/
cp -R assets dist/
cp data/datos.json dist/data/
echo "dist/ listo"
