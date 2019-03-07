#!/usr/bin/python
# Filename: make_det.py

import cDetrendedDEM as cdet


def make_det():
    path2ras_h_low = "D:\\LYR_SSCstudies\\RestorationPlans\\TBR_summary\\2Dremodel\\v00\\rasters_h\\h000_1k.tif"
    path2ras_dem = "D:\\LYR_SSCstudies\\RestorationPlans\\TBR_summary\\DEM\\v00\\export2numeric_model\\TBR08_clip00.tif"
    out_dir = "D:\\Python\\StreamRestoration\\LifespanDesign\\Input\\2008_TBR_v00\\"
    det = cdet.DET(out_dir)
    det.calculate_det(path2ras_h_low, path2ras_dem)


if __name__ == "__main__":
    make_det()
