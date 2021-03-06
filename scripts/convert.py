import xml.etree.ElementTree as ET
import copy
import os
from cairosvg import svg2png, svg2pdf
from math import floor


def remove_by_class(parent_node, class_name):
    nodes_to_remove = []
    for child in parent_node:
        if child.attrib['class'] == class_name:
            nodes_to_remove.append(child)

    for child_node in nodes_to_remove:
        parent_node.remove(child_node)


def process_svg(root, show_baseline=False, show_bounding_box=False):
    for child in root:
        parametric_attributes = []
        for attrib in child.attrib:
            if attrib.startswith('{https://parametric-svg.github.io/v0.2}'):
                parametric_attributes.append(attrib)

        for attrib in parametric_attributes:   # indentation
            child.attrib.pop(attrib)

    if not show_baseline:
        remove_by_class(root, "baseline")

    if not show_bounding_box:
        remove_by_class(root, "bounding-box")


def remove_parametric_attributes(root):

    root.attrib.pop('{https://parametric-svg.github.io/v0.2}defaults')

    for child in root:
        parametric_attributes = []
        for attrib in child.attrib:
            if attrib.startswith('{https://parametric-svg.github.io/v0.2}'):
                parametric_attributes.append(attrib)

        for attrib in parametric_attributes:
            child.attrib.pop(attrib)


def format_specification_glyph(root):
    baseline_style = "opacity:1;fill:none;fill-opacity:1;stroke:#b3b3b3;stroke-width:0.49999994;" +\
                     "stroke-linecap:round;stroke-linejoin:miter;stroke-miterlimit:4;stroke-dasharray:1,0.5;" +\
                     "stroke-dashoffset:0;stroke-opacity:1"

    bbox_style = "opacity:0.5;fill:none;fill-opacity:1;stroke:#999999;stroke-width:0.5;stroke-miterlimit:4;" +\
                 "stroke-dasharray:1, 0.5;stroke-dashoffset:0;stroke-opacity:1"

    for child in root:
        if child.attrib.get('class') == "baseline":
            child.attrib['style'] = baseline_style
        elif child.attrib.get('class') == "bounding-box":
            child.attrib['style'] = bbox_style


def create_glyph_grid(glyphs):
    x_padding = 10
    y_padding = 10
    num_columns = 10
    glyph_size = 100

    print(f"Creating grid of {len(glyphs)} glyphs")
    svg = ET.Element('svg')
    svg.attrib['width'] = str(num_columns * glyph_size + (num_columns + 1) * x_padding)

    num_rows = floor(len(glyphs) / num_columns)
    svg.attrib['height'] = str(num_rows * glyph_size + (num_rows + 1) * y_padding)

    i = 0
    for glyph_name in glyphs:
        glyph = glyphs[glyph_name]

        group = ET.SubElement(svg, 'g')

        title = ET.SubElement(group, 'text')
        title.text = glyph_name
        title.attrib['font-size'] = "5"
        title.attrib['y'] = str(glyph_size / 2)

        column = i % num_columns
        row = floor(i / num_columns)
        group.attrib['transform'] = f"translate({column * (glyph_size + x_padding) + x_padding}, {row * (glyph_size + y_padding) + y_padding})"

        group.attrib['id'] = glyph_name

        for child in glyph:
            group.append(child)
        svg.append(group)
        i += 1

    return svg


def convert_svg(svg_string, directory, name):
    svg2png(bytestring=svg_string, write_to=os.path.join(directory, f"{name}.png"))
    svg2pdf(bytestring=svg_string, write_to=os.path.join(directory, f"{name}.pdf"))


base_dir = '../glyph_definitions'
output_dir = '../converted'


specification_glyphs = {}
bare_glyphs = {}

for file_name in os.listdir(base_dir):
    print(f"Now processing {file_name}")
    base_name = os.path.splitext(file_name)[0]
    extension = os.path.splitext(file_name)[1]

    if extension != ".svg":
        continue

    glyph_dir = os.path.join(output_dir, base_name)
    if not os.path.exists(glyph_dir):
        os.makedirs(glyph_dir)

    tree = ET.parse(os.path.join(base_dir, file_name))
    svg_tree = tree.getroot()

    # remove parametric attributes to get 'conventional' SVG
    remove_parametric_attributes(svg_tree)

    ET.register_namespace("", "http://www.w3.org/2000/svg")

    # Set style to match specification style
    format_specification_glyph(svg_tree)
    convert_svg(ET.tostring(svg_tree), glyph_dir, f"{base_name}-specification")
    tree.write(os.path.join(glyph_dir, f"{base_name}-specification.svg"))

    specification_glyphs[base_name] = copy.deepcopy(svg_tree)

    # convert to glyph-only format
    remove_by_class(svg_tree, "baseline")
    remove_by_class(svg_tree, "bounding-box")

    convert_svg(ET.tostring(svg_tree), glyph_dir, f"{base_name}")
    tree.write(os.path.join(glyph_dir, f"{base_name}.svg"))

    bare_glyphs[base_name] = copy.deepcopy(svg_tree)


grid = create_glyph_grid(specification_glyphs)
grid_svg_string = ET.tostring(grid, encoding="unicode")
with open(os.path.join(output_dir, "all-specification.svg"), 'w') as f:
    f.write(grid_svg_string)
convert_svg(grid_svg_string, output_dir, "all-specification")


grid = create_glyph_grid(bare_glyphs)
grid_svg_string = ET.tostring(grid, encoding="unicode")
with open(os.path.join(output_dir, "all.svg"), 'w') as f:
    f.write(grid_svg_string)
convert_svg(grid_svg_string, output_dir, "all")
