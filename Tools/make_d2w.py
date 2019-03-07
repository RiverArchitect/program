#!/usr/bin/python
# Filename: make_d2w.py

import cDepth2Groundwater as cd2w


def make_d2w():
    path2ras_h_low = "D:\\temp\\h530"  # Must not contain zero-pixels (0 = NoData)
    path2ras_dem = "D:\\temp\\dem"
    out_dir = "D:\\temp\\"
    d2w = cd2w.D2W(out_dir)
    d2w.calculate_d2w(path2ras_h_low, path2ras_dem)


if __name__ == "__main__":
    make_d2w()
