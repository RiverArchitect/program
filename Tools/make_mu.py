#!/usr/bin/python
# Filename: make_mu.py

import cMorphUnits as cmu


def make_mu():
    # define h (flow depth) rasters
    path2ras_h_base = "D:\\LYR_SSCstudies\\RestorationPlans\\TBR_summary\\2Dremodel\\v00\\rasters_h\\h000_9k.tif"
    path2ras_h_bf = "D:\\LYR_SSCstudies\\RestorationPlans\\TBR_summary\\2Dremodel\\v00\\rasters_h\\h005_0k.tif"
    path2ras_h_flood = "D:\\LYR_SSCstudies\\RestorationPlans\\TBR_summary\\2Dremodel\\v00\\rasters_h\\h021_1k.tif"

    # define u (flow velocity) raster (base flow only)
    path2ras_u_base = "D:\\LYR_SSCstudies\\RestorationPlans\\TBR_summary\\2Dremodel\\v00\\rasters_u\\u000_9k.tif"

    out_dir = "D:\\Python\\StreamRestoration\\LifespanDesign\\Input\\2008_TBR_v00\\"

    mu = cmu.MU(out_dir)
    mu.calculate_mu_baseflow(path2ras_h_base, path2ras_u_base)
    mu.calculate_mu_bankfull(path2ras_h_bf)
    mu.calculate_mu_floodway(path2ras_h_flood)
    mu.save_mu(out_dir)


if __name__ == "__main__":
    make_mu()