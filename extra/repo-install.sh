#!/bin/bash
#
# A script for the lazy folk and probably a butchering of git.
# Run this script once you have **ALL OF THE DEPENDENCIES** set up and
# updated; this also include dependencies **OUTSIDE OF PYTHON**, like
# 'opusfile-devel' on Fedora.
# Either way, the debug message pointing out what is missing when
# compiling PHAzOR (line #16) helps you find out what is needed.
# Those packages usually have similar enough names to be found quite
# easily by your package manager of choice.
#
# The script below installs the TauonMusicBox repo as a desktop app by
# cloning files into temporary ones and changing+deploying them;
# lines #40 to #45. I did it because I was too lazy to learn RPM
# packaging :B
#
# If you're running it for the very first time
# (and just to be on the safe side), then the repository itself should
# probably be cleansed, as in:
#   ----------------------------------
#   git reset --hard && git clean -dfx
#   ----------------------------------
#
# NEVER run this script as sudo!
# Thank you.

RepoDir=$(realpath $(dirname "$0")/..)
ShareDir=~/.local/share
cd $RepoDir

set -e

rm -fR lib
sh compile-phazor.sh

cp -rf locale ../
python3 compile-translations.py install --root=$ShareDir
( cd locale
  rm -fR */*/tauon.po )
cp -rf locale $ShareDir/
rm -fR locale
mv ../locale ./

cp -f extra/tauonmb.{,tmp.}desktop
cp -f extra/tauonmb.{,tmp.}sh

sed -i "s+/opt/tauon-music-box/tauonmb+sh $RepoDir/extra/tauonmb.tmp+g" extra/tauonmb.tmp.desktop
sed -i '1a cd $(realpath $(dirname "$0")/..)' extra/tauonmb.tmp.sh
sed -i "s+/opt/tauon-music-box+$RepoDir+g" extra/tauonmb.tmp.sh

mkdir -p $ShareDir/{applications,icons/hicolor/scalable/apps}
install -Dm755 extra/tauonmb.tmp.desktop $ShareDir/applications/tauonmb.desktop
install -Dm644 extra/tauonmb{,-symbolic}.svg $ShareDir/icons/hicolor/scalable/apps/

# This lines uses sudo to update your desktop apps list so you can
# open it from the menu as soon as it is ready.
sudo update-desktop-database

echo -e "\n== == == == == ==\n\
 Setup finished!\n\
== == == == == =="
