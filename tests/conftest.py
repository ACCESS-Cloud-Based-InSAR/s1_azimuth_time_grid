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
