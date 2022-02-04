#!/bin/bash
#
# Removes the '.desktop' and '.svg's files from their deployed location.

rm -f ~/.local/share/{applications/tauonmb.desktop,icons/hicolor/scalable/apps/tauonmb{.svg,-symbolic.svg}}
sudo update-desktop-database
