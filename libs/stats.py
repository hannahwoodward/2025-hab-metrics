import numpy as np
import scipy
import xarray
# import xskillscore as xs

import libs.utils


def get_ctable(data_hab_vals, clim_hab_vals, type='all'):
    contingency_numbers = [1, 2, 3]
    cmap = { 1: 0, 2: 1, 3: 2 }
    ctable = np.array([[0, 0, 0], [0, 0, 0], [0, 0, 0]])
    f_skill_score = calc_skill_scores_3x3

    if type == 'complex':
        ctable = np.array([[0, 0], [0, 0]])
        contingency_numbers = [1, 3]
        cmap = { 1: 0, 3: 1}
        f_skill_score = calc_skill_scores_2x2
        # Set all microbial values to limited
        data_hab_vals = data_hab_vals.where(
            data_hab_vals.isnull() | (data_hab_vals != 2),
            1
        )
        clim_hab_vals = clim_hab_vals.where(
            clim_hab_vals.isnull() | (clim_hab_vals != 2),
            1
        )
    elif type == 'microbial':
        ctable = np.array([[0, 0], [0, 0]])
        contingency_numbers = [1, 2]
        cmap = { 1: 0, 2: 1}
        f_skill_score = calc_skill_scores_2x2
        # Set all complex values to microbial
        data_hab_vals = data_hab_vals.where(
            data_hab_vals.isnull() | (data_hab_vals != 3),
            2
        )
        clim_hab_vals = clim_hab_vals.where(
            clim_hab_vals.isnull() | (clim_hab_vals != 3),
            2
        )

    for p_i in contingency_numbers:
        for o_i in contingency_numbers:
            freq_weighted = libs.utils.weighted(xarray.where(
                (data_hab_vals == o_i) & (clim_hab_vals == p_i),
                1,
                0
            )).sum().values

            ctable[cmap[p_i]][cmap[o_i]] = np.round(freq_weighted)

    return ctable, f_skill_score


def calc_skill_scores_3x3(ct):
    ct_total = ct.sum()

    ct_lim = [
        [ct[0][0], ct[0][1] + ct[0][2]],
        [ct[1][0] + ct[2][0], ct[1][1] + ct[1][2] + ct[2][1] + ct[2][2]]
    ]

    ct_mic = [
        [ct[1][1], ct[1][0] + ct[1][2]],
        [ct[0][1] + ct[2][1], ct[0][0] + ct[0][2] + ct[2][0] + ct[2][2]]
    ]

    ct_com = [
        [ct[2][2], ct[2][0] + ct[2][1]],
        [ct[0][2] + ct[1][2], ct[0][0] + ct[0][1] + ct[1][0] + ct[1][1]]
    ]

    prop_correct = (ct[0][0] + ct[1][1] + ct[2][2]) / ct_total

    # Calculate marginal probabilities
    p_y1_m = ct[0].sum() / ct_total
    p_y2_m = ct[1].sum() / ct_total
    p_y3_m = ct[2].sum() / ct_total
    p_o1_m = (ct[0][0] + ct[1][0] + ct[2][0]) / ct_total
    p_o2_m = (ct[0][1] + ct[1][1] + ct[2][1]) / ct_total
    p_o3_m = (ct[0][2] + ct[1][2] + ct[2][2]) / ct_total

    # The proportion correct for the random reference forecasts:
    prop_correct_rr = p_y1_m * p_o1_m + p_y2_m * p_o2_m + p_y3_m * p_o3_m

    # Calculate Heidke skill score
    # Proportion correct for perfect forecasts is 1
    heidke_ss = (
        (prop_correct - prop_correct_rr) / (1 - prop_correct_rr)
    )

    # Calculate Peirce skill score
    # Proportion correct for perfect forecasts is 1
    # Unbiased random prop
    prop_unbiased_random = p_o1_m**2 + p_o2_m**2 + p_o3_m**2

    peirce_ss = (
        (prop_correct - prop_correct_rr) / (1 - prop_unbiased_random)
    )

    # Gerrity skill score
    # A variant of the Gandin-Murphy skill score that adds a
    # weight for 'further away' categories to be 'worse'
    d_1 = (1 - p_o1_m) / p_o1_m
    d_2 = (1 - (p_o1_m + p_o2_m)) / (p_o1_m + p_o2_m)

    score_weights = 0.5 * np.array([
        [d_1 + d_2, d_2 - 1, -2],
        [d_2 - 1, (1 / d_1) + d_2, (1 / d_1) - 1],
        [-2, (1 / d_1) - 1, (1 / d_1) + (1 / d_2)]
    ])

    gm_ss = (ct * score_weights / ct.sum()).sum()

    return {
        'pc': prop_correct,
        'hss': heidke_ss,
        'pss': peirce_ss,
        'gss': gm_ss
    }


def calc_skill_scores_2x2(ct):
    ct_total = ct.sum()

    ct_lim = [
        [ct[0][0], ct[0][1]],
        [ct[1][0], ct[1][1]]
    ]

    ct_hab = [
        [ct[1][1], ct[1][0]],
        [ct[0][1], ct[0][0]]
    ]

    prop_correct = (ct[0][0] + ct[1][1]) / ct_total

    # Calculate marginal probabilities
    p_y1_m = ct[0].sum() / ct_total
    p_y2_m = ct[1].sum() / ct_total
    p_o1_m = (ct[0][0] + ct[1][0]) / ct_total
    p_o2_m = (ct[0][1] + ct[1][1]) / ct_total

    # The proportion correct for the random reference forecasts:
    prop_correct_rr = p_y1_m * p_o1_m + p_y2_m * p_o2_m

    # Calculate Heidke skill score
    # Proportion correct for perfect forecasts is 1
    heidke_ss = (
        (prop_correct - prop_correct_rr) / (1 - prop_correct_rr)
    )

    # Calculate Peirce skill score
    # Proportion correct for perfect forecasts is 1
    # Unbiased random prop
    prop_unbiased_random = p_o1_m**2 + p_o2_m**2

    peirce_ss = (
        (prop_correct - prop_correct_rr) / (1 - prop_unbiased_random)
    )

    return {
        'pc': prop_correct,
        'hss': heidke_ss,
        'pss': peirce_ss
    }
