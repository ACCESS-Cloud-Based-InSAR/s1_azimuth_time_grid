import datetime
from pathlib import Path

import hyp3lib
import numpy as np
import pandas as pd
import pytest
import xarray as xr

import s1_azimuth_time_grid
from s1_azimuth_time_grid import (get_inverse_weights_for_dates,
                                  get_n_closest_datetimes,
                                  get_s1_azimuth_time_grid,
                                  get_slc_id_from_point_and_time)


def get_start_time_from_slc_id(slc_id: str) -> datetime.datetime:
    acq_start_time_token = slc_id.split('_')[5]
    return pd.Timestamp(acq_start_time_token)


def test_get_slc_id():
    """
    Function tested gets SLC with respect to space and time.

    Test is derived using a grid similar to:
    S1-GUNW-A-R-064-tops-20210723_20210711-015000-00119W_00033N-PP-6267-v2_0_6.nc
    Over Los Angeles.

    Makes sure that there is no SLC 10 degrees translated along longitude at exactly same time.
    """

    lon = np.linspace(-119, -114, 6)
    lat = np.linspace(36, 33, 4)

    lat_center = np.mean(lat)
    lon_center = np.mean(lon)

    ref_time = datetime.datetime(2021, 7, 23, 1, 50, 0)
    ref_slc_ids = ['S1B_IW_SLC__1SDV_20210723T014947_20210723T015014_027915_0354B4_B3A9']

    sec_time = datetime.datetime(2021, 7, 11, 1, 50, 0)
    sec_slc_ids = ['S1B_IW_SLC__1SDV_20210711T014922_20210711T014949_027740_034F80_859D',
                   'S1B_IW_SLC__1SDV_20210711T014947_20210711T015013_027740_034F80_D404',
                   'S1B_IW_SLC__1SDV_20210711T015011_20210711T015038_027740_034F80_376C']

    ids = [ref_slc_ids, sec_slc_ids]
    times = [ref_time, sec_time]
    for time, slc_ids in zip(times, ids):
        slc_id = get_slc_id_from_point_and_time(lon_center, lat_center, time)
        assert slc_id in slc_ids

    for time, slc_ids in zip(times, ids):
        with pytest.raises(ValueError):
            _ = get_slc_id_from_point_and_time(lon_center + 10, lat_center, time)


