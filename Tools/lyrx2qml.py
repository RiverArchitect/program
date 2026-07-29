#!/usr/bin/python
""" Convert an ArcGIS Pro layer file (.lyrx) into a QGIS layer style (.qml).

River Architect's mapping moved from ArcGIS Pro to QGIS print layouts (see
.site_packages/riverpy/cMapper.py). Layer symbology moved with it: .lyrx -> .qml.

.lyrx is JSON (the Esri CIM format), so the class breaks, colours and labels of the
published lifespan symbology can be carried over exactly rather than re-invented.

Supported colorizers
--------------------
  CIMRasterClassifyColorizer  -> QGIS singlebandpseudocolor, DISCRETE interpolation
  CIMRasterUniqueValueColorizer -> QGIS paletted/unique values

Anything else is reported and skipped.

Usage
-----
    python lyrx2qml.py <input.lyrx> [output.qml]
    python lyrx2qml.py ../02_Maps/templates/symbology/LifespanRasterSymbology.lyrx

Pure standard library - no QGIS, GDAL or arcpy needed.
"""

import argparse
import colorsys
import json
import os
import sys
from xml.etree import ElementTree as ET
from xml.dom import minidom


def cim_color_to_rgba(color):
    """Convert a CIM colour of any flavour into an (r, g, b, a) 0-255 tuple."""
    if not color:
        return (0, 0, 0, 255)
    ctype = color.get("type", "")
    values = color.get("values", [])

    if ctype == "CIMRGBColor":
        r, g, b = values[0], values[1], values[2]
        alpha = values[3] if len(values) > 3 else 100
    elif ctype == "CIMHSVColor":
        # CIM stores H in degrees 0-360, S and V as percentages.
        h, s, v = values[0] / 360.0, values[1] / 100.0, values[2] / 100.0
        r, g, b = [c * 255.0 for c in colorsys.hsv_to_rgb(h, s, v)]
        alpha = values[3] if len(values) > 3 else 100
    elif ctype == "CIMCMYKColor":
        c, m, y, k = [v / 100.0 for v in values[:4]]
        r = 255.0 * (1 - c) * (1 - k)
        g = 255.0 * (1 - m) * (1 - k)
        b = 255.0 * (1 - y) * (1 - k)
        alpha = values[4] if len(values) > 4 else 100
    elif ctype == "CIMGrayColor":
        r = g = b = values[0] * 2.55
        alpha = values[1] if len(values) > 1 else 100
    else:
        print("    WARNING: unsupported colour type %s - falling back to black." % ctype)
        return (0, 0, 0, 255)

    return (int(round(r)), int(round(g)), int(round(b)), int(round(alpha * 2.55)))


def find_colorizer(document):
    for layer in document.get("layerDefinitions", []):
        if "colorizer" in layer:
            return layer.get("name", "layer"), layer["colorizer"]
    return None, None


def build_pseudocolor_qml(colorizer):
    """QGIS singlebandpseudocolor renderer from a CIMRasterClassifyColorizer."""
    breaks = colorizer.get("classBreaks", [])
    if not breaks:
        raise ValueError("no classBreaks in colorizer")

    nodata_rgba = cim_color_to_rgba(colorizer.get("noDataColor"))

    qgis = ET.Element("qgis", {"version": "3.34", "styleCategories": "AllStyleCategories"})
    pipe = ET.SubElement(qgis, "pipe")
    renderer = ET.SubElement(pipe, "rasterrenderer", {
        "type": "singlebandpseudocolor",
        "band": "1",
        "opacity": "1",
        "alphaBand": "-1",
        "classificationMin": str(_lower_bound(breaks)),
        "classificationMax": str(breaks[-1]["upperBound"]),
        "nodataColor": "#%02x%02x%02x" % nodata_rgba[:3],
    })

    shader = ET.SubElement(renderer, "rastershader")
    ramp = ET.SubElement(shader, "colorrampshader", {
        # DISCRETE reproduces "everything up to upperBound gets this colour", which is
        # exactly what an ArcGIS classify colorizer does.
        "colorRampType": "DISCRETE",
        "classificationMode": "1",
        "clip": "0",
        "labelPrecision": "2",
        "minimumValue": str(_lower_bound(breaks)),
        "maximumValue": str(breaks[-1]["upperBound"]),
    })

    for brk in breaks:
        r, g, b, a = cim_color_to_rgba(brk.get("color"))
        ET.SubElement(ramp, "item", {
            "value": str(brk["upperBound"]),
            "label": str(brk.get("label", brk["upperBound"])).strip(),
            "color": "#%02x%02x%02x" % (r, g, b),
            "alpha": str(a),
        })

    # NoData transparent, matching the .lyrx noDataColor alpha of 0.
    if nodata_rgba[3] == 0:
        ET.SubElement(pipe, "nodata")

    ET.SubElement(qgis, "blendMode").text = "0"
    return qgis


