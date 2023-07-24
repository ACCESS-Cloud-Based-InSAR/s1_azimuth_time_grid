from pathlib import Path

import pytest

test_data = Path(__file__).parent.resolve() / 'test_data'


@pytest.fixture(scope='session')
def gunw_azimuth_test():
    return test_data / 'S1-GUNW-A-R-064-tops-20210723_20210711-015000-00119W_00033N-PP-6267-v2_0_6.nc'
