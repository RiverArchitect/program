# !/usr/bin/python
""" Map production for River Architect, built on QGIS print layouts.

Replaces the former ArcGIS Pro implementation (arcpy.mp.ArcGISProject / .aprx projects,
.lyrx layer files, PDFDocumentCreate page stitching). Nothing here needs an Esri licence.

What changed conceptually
-------------------------
* Project file:  .aprx  ->  .qgz          (QgsProject, readable and editable in QGIS)
* Layer style:   .lyrx  ->  .qml          (QgsRasterLayer.loadNamedStyle)
* Page series:   PDFDocumentCreate + appendPages  ->  QGIS Atlas
  The old code exported one temporary PDF per map centre point and stitched them together.
  QGIS drives a multi-page series natively: a coverage layer holds one rectangle per page and
  QgsLayoutExporter.exportToPdf(atlas, ...) writes a single multi-page PDF in one call.
* Layout:        a layout stored inside the proprietary template  ->  composed in code
  The layout (map frame, legend, scale bar, north arrow, title, footer) is built
  programmatically, so no binary template is required. An existing .qgz template is used
  instead when one is present in 02_Maps/templates/.

The public API (Mapper(condition, map_type, *args), prepare_layout(), make_pdf_maps(),
.error) is unchanged, so LifespanDesign/feature_analysis.py, MaxLifespan/action_planner.py
and VolumeAssessment/volume_gui.py keep working without modification.

Running headless requires QT_QPA_PLATFORM=offscreen, which this module sets itself.
"""

import os
import sys
import logging

try:
    import config
    import fGlobal as fGl
except:
    print("ExceptionERROR: Cannot find package files (/.site_packages/riverpy/fGlobal.py).")

# QGIS must run offscreen when there is no display attached; set before importing qgis.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from qgis.core import (QgsApplication, QgsProject, QgsRasterLayer, QgsVectorLayer,
                           QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLegend,
                           QgsLayoutItemScaleBar, QgsLayoutItemLabel, QgsLayoutItemPicture,
                           QgsLayoutPoint, QgsLayoutSize, QgsUnitTypes, QgsLayoutExporter,
                           QgsRectangle, QgsFeature, QgsGeometry, QgsLayerTreeGroup,
                           QgsCoordinateReferenceSystem)
    from qgis.PyQt.QtGui import QFont
    QGIS_AVAILABLE = True
except:
    QGIS_AVAILABLE = False
    print("ExceptionERROR: QGIS (qgis.core) is not available - mapping is disabled.\n"
          "                Install QGIS and run River Architect with a Python that has the\n"
          "                QGIS bindings on its path (see docs/qgis_mapping.md).")

# Page geometry defaults, in millimetres. ANSI E landscape reproduces the former arcpy layout.
ANSI_E_LANDSCAPE = (1117.6, 863.6)
DEFAULT_DPI = 96
SINGLE_MAP_DPI = 192


def _p(*parts):
    """Join path fragments and normalise the mixed \\ and / separators used across config.py."""
    joined = os.path.join(*[str(x) for x in parts if str(x)])
    return os.path.normpath(joined.replace("\\", os.sep).replace("/", os.sep))


class QgisSession(object):
    """Process-wide QgsApplication. QGIS may only be initialised once per process."""
    _app = None

    @classmethod
    def start(cls):
        if not QGIS_AVAILABLE:
            return None
        if cls._app is None:
            prefix = os.environ.get("QGIS_PREFIX_PATH", "/usr")
            QgsApplication.setPrefixPath(prefix, True)
            cls._app = QgsApplication([], False)
            cls._app.initQgis()
        return cls._app

    @classmethod
    def stop(cls):
        if cls._app is not None:
            cls._app.exitQgis()
            cls._app = None