def build_paletted_qml(colorizer):
    """QGIS paletted renderer from a CIMRasterUniqueValueColorizer."""
    qgis = ET.Element("qgis", {"version": "3.34", "styleCategories": "AllStyleCategories"})
    pipe = ET.SubElement(qgis, "pipe")
    renderer = ET.SubElement(pipe, "rasterrenderer", {
        "type": "paletted", "band": "1", "opacity": "1", "alphaBand": "-1"})
    palette = ET.SubElement(renderer, "colorPalette")

    for group in colorizer.get("groups", []):
        for cls in group.get("classes", []):
            values = cls.get("values", [])
            if not values:
                continue
            r, g, b, a = cim_color_to_rgba(cls.get("color"))
            ET.SubElement(palette, "paletteEntry", {
                "value": str(values[0]),
                "label": str(cls.get("label", values[0])).strip(),
                "color": "#%02x%02x%02x" % (r, g, b),
                "alpha": str(a),
            })
    return qgis


def _lower_bound(breaks):
    """Sensible classification minimum: one step below the first upper bound."""
    first = breaks[0]["upperBound"]
    return first - 1 if len(breaks) < 2 else first - (breaks[1]["upperBound"] - first)


def convert(lyrx_path, qml_path=None):
    with open(lyrx_path, "r", encoding="utf-8") as handle:
        document = json.load(handle)

    name, colorizer = find_colorizer(document)
    if colorizer is None:
        print("ERROR: no colorizer found in %s" % lyrx_path)
        return None

    ctype = colorizer.get("type")
    print("  layer '%s', colorizer %s" % (name, ctype))

    if ctype == "CIMRasterClassifyColorizer":
        root = build_pseudocolor_qml(colorizer)
        n = len(colorizer.get("classBreaks", []))
        print("  converted %d class breaks" % n)
    elif ctype == "CIMRasterUniqueValueColorizer":
        root = build_paletted_qml(colorizer)
        print("  converted unique-value palette")
    else:
        print("ERROR: unsupported colorizer type %s" % ctype)
        return None

    if qml_path is None:
        qml_path = os.path.splitext(lyrx_path)[0] + ".qml"

    pretty = minidom.parseString(ET.tostring(root, "utf-8")).toprettyxml(indent="  ")
    with open(qml_path, "w", encoding="utf-8") as handle:
        handle.write(pretty)
    print("  wrote %s" % qml_path)
    return qml_path


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("lyrx", help="input .lyrx file")
    parser.add_argument("qml", nargs="?", help="output .qml file (default: alongside input)")
    args = parser.parse_args()

    if not os.path.isfile(args.lyrx):
        print("ERROR: no such file: %s" % args.lyrx)
        return 1
    print("Converting %s" % args.lyrx)
    return 0 if convert(args.lyrx, args.qml) else 1


if __name__ == "__main__":
    sys.exit(main())
