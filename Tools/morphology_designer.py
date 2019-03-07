#!/usr/bin/python
# Filename: morphology_designer.py

import cHydraulic as chy
import cPoolRiffle as cpr
import cInputOutput as cio


def design_manager():
    D50 = 0.0914  # (m) CHANGE bed grain size Bartons Bar: 0.0965 / Upper Gilt Edge Bar: 0.0914
    l = 750       # (m) CHANGE reach lenght Bartons Bar: 350 / Upper Gilt Edge  Bar: 750
    m = 2.58      # (-) CHANGE normal channel bank slope All: 2.58
    S0 = 0.004    # (-) CHANGE channel slope Bartons Bar: 0.005 / Upper Gilt Edge  Bar: 0.004
    w_base = 24.0  # (m) CHANGE base width Bartons Bar: 5.5 / Upper Gilt Edge  Bar: 24
    target_D_z = 0.915  # (m) CHANGE target pool depth (must be >0)

    hy = chy.Hydraulic(S0, D50)

    n_normal = 0.04
    n_mpm = hy.roughness_mpm(D50 * 2.75)
    n_strickler = hy.roughness_strickler(D50)
    roughness = [n_normal, n_mpm, n_strickler]
    rougness_names = ["n_normal", "n_mpm", "n_strickler"]
    roughness_dict = dict(zip(rougness_names, roughness))

    for n_type in roughness_dict.keys():
        print("Calculating with roughness type " + str(n_type) + ".")
        pr = cpr.PoolRiffle()
        pr.set_normal_channel(D50, m, roughness_dict[n_type], l, S0, w_base)
        result_matrix = pr.pool_riffle_designer(target_D_z)
        result_matrix.append(m)
        result_matrix.append(roughness_dict[n_type])
        result_matrix.append(w_base)

        writer = cio.Write("pr_" + n_type + ".xlsx")
        writer.write_pool_riffle(result_matrix)


if __name__ == "__main__":
    design_manager()