class Mapper:
    def __init__(self, condition, map_type, *args):
        # condition = [str] state of planning situation, e.g., "2008"
        # map_type = [str] options: "lf", "ds", "mlf", "mt"
        # args[0] alternative raster input directory - if empty: uses standard output
        # args[1] alternative output directory - if empty: 02_Maps/CONDITION/
        self.logger = logging.getLogger("logfile")

        self.condition = condition
        self.dir_map_shp = ""
        self.error = False
        self.map_type = map_type
        self.map_string = ""
        self.map_list = []
        self.ras4map_list = []
        self.raster_extent = None          # QgsRectangle
        self.resolution = DEFAULT_DPI
        self.xy_center_points = []
        self.dx = None
        self.dy = None
        self.page_size = ANSI_E_LANDSCAPE

        self.project = None
        self.layout = None
        self.map_item = None
        self.legend = None

        if not QGIS_AVAILABLE:
            self.error = True
            self.logger.info("ERROR: QGIS is not available - cannot produce maps.")

        try:
            if not (args[0].__len__() < 2):
                self.dir_map_ras = args[0]
            else:
                self.dir_map_ras = str(self.get_input_ras_dir(map_type))
            fGl.chk_dir(self.dir_map_ras)
        except:
            try:
                self.dir_map_ras = str(self.get_input_ras_dir(map_type))
            except:
                self.logger.info("WARNING: The provided path to rasters for mapping is invalid. Using templates instead.")
                self.dir_map_ras = _p(config.dir2map_templates, "rasters")

        try:
            self.output_dir = args[1]
        except:
            self.output_dir = _p(config.dir2map, self.condition) + os.sep
        fGl.chk_dir(self.output_dir)
        fGl.chk_dir(_p(self.output_dir, "layers") + os.sep)

        if QGIS_AVAILABLE:
            QgisSession.start()
            self.project = self.open_project()

    # ------------------------------------------------------------------ project

    def project_path(self):
        return _p(self.output_dir, "maps_%s_design.qgz" % self.condition)

    def open_project(self):
        """Create (or reopen) the QGIS project that carries this condition's maps.

        Replaces copy_template_project(), which duplicated river_template.aprx. If a QGIS
        template exists at 02_Maps/templates/river_template.qgz it is used as the starting
        point; otherwise an empty project is created and the layout is composed in code.
        """
        project = QgsProject.instance()
        project.clear()
        target = self.project_path()

        if os.path.isfile(target):
            if project.read(target):
                self.logger.info(" >> Using existing project: " + target)
                return project
            self.logger.info("WARNING: Could not read %s - starting a new project." % target)

        template = _p(config.dir2map_templates, "river_template.qgz")
        if os.path.isfile(template):
            if project.read(template):
                self.logger.info(" >> Started from QGIS template: " + template)
            else:
                self.logger.info("WARNING: Could not read %s - starting an empty project." % template)
        else:
            self.logger.info(" >> No river_template.qgz found - composing layout in code.")

        project.setFileName(target)
        return project

    def save_project(self):
        try:
            self.project.write(self.project_path())
        except Exception as e:
            self.logger.info("WARNING: Could not save QGIS project (%s)." % e)

    # ------------------------------------------------------------------ styles

    def choose_ref_layer(self, raster_type):
        # returns the base name of the .qml style for a raster type (formerly a .lyrx layer)
        try:
            if 'lf' in str(raster_type):
                return "lf_sym"
            if 'ds' in str(raster_type):
                return "ds_sym"
        except ValueError:
            return ""
        return ""

    def choose_ref_layout(self, map_lyr_name=str()):
        if "lf" in map_lyr_name:
            if not ("mlf" in map_lyr_name):
                return "layout_lf"
            else:
                if "bio" in map_lyr_name.lower():
                    return "layout_mlf_bioeng"
                if "maint" in map_lyr_name.lower():
                    return "layout_mlf_maintenance"
                if "plant" in map_lyr_name.lower():
                    return "layout_mlf_plants"
                if "terra" in map_lyr_name.lower():
                    return "layout_mlf_terraforming"
        if "ds" in map_lyr_name:
            if "bio" in map_lyr_name.lower():
                return "layout_ds_bio"
            if ("dcf" in map_lyr_name.lower()) or ("dcr" in map_lyr_name.lower()) or ("dst" in map_lyr_name.lower()) or ("grav" in map_lyr_name.lower()) or ("rocks" in map_lyr_name.lower()):
                return "layout_ds_Dcr"
            if "fines" in map_lyr_name.lower():
                if "15" in map_lyr_name.lower():
                    return "layout_ds_FS_D15"
                if "85" in map_lyr_name.lower():
                    return "layout_ds_FS_D85"
            if "sidech" in map_lyr_name.lower():
                return "layout_ds_SeS0"
            if "sideca" in map_lyr_name.lower():
                return "layout_ds_sideca"
            if "widen" in map_lyr_name.lower():
                return "layout_ds_widen"
            if ("wood" in map_lyr_name.lower()) or ("Dw" in map_lyr_name.lower()):
                return "layout_ds_Dw"
        if "volume_" in map_lyr_name:
            return map_lyr_name
        if "exc" in map_lyr_name:
            return "volume_cust_neg"
        if "fil" in map_lyr_name:
            return "volume_cust_pos"
        return "layout_lf"

    def choose_map_layer(self, map_name=str()):
        if "lf" in map_name:
            if not ("mlf" in map_name):
                return "layer_lf"
            else:
                if "bio" in map_name.lower():
                    return "layer_mlf_bioeng"
                if "maint" in map_name.lower():
                    return "layer_mlf_connectivity"
                if "plant" in map_name.lower():
                    return "layer_mlf_plants"
                if "terra" in map_name.lower():
                    return "layer_mlf_terraforming"
        if "ds_" in map_name:
            if "bio" in map_name.lower():
                return "layer_ds_bio"
            if ("dcf" in map_name.lower()) or ("dcr" in map_name.lower()) or ("dst" in map_name.lower()) or ("grav" in map_name.lower()) or ("grain" in map_name.lower()):
                return "layer_ds_Dcr"
            if "fines" in map_name.lower():
                if "15" in map_name.lower():
                    return "layer_ds_FS_D15"
                if "85" in map_name.lower():
                    return "layer_ds_FS_D85"
            if "sidech" in map_name.lower():
                return "layer_ds_SeS0"
            if "sideca" in map_name.lower():
                return "layer_ds_sideca"
            if "widen" in map_name.lower():
                return "layer_ds_widen"
            if "wood" in map_name.lower():
                return "layer_ds_Dw"
        if "volume_" in map_name:
            return map_name
        if "exc" in map_name:
            return "volume_cust_neg"
        if "fil" in map_name:
            return "volume_cust_pos"
        return "layer_lf"

    def style_file(self, style_name):
        """Full path of a .qml style, or an empty string when it does not exist."""
        for candidate in (style_name, style_name + ".qml"):
            path = _p(config.dir2map_templates, "symbology", candidate)
            if os.path.isfile(path):
                return path
        return ""

    def apply_style(self, layer, style_name):
        qml = self.style_file(style_name)
        if not qml:
            self.logger.info("    * no .qml style '%s' found - using QGIS defaults." % style_name)
            return False
        try:
            message, ok = layer.loadNamedStyle(qml)
            if ok:
                layer.triggerRepaint()
                self.logger.info("    * applied style: " + os.path.basename(qml))
                return True
            self.logger.info("WARNING: Could not apply %s (%s)." % (qml, message))
        except Exception as e:
            self.logger.info("WARNING: Could not apply %s (%s)." % (qml, e))
        return False

    # ------------------------------------------------------------------ layers

    def get_input_ras_dir(self, map_type):
        if (map_type == "lf") or (map_type == "ds"):
            return _p(config.dir2lf, "Output", "Rasters", self.condition) + os.sep
        if map_type == "mlf":
            self.dir_map_shp = _p(config.dir2ml, "Output", "Shapefiles", self.condition) + os.sep
            return _p(config.dir2ml, "Output", "Rasters", self.condition) + os.sep
        if map_type == "mt":
            return _p(config.dir2mt, "Output", "Rasters", self.condition) + os.sep

    def get_raster_extent(self, path2raster):
        # path2raster = STR of full raster directory (e.g., D:/temp/raster.tif)
        layer = QgsRasterLayer(_p(path2raster), os.path.basename(str(path2raster)))
        if not layer.isValid():
            self.logger.info("ERROR: Invalid raster: " + str(path2raster))
            return None
        return layer.extent()

    def add_background_layers(self):
        """Add any background layers shipped with the template directory."""
        added = []
        bg_dir = _p(config.dir2map_templates, "rasters")
        if not os.path.isdir(bg_dir):
            return added
        for name in sorted(os.listdir(bg_dir)):
            if not name.lower().endswith((".tif", ".tiff")):
                continue
            if "background" not in name.lower():
                continue
            layer = QgsRasterLayer(_p(bg_dir, name), os.path.splitext(name)[0])
            if layer.isValid():
                self.project.addMapLayer(layer)
                added.append(layer)
        return added

    def add_map_raster(self, raster_path, layer_name, style_name):
        layer = QgsRasterLayer(_p(raster_path), layer_name)
        if not layer.isValid():
            self.logger.info("ERROR: Could not load raster " + str(raster_path))
            self.error = True
            return None
        self.apply_style(layer, style_name)
        self.project.addMapLayer(layer)
        if not self.project.crs().isValid() and layer.crs().isValid():
            self.project.setCrs(layer.crs())
        self.raster_extent = layer.extent()
        return layer

    def add_shapefiles(self):
        """Add MaxLifespan shapefiles (map_type 'mlf') alongside the rasters."""
        added = []
        if not self.dir_map_shp or not os.path.isdir(self.dir_map_shp):
            return added
        for name in sorted(os.listdir(self.dir_map_shp)):
            if not name.lower().endswith(".shp"):
                continue
            layer = QgsVectorLayer(_p(self.dir_map_shp, name), os.path.splitext(name)[0], "ogr")
            if layer.isValid():
                self.apply_style(layer, os.path.splitext(name)[0])
                self.project.addMapLayer(layer)
                added.append(layer)
            else:
                self.logger.info("WARNING: Invalid shapefile: " + name)
        return added

    # ------------------------------------------------------------------ layout

    def build_layout(self, layout_name, title_text):
        """Compose a print layout: map frame, legend, scale bar, north arrow, title, footer.

        Replaces the layouts that used to live inside river_template.aprx.
        """
        manager = self.project.layoutManager()
        existing = manager.layoutByName(layout_name)
        if existing is not None:
            manager.removeLayout(existing)

        layout = QgsPrintLayout(self.project)
        layout.initializeDefaults()
        layout.setName(layout_name)

        width, height = self.page_size
        page = layout.pageCollection().page(0)
        page.setPageSize(QgsLayoutSize(width, height, QgsUnitTypes.LayoutMillimeters))

        margin = 0.02 * width
        legend_width = 0.16 * width
        header = 0.05 * height
        footer = 0.04 * height

        # --- map frame ---
        map_item = QgsLayoutItemMap(layout)
        map_item.setId("river_map")
        layout.addLayoutItem(map_item)
        map_item.attemptMove(QgsLayoutPoint(margin, header, QgsUnitTypes.LayoutMillimeters))
        map_item.attemptResize(QgsLayoutSize(width - 3 * margin - legend_width,
                                             height - header - footer,
                                             QgsUnitTypes.LayoutMillimeters))
        map_item.setFrameEnabled(True)
        if self.raster_extent is not None:
            map_item.zoomToExtent(self.raster_extent)

        # --- title ---
        title = QgsLayoutItemLabel(layout)
        title.setText(title_text)
        font = QFont()
        font.setPointSize(22)
        font.setBold(True)
        try:
            title.setFont(font)
        except:
            pass
        title.adjustSizeToText()
        layout.addLayoutItem(title)
        title.attemptMove(QgsLayoutPoint(margin, 0.3 * header, QgsUnitTypes.LayoutMillimeters))

        # --- legend ---
        legend = QgsLayoutItemLegend(layout)
        legend.setTitle("Legend")
        legend.setLinkedMap(map_item)
        legend.setLegendFilterByMapEnabled(True)
        layout.addLayoutItem(legend)
        legend.attemptMove(QgsLayoutPoint(width - margin - legend_width, header,
                                          QgsUnitTypes.LayoutMillimeters))
        legend.attemptResize(QgsLayoutSize(legend_width, 0.5 * height,
                                           QgsUnitTypes.LayoutMillimeters))
        legend.setFrameEnabled(True)
        self.legend = legend

        # --- scale bar ---
        scalebar = QgsLayoutItemScaleBar(layout)
        scalebar.setStyle("Single Box")
        scalebar.setLinkedMap(map_item)
        scalebar.applyDefaultSize()
        layout.addLayoutItem(scalebar)
        scalebar.attemptMove(QgsLayoutPoint(margin, height - footer + 0.005 * height,
                                            QgsUnitTypes.LayoutMillimeters))

        # --- north arrow (ships with QGIS) ---
        arrow_svg = _p(QgsApplication.pkgDataPath(), "svg", "arrows", "NorthArrow_02.svg")
        if os.path.isfile(arrow_svg):
            arrow = QgsLayoutItemPicture(layout)
            arrow.setPicturePath(arrow_svg)
            layout.addLayoutItem(arrow)
            arrow.attemptResize(QgsLayoutSize(0.03 * width, 0.03 * width,
                                              QgsUnitTypes.LayoutMillimeters))
            arrow.attemptMove(QgsLayoutPoint(width - margin - legend_width - 0.05 * width, header,
                                             QgsUnitTypes.LayoutMillimeters))

        # --- footer ---
        footer_label = QgsLayoutItemLabel(layout)
        footer_label.setText("River Architect  |  condition: %s  |  page [%% @atlas_featurenumber %%] "
                             "of [%% @atlas_totalfeatures %%]" % self.condition)
        footer_label.adjustSizeToText()
        layout.addLayoutItem(footer_label)
        footer_label.attemptMove(QgsLayoutPoint(margin, height - 0.6 * footer,
                                                QgsUnitTypes.LayoutMillimeters))

        manager.addLayout(layout)
        self.layout = layout
        self.map_item = map_item
        return layout

    # ------------------------------------------------------------------ atlas

    def make_xy_centerpoints(self, new_extents):
        # shape(new_extents) = [XMin, YMin, XMax, YMax]
        self.xy_center_points = []
        self.xy_center_points.append(
            [float((new_extents[0] + new_extents[2]) / 2.), float((new_extents[1] + new_extents[3]) / 2.)])
        self.dx = float(new_extents[2] - new_extents[0])
        self.dy = float(new_extents[3] - new_extents[1])
        self.logger.info("      - New X center: " + str(self.xy_center_points[0][0]))
        self.logger.info("      - New Y center: " + str(self.xy_center_points[0][1]))
        self.logger.info("      - New map width: " + str(self.dx))
        self.logger.info("      - New map height: " + str(self.dy))
        self.resolution = SINGLE_MAP_DPI  # improve resolution of single maps

    def coverage_layer(self):
        """One rectangle per map page, driving the QGIS atlas.

        This is the structural replacement for the old loop that zoomed the map frame to each
        centre point, exported a temporary PDF and appended it to a growing document.
        """
        crs = self.project.crs()
        uri = "Polygon?crs=%s&field=page:integer&field=label:string" % (
            crs.authid() if crs.isValid() else "EPSG:4326")
        layer = QgsVectorLayer(uri, "map_pages", "memory")
        if not layer.isValid():
            self.logger.info("ERROR: Could not create the atlas coverage layer.")
            return None

        centers = self.xy_center_points
        if not centers and self.raster_extent is not None:
            centers = [[self.raster_extent.center().x(), self.raster_extent.center().y()]]
            self.dx = self.raster_extent.width()
            self.dy = self.raster_extent.height()

        if self.dx is None or self.dy is None or self.dx <= 0 or self.dy <= 0:
            if self.raster_extent is None:
                self.logger.info("ERROR: No extent available for the map series.")
                return None
            self.dx = self.raster_extent.width()
            self.dy = self.raster_extent.height()

        features = []
        for i, xy in enumerate(centers):
            try:
                x, y = float(xy[0]), float(xy[1])
            except:
                self.logger.info("ERROR: Invalid x-y coordinates in extent source "
                                 "[mapping.inp / reaches] - skipping page %d." % (i + 1))
                continue
            rect = QgsRectangle(x - 0.5 * self.dx, y - 0.5 * self.dy,
                                x + 0.5 * self.dx, y + 0.5 * self.dy)
            feature = QgsFeature(layer.fields())
            feature.setGeometry(QgsGeometry.fromRect(rect))
            feature.setAttribute("page", i + 1)
            feature.setAttribute("label", "fig_%02d" % (i + 1))
            features.append(feature)

        if not features:
            self.logger.info("ERROR: No valid map pages could be defined.")
            return None

        layer.dataProvider().addFeatures(features)
        layer.updateExtents()
        self.project.addMapLayer(layer, False)   # keep it out of the legend
        self.logger.info("    * map series: %d page(s)" % len(features))
        return layer

    # ------------------------------------------------------------------ export

    def make_pdf_maps(self, map_name, *args, **kwargs):
        # map_name = STR of pdf name
        # args[0] =  STR of alternative output directory for PDFs
        # optional kwarg "extent": overwrite mapping extent ("raster", "MAXOF" or [xmin, ymin, xmax, ymax])
        # optional kwarg "map_layout": alternative QgsPrintLayout object
        if not QGIS_AVAILABLE:
            self.error = True
            return

        try:
            if args[0].__len__() > 3:
                self.output_dir = args[0]
                fGl.chk_dir(self.output_dir)
                self.logger.info(" >> Alternative output directory provided: " + str(self.output_dir))
        except:
            pass

        try:
            for k in kwargs.items():
                if "extent" in str(k[0]).lower():
                    if k[1] == "raster":
                        self.logger.info(" >> Using Raster coordinates for mapping.")
                        if self.raster_extent is not None:
                            self.make_xy_centerpoints([self.raster_extent.xMinimum(),
                                                       self.raster_extent.yMinimum(),
                                                       self.raster_extent.xMaximum(),
                                                       self.raster_extent.yMaximum()])
                    else:
                        if not (k[1] == "MAXOF"):
                            self.make_xy_centerpoints(k[1])
                            self.logger.info(" >> Special reach extents provided.")
                            self.logger.info("    --> Overwriting mapping.inp center point definitions.")
                if "map_layout" in k[0]:
                    self.logger.info(" >> External map layout provided - using: " + str(k[1]))
                    self.layout = k[1]
        except:
            pass

        if self.layout is None:
            self.logger.info("ERROR: No map layout prepared - call prepare_layout() first.")
            self.error = True
            return

        self.logger.info(" >> Starting PDF creation for: " + str(self.layout.name()))
        page = self.layout.pageCollection().page(0)
        self.logger.info("    * Map format: %0.1f mm x %0.1f mm"
                         % (page.pageSize().width(), page.pageSize().height()))

        map_name = os.path.basename(str(map_name).replace("\\", "/"))
        pdf_name = _p(self.output_dir, map_name.split(".pdf")[0] + ".pdf")
        try:
            if os.path.isfile(pdf_name):
                os.remove(pdf_name)
        except OSError:
            pass

        coverage = self.coverage_layer()
        if coverage is None:
            self.error = True
            return

        try:
            atlas = self.layout.atlas()
            atlas.setEnabled(True)
            atlas.setCoverageLayer(coverage)
            atlas.setFilenameExpression("\"label\"")
            self.map_item.setAtlasDriven(True)
            self.map_item.setAtlasScalingMode(QgsLayoutItemMap.Auto)
            atlas.updateFeatures()

            settings = QgsLayoutExporter.PdfExportSettings()
            settings.dpi = self.resolution
            settings.rasterizeWholeImage = False
            settings.forceVectorOutput = False

            self.logger.info("    * Creating PDF %s (%d page(s), %d dpi) ..."
                             % (pdf_name, atlas.count(), self.resolution))
            result, message = QgsLayoutExporter.exportToPdf(atlas, pdf_name, settings)

            if result == QgsLayoutExporter.Success:
                self.logger.info("    * Finished map: " + pdf_name)
            else:
                self.error = True
                self.logger.info("ERROR: PDF export failed (%s)." % (message or result))
        except Exception as e:
            self.logger.info("ERROR: Mapping failed (%s)." % e)
            self.error = True
        finally:
            try:
                self.project.removeMapLayer(coverage.id())
            except:
                pass

        self.save_project()

    # ------------------------------------------------------------------ driver

    def prepare_layout(self, *args, **kwargs):
        # prepares map layouts in the QGIS project and starts mapping if not args[0]
        # kwargs: - map_items=LIST of items for mapping (default: all rasters in dir_map_ras folder)
        if not QGIS_AVAILABLE:
            self.error = True
            return

        try:
            direct_mapping = args[0]
        except:
            direct_mapping = True

        self.ras4map_list = fGl.list_file_type_in_dir(self.dir_map_ras, ".tif")
        if self.ras4map_list.__len__() < 1:
            self.ras4map_list = fGl.list_file_type_in_dir(self.dir_map_ras, ".aux.xml")
        try:
            for k in kwargs.items():
                if "map_items" in str(k[0]).lower():
                    self.map_list = k[1]
        except:
            pass
        if self.map_list.__len__() < 1:
            self.map_list = self.ras4map_list

        self.logger.info("\n\nMAPPING")
        self.logger.info("----- ----- ----- ----- ----- ----- ----- ----- -----")

        for map_item in self.map_list:
            map_name = os.path.basename(str(map_item).replace("\\", "/"))
            map_name = str(map_name).lower().split(".tif")[0].split("_mlf")[0]
            self.logger.info(" >> Preparing map: " + _p(self.output_dir, map_name + ".pdf"))

            self.map_string = self.choose_map_layer(str(map_name).lower().split(".tif")[0])
            if self.map_string.__len__() < 1:
                self.logger.info("ERROR: No reference map found for %s (skipping)." % str(map_item))
                continue
            self.logger.info("    * source map layer: " + self.map_string)

            layout_name = self.choose_ref_layout(self.map_string)
            if layout_name.__len__() < 1:
                self.logger.info("ERROR: No reference layout found for %s (skipping)." % str(self.map_string))
                continue
            self.logger.info("    * source map layout: " + layout_name)

            try:
                # start each map from a clean layer stack so that the legend only shows
                # what belongs on this sheet (the old code toggled lyr.visible instead)
                self.project.removeAllMapLayers()
                self.raster_extent = None

                self.add_background_layers()

                raster_path = map_item if os.path.isabs(str(map_item)) \
                    else _p(self.dir_map_ras, str(map_item))
                if not str(raster_path).lower().endswith((".tif", ".tiff")):
                    raster_path = raster_path + ".tif"

                if self.map_type == "mlf":
                    self.add_shapefiles()
                    style = "LifespanRasterSymbology"
                else:
                    style = self.choose_ref_layer(map_name)

                self.logger.info("    * creating new layer ...")
                layer = self.add_map_raster(raster_path, map_name, style)
                if layer is None:
                    continue

                # keep a QGIS layer definition next to the PDF, replacing the old .lyrx export
                try:
                    layer.saveNamedStyle(_p(self.output_dir, "layers", map_name + ".qml"))
                except Exception as e:
                    self.logger.info("WARNING: Could not save layer style (%s)." % e)

                self.build_layout(layout_name, "%s - %s" % (self.condition, map_name))
                self.save_project()

                if direct_mapping:
                    self.logger.info("    * Calling PDF map creator ...")
                    self.make_pdf_maps(map_name, extent="raster")

            except Exception as e:
                self.logger.info("ERROR: Map layout preparation failed (%s)." % e)
                self.error = True

    def zoom2map(self, xy):
        """Kept for API compatibility. Page extents are now driven by the atlas coverage layer."""
        try:
            x, y = float(xy[0]), float(xy[1])
        except:
            self.logger.info("ERROR: Mapping could not assign xy-values. Undefined zoom.")
            return
        if self.map_item is None or self.dx is None or self.dy is None:
            return
        self.map_item.zoomToExtent(QgsRectangle(x - 0.5 * self.dx, y - 0.5 * self.dy,
                                                x + 0.5 * self.dx, y + 0.5 * self.dy))

    def __call__(self):
        pass
