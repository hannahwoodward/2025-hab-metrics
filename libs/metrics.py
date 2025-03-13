import numpy as np
import xarray

import libs.utils


def calc_hab_fractions(data):
    total_area = libs.utils.weighted(
        xarray.where(data > 0, 1, 0),
        dim='lat'
    ).sum()

    microbial = (libs.utils.weighted(
        xarray.where(data > 1, 1, 0),
        dim='lat'
    ).sum() / total_area).values

    complex = (libs.utils.weighted(
        xarray.where(data == 3, 1, 0),
        dim='lat'
    ).sum() / total_area).values

    return {
        'microbial': microbial,
        'complex': complex
    }


def get_metric_kwargs():
    return {
        'colorbar_kwargs': {
            'label': '',
            'spacing': 'uniform',
            'values': [1, 2, 3]
        },
        'colorbar_ticks': [1, 2, 3],
        'colorbar_ticklabels': [
            'Limited',
            'Microbial only',
            'Complex + Microbial'
        ],
        'plot_kwargs': {
            # 'cmap': 'YlGn',
            # 'levels': np.arange(0, 6, 1),
            'colors': ['#D9F0A3', '#77C679', '#3C8444', '#fff'],
            'levels': [1, 2, 3, 4],
        }
    }


def h_a25(data):
    '''
    Adams+ 2025
    https://doi.org/10.3847/1538-4357/ada3c8
    Habitability based on 'liquid water' temperatures 0-100C
    and precipitation 300mm per Earth year
    '''
    return xarray.where(
        (
            (data['tas'] >= 273.15) &
            (data['tas'] <= 373.15) &
            (data['pr'] >= (300.0 / (365.0 * 24 * 60 * 60)))
        ),
        2,
        1
    )


def h_dg19h(data):
    '''
    Del Genio+ 2019
    doi.org/10.3847/1538-4357/ab57fd
    Habitability based on Aridity Index where 'Humid'
    '''
    data_ai = data['ai']

    return xarray.where(
        data_ai > 0.39,
        2,
        1
    )


def h_dg19na(data):
    '''
    Del Genio+ 2019
    doi.org/10.3847/1538-4357/ab57fd
    Habitability based on Aridity Index where 'NonArid'
    '''
    data_ai = data['ai']

    return xarray.where(
        data_ai < 0.17,
        1,
        2
    )


def h_icefree(data, sic=0.15):
    '''
    Habitability based on ice-free area
    e.g. Sergeev+ 2022
    doi.org/10.3847/PSJ/ac6cf2
    '''
    return xarray.where(
        (data['siconc'] <= sic),
        2,
        1
    )


def h_obs(data_monthly):
    data_mean = data_monthly.mean('month').compute()

    # Terrestrial habitability
    ndvi_hab = xarray.where(
        data_mean['ndvi'] > 0.3,
        3,
        xarray.where(
            data_mean['ndvi'] > 0.15,
            2,
            xarray.where(
                data_mean['ndvi'].notnull(),
                1,
                np.nan
            )
        )
    )

    # Marine habitability
    chla_hab = xarray.where(
        data_monthly['chla'].min('month') > 0.15,
        3,
        xarray.where(
            data_mean['chla'] > 0.15,
            2,
            xarray.where(
                data_mean['chla'].notnull(),
                1,
                np.nan
            )
        )
    )

    return ndvi_hab.where(
        ndvi_hab.notnull(),
        chla_hab
    )


def h_s08(data):
    '''
    Spiegel+ 2008 / Jansen+ 2019
    doi.org/10.1086/588089
    doi.org/10.3847/1538-4357/ab113d
    Habitability based on 'liquid water' temperatures 0-100C
    '''
    return xarray.where(
        (data['tas'] >= 273.15) & (data['tas'] <= 373.15),
        2,
        1
    )


def h_s16(data):
    '''
    Silva+ 2016
    doi.org/10.1017/S1473550416000215
    Complex habitability based on multicellular poikilotherms 0-50C
    '''
    return xarray.where(
        (data['tas'] >= 273.15) & (data['tas'] <= 323.15),
        3,
        1
    )


def h_w25(data, t_unit='K'):
    '''
    Woodward+ 2025
    Complex + microbial habitability based on
    temperature, precipitation, and evaporation

    Units:
    - tas: 'K' or 'C'
    - pr, evspsbl: kg m2 s-1 (equiv to mm s-1)
    '''
    # Apply temperature filter
    hab_area_tas = h_w25_tas(data['tas'], t_unit)
    if (type(hab_area_tas) == type(None)):
        return None

    hab_area_complex = hab_area_tas['complex']
    hab_area_microbial = hab_area_tas['microbial']

    # Apply net precipitation filter if data provided
    if 'pr' in data and 'evspsbl' in data:
        hab_area_prnet = h_w25_water(
            data['pr'],
            data['evspsbl']
        )
        hab_area_complex = hab_area_complex.where(
            hab_area_complex.notnull() & hab_area_prnet.notnull()
        )
        hab_area_microbial = hab_area_microbial.where(
            hab_area_microbial.notnull() & hab_area_prnet.notnull()
        )

    # Merge complex & microbial masks and set masks to uniform values
    hab_area = hab_area_microbial\
        .where(hab_area_microbial.isnull(), 2)\
        .where(hab_area_complex.isnull(), 3)\
        .where(hab_area_microbial.notnull(), 1)

    return hab_area


def h_w25_water(data_pr, data_evspsbl):
    data_prnet = data_pr - data_evspsbl
    pr_min = 250.0 / (365.0 * 24 * 60 * 60)

    return data_prnet.where(
        (data_prnet >= 0) & (data_pr >= pr_min)
    )


def h_w25_tas(data_tas, t_unit='K'):
    if t_unit not in ['C', 'K']:
        print('Provide temperature unit `C` or `K`.')
        return None

    complex_t_min = 273.15
    complex_t_max = 323.15
    microbial_t_min = 251.15
    microbial_t_max = 393.15
    if t_unit == 'C':
        complex_t_min = 0
        complex_t_max = 50
        microbial_t_min = -22
        microbial_t_max = 120

    hab_area_complex = data_tas.where(
        (data_tas >= complex_t_min) & (data_tas < complex_t_max)
    )
    hab_area_microbial = data_tas.where(
        (data_tas >= microbial_t_min) & (data_tas < microbial_t_max)
    )

    return {
        'complex': hab_area_complex,
        'microbial': hab_area_microbial
    }
