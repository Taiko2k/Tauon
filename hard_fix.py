# This is still just a main idea, nothing much's going on.
"""Applies the patch for less warns on official releases."""
import logging
import subprocess


def main() -> None:
    try:
        logging.info("Attempting to apply MA/KF patch...")
        subprocess.run("patch -Np1 < extra/pyinstaller-hooks/bla.diff", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        logging.warning(f"Patch application failed: {e}. Proceeding with the build.")
        pass

if __name__ == "__main__":
	main()
