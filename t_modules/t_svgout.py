from gi import require_version
require_version('Rsvg', '2.0')
from gi.repository import Rsvg
import cairo
import os


def render_icons(source_directory, output_directory, scale):

    targets = []
    # Verify svg files exist
    for file in os.listdir(source_directory):
        if file.endswith(".svg") and os.path.isfile(os.path.join(source_directory, file)):
            targets.append(file)

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Render svg files to png
    for file in targets:
        name = os.path.splitext(file)[0]
        in_path = os.path.join(source_directory, file)
        out_path = os.path.join(output_directory, name + ".png")

        handle = Rsvg.Handle()
        svg = handle.new_from_file(in_path)

        unscaled_width = svg.props.width
        unscaled_height = svg.props.height

        width = unscaled_width * scale
        height = unscaled_height * scale

        svg_surface = cairo.SVGSurface(None, width, height)
        svg_context = cairo.Context(svg_surface)
        svg_context.save()
        svg_context.scale(width/unscaled_width, height/unscaled_height)
        svg.render_cairo(svg_context)
        svg_context.restore()

        svg_surface.write_to_png(out_path)
