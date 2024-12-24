#!/bin/bash

set -e

if [ -d fonts ]; then
  echo "fonts directory already exists"
  exit 1
fi

TTF_DIR="fonts/NotoSans/googlefonts/ttf"

mkdir -p fonts
cd fonts
git clone --filter=blob:none --no-checkout https://github.com/notofonts/notofonts.github.io.git
cd notofonts.github.io
git sparse-checkout set --cone "$TTF_DIR"
git checkout main
cp "$TTF_DIR"/*.ttf ..
cd ..
rm -rf notofonts.github.io
