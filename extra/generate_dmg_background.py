"""Generate a background image for the macOS DMG installer.

Creates a clean background with an arrow pointing from the app icon
to the Applications folder, guiding the user to drag-and-drop install.

Window and icon layout must match the create-dmg arguments:
  --window-size 540 400
  --icon "TauonMusicBox.app" 150 170
  --app-drop-link 390 170
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

# Must match --window-size in the create-dmg command
WIDTH = 540
HEIGHT = 400

# Must match --icon / --app-drop-link positions in the create-dmg command
APP_ICON_X = 150
APPS_FOLDER_X = 390
ICON_Y = 170
ICON_RADIUS = 55  # half the --icon-size (100)

# Arrow styling
ARROW_COLOR = (100, 100, 100, 255)
SHAFT_WIDTH = 3
HEAD_LENGTH = 16
HEAD_HALF_HEIGHT = 8

# Background color – a neutral light grey matching typical macOS DMGs
BG_COLOR = (220, 220, 220, 255)


def main() -> None:
    output = sys.argv[1] if len(sys.argv) > 1 else "dist/dmg-background.png"
    Path(output).parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGBA", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Arrow endpoints – leave space between icon edges and arrow
    gap = 12
    x_start = APP_ICON_X + ICON_RADIUS + gap
    x_end = APPS_FOLDER_X - ICON_RADIUS - gap
    y = ICON_Y

    # Shaft
    draw.line(
        [(x_start, y), (x_end - HEAD_LENGTH, y)],
        fill=ARROW_COLOR,
        width=SHAFT_WIDTH,
    )

    # Arrowhead (solid triangle)
    draw.polygon(
        [
            (x_end, y),
            (x_end - HEAD_LENGTH, y - HEAD_HALF_HEIGHT),
            (x_end - HEAD_LENGTH, y + HEAD_HALF_HEIGHT),
        ],
        fill=ARROW_COLOR,
    )

    img.save(output)
    print(f"Saved DMG background: {output}")


if __name__ == "__main__":
    main()
