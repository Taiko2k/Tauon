"""Let's make this standard, new typings are great, but nice and slow."""
import subprocess
from pathlib import Path

python_version = "3.11"
current_dir = Path.cwd()
current_script = Path(__file__).name

track_py = sorted(py for py in current_dir.rglob("*.py") \
                  if py.name != current_script)
RES = "\033[0m"

for python_file in track_py:
    command = [
        "pyright",
        "--pythonversion", python_version,
        "--verbose",
        "--level", "error",
        str(python_file)
    ]
    try:
        result = subprocess.run(command, text=True, capture_output=True, check=True)
        print(f"{python_file}: {'\033[92m'}Passed!{RES}")
    except subprocess.CalledProcessError as e:
        print(f"{python_file}: {'\033[91m'}Failed.{RES}")
        print(result.stdout)
        raise
