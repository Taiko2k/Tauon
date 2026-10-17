# Upgrading a source checkout to the native launcher

Tauon now starts through a native `tauon` executable. Running it as a Python script no longer works.

1. **Update:**

   ```bash
   git pull && git submodule update --init --recursive
   ```


1. **Rebuild your virtual environment.** The quickest way is `./run.sh 1`,
   which deletes `.venv` and `build`, reinstalls and launches. Or do it by
   hand:

   ```bash
   python -m pip install scikit-build-core
   python -m pip install --no-build-isolation -C build-dir=build/editable -e ".[all,dev]"
   ```

2. **Launch with `.venv/bin/tauon`.** `python -m tauon`,
   `python src/tauon/__main__.py` and the old `tauonmb` command are gone, so
   update any shortcuts or scripts that use them. `extra/tauonmb.sh` has been
   removed too. The remote-control commands (`--next`, `--playpause` and so
   on) now go to the `tauon` executable.


Your library and settings stay where they were. The window's size and position
reset once.
