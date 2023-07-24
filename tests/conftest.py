from pathlib import Path

import pytest

test_data = Path(__file__).parent.resolve() / 'test_data'


@pytest.fixture(scope='session')
def gunw_azimuth_test():
    return test_data / 'S1-GUNW-A-R-064-tops-20210723_20210711-015000-00119W_00033N-PP-6267-v2_0_6.nc'


@pytest.fixture(scope='session')
def orbit_dict_for_azimuth_test():
    return {'reference': test_data / 'S1B_OPER_AUX_POEORB_OPOD_20210812T111941_V20210722T225942_20210724T005942.EOF',
            'secondary': test_data / 'S1B_OPER_AUX_POEORB_OPOD_20210731T111940_V20210710T225942_20210712T005942.EOF'}


@pytest.fixture(scope='session')
def slc_id_dict_for_azimuth_test():
    return {'reference': test_data / 'S1B_IW_SLC__1SDV_20210723T014947_20210723T015014_027915_0354B4_B3A9',
            'secondary': test_data / 'S1B_IW_SLC__1SDV_20210711T014947_20210711T015013_027740_034F80_D404'}