@pytest.mark.parametrize('ifg_type', ['reference', 'secondary'],)
def test_s1_timing_array_wrt_slc_center_time(gunw_azimuth_test: Path,
                                             ifg_type: str,
                                             orbit_dict_for_azimuth_test: dict,
                                             slc_id_dict_for_azimuth_test: dict,
                                             mocker):
    """Make sure the SLC start time is within reasonable amount of grid. The flow chart is:

    (datetime, lon, lat) --> SLC id --> orbit --> azimuth time grid (via ISCE3)

    The input (leftmost) datetime should not deviate too much from azimuth time grid and that is the content of test.
    """

    group = 'science/grids/imagingGeometry'
    with xr.open_dataset(gunw_azimuth_test, group=group, mode='r') as ds:
        res_x, res_y = ds.rio.resolution()
        # assuming ul corner centered
        lat = ds.latitudeMeta.data - res_y / 2.
        lon = ds.longitudeMeta.data - res_x / 2.
        hgt = ds.heightsMeta.data
    group = 'science/radarMetaData/inputSLC'
    with xr.open_dataset(gunw_azimuth_test, group=f'{group}/{ifg_type}') as ds:
        slc_ids = ds['L1InputGranules'].data
        # Ensure non-empty and sorted by acq_time
        slc_ids = sorted(list(filter(lambda x: x, slc_ids)))

    # Get the middle SLC start_time
    n = len(slc_ids)
    slc_start_time = get_start_time_from_slc_id(slc_ids[n // 2]).to_pydatetime()

    # Azimuth time grid
    mocker.patch('hyp3lib.get_orb.downloadSentinelOrbitFile',
                 # Hyp3 Lib returns 2 values
                 return_value=(orbit_dict_for_azimuth_test[ifg_type], ''))
    mocker.patch('s1_azimuth_time_grid.s1_azimuth_timing._asf_query',
                 return_value=(slc_id_dict_for_azimuth_test[ifg_type], ''))
    time_grid = get_s1_azimuth_time_grid(lon, lat, hgt, slc_start_time)

    abs_diff = np.abs(time_grid - np.datetime64(slc_start_time)) / np.timedelta64(1, 's')
    # Assert the absolute difference is less than 40 seconds from start time
    # Recall the SLC image spans approximately 30 seconds, but this grid is 1/3-1/2 bigger on each end.
    # And our time we are comparing against is a *start_time*
    assert np.all(abs_diff < 40)

    s1_azimuth_time_grid.s1_azimuth_timing._asf_query.assert_called_once()
    hyp3lib.get_orb.downloadSentinelOrbitFile.assert_called_once()


@pytest.mark.parametrize('ifg_type', ['reference', 'secondary'])
def test_s1_timing_array_wrt_variance(gunw_azimuth_test: Path,
                                      ifg_type: str,
                                      orbit_dict_for_azimuth_test: dict,
                                      slc_id_dict_for_azimuth_test: dict,
                                      mocker):
    """Make sure along the hgt dimension of grid there is very small deviations
    """
    group = 'science/grids/imagingGeometry'
    with xr.open_dataset(gunw_azimuth_test, group=group, mode='r') as ds:
        res_x, res_y = ds.rio.resolution()
        # assuming ul corner centered
        lat = ds.latitudeMeta.data - res_y / 2.
        lon = ds.longitudeMeta.data - res_x / 2.
        hgt = ds.heightsMeta.data

    group = 'science/radarMetaData/inputSLC'
    with xr.open_dataset(gunw_azimuth_test, group=f'{group}/{ifg_type}') as ds:
        slc_ids = ds['L1InputGranules'].data
        # Ensure non-empty and sorted by acq_time
        slc_ids = sorted(list(filter(lambda x: x, slc_ids)))

    # Get the middle SLC start_time
    slc_start_time = get_start_time_from_slc_id(slc_ids[0]).to_pydatetime()

    # Azimuth time grid
    # Azimuth time grid
    mocker.patch('hyp3lib.get_orb.downloadSentinelOrbitFile',
                 # Hyp3 Lib returns 2 values
                 return_value=(orbit_dict_for_azimuth_test[ifg_type], ''))
    mocker.patch('s1_azimuth_time_grid.s1_azimuth_timing._asf_query',
                 return_value=(slc_id_dict_for_azimuth_test[ifg_type], ''))
    X = get_s1_azimuth_time_grid(lon, lat, hgt, slc_start_time)

    Z = (X - X.min()) / np.timedelta64(1, 's')
    std_hgt = Z.std(axis=0).max()
    # Asserts the standard deviation in height is less than 2e-3 seconds
    assert np.all(std_hgt < 2e-3)

    s1_azimuth_time_grid.s1_azimuth_timing._asf_query.assert_called_once()
    hyp3lib.get_orb.downloadSentinelOrbitFile.assert_called_once()


def test_n_closest_dts():
    """Check that the n closest datetimes are correct and in correct order.
    Order being absolute distance to supplied datetime"""
    n_target_datetimes = 3
    time_step = 6
    dt = datetime.datetime(2023, 1, 1, 11, 1, 1)
    out = get_n_closest_datetimes(dt, n_target_datetimes, time_step)
    expected = [datetime.datetime(2023, 1, 1, 12, 0, 0),
                datetime.datetime(2023, 1, 1, 6, 0, 0),
                datetime.datetime(2023, 1, 1, 18, 0, 0)]
    assert out == expected

    n_target_datetimes = 4
    time_step = 2
    dt = datetime.datetime(2023, 2, 1, 8, 1, 1)
    out = get_n_closest_datetimes(dt, n_target_datetimes, time_step)
    expected = [datetime.datetime(2023, 2, 1, 8, 0, 0),
                datetime.datetime(2023, 2, 1, 10, 0, 0),
                datetime.datetime(2023, 2, 1, 6, 0, 0),
                datetime.datetime(2023, 2, 1, 12, 0, 0)]
    assert out == expected

    n_target_datetimes = 2
    time_step = 4
    dt = datetime.datetime(2023, 1, 1, 20, 1, 1)
    out = get_n_closest_datetimes(dt, n_target_datetimes, time_step)
    expected = [datetime.datetime(2023, 1, 1, 20, 0, 0),
                datetime.datetime(2023, 1, 2, 0, 0, 0)]
    assert out == expected

    n_target_datetimes = 2
    # Does not divide 24 hours so has period > 1 day.
    time_step = 5
    dt = datetime.datetime(2023, 1, 1, 20, 1, 1)
    with pytest.raises(ValueError):
        _ = get_n_closest_datetimes(dt, n_target_datetimes, time_step)


input_times = [np.datetime64('2021-01-01T07:00:00'),
               np.datetime64('2021-01-01T07:00:00'),
               np.datetime64('2021-01-01T06:00:00')
               ]
windows = [6, 3, 6]
expected_weights_list = [[.833, .167, 0],
                         [1., 0., 0.],
                         [1., 0., 0.]]


@pytest.mark.parametrize('input_time, temporal_window, expected_weights',
                         zip(input_times, windows, expected_weights_list))
def test_inverse_weighting(input_time: np.datetime64,
                           temporal_window: int | float,
                           expected_weights: list[float]):
    """The test is designed to determine valid inverse weighting

    Parameters
    ----------
    input_time : np.datetime64
        This input datetime is used to create a 4 x 4  array X such that
        X[0, 0] = input time and the remainder are incremented by 1 second
    temporal_window : int | float
        The size (in hours) to consider for weighting
    expected_weights : float
        This is a single float because the 1 second delta does (in X construction)
        does not impact weights significantly (only tested 1e-3)
    """

    N = 4

    date_0 = np.datetime64('2021-01-01T06:00:00')
    date_1 = np.datetime64('2021-01-01T12:00:00')
    date_2 = np.datetime64('2021-01-01T00:00:00')
    dates = [date_0, date_1, date_2]
    dates = list(map(lambda dt: dt.astype(datetime.datetime), dates))

    timing_grid = np.full((N, N),
                          input_time,
                          dtype='datetime64[ms]')
    delta = np.timedelta64(1, 's') * np.arange(N**2)
    delta = delta.reshape((N, N))

    out_weights = get_inverse_weights_for_dates(timing_grid,
                                                dates,
                                                temporal_window_hours=temporal_window
                                                )

    # Weights should be approximately (in this order): .833..., .1666..., 0
    # Note the delta makes all entries outside of top right corner slightly different
    for k in range(3):
        np.testing.assert_almost_equal(expected_weights[k],
                                       out_weights[k],
                                       1e-3)
