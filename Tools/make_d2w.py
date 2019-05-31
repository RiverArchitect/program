#!/usr/bin/python
# Filename: make_d2w.py

import cWaterLevel as cWL


def make_d2w():
    path2ras_h_low = "D:\\temp\\h530"  # Must not contain zero-pixels (0 = NoData)
    path2ras_dem = "D:\\temp\\dem"
    out_dir = "D:\\temp\\"
    wle = cWL.WLE(out_dir)
    wle.calculate_d2w(path2ras_h_low, path2ras_dem)


if __name__ == "__main__":
    make_d2w()
