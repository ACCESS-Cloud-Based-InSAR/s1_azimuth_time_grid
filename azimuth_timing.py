import numpy as np
import isce3.ext.isce3 as isce


SPEED_OF_LIGHT = 299792458.0


def get_azimuth_timing_grid(lon: np.ndarray, lat: np.ndarray, hgt:  np.ndarray, orb: isce.core.Orbit) -> np.ndarray:
    '''
    Source: https://github.com/dbekaert/RAiDER/blob/dev/tools/RAiDER/losreader.py#L601C1-L674C22

    lon, lat, hgt are coordinate arrays (this routine makes a mesh to comute azimuth timing grid)
    '''

    num_iteration = 30
    residual_threshold = 1.0e-7

    elp = isce.core.Ellipsoid()
    dop = isce.core.LUT2d()
    look = isce.core.LookSide.Right

    hgt_mesh, lat_mesh, lon_mesh = np.meshgrid(hgt, lat, lon,
                                               # indexing keyword argument
                                               # Ensures output dimensions
                                               # align with order the inputs
                                               # height x latitude x longitude
                                               indexing='ij')
    m, n, p = hgt_mesh.shape
    az_arr = np.full((m, n, p),
                     np.datetime64('NaT'),
                     # source: https://stackoverflow.com/a/27469108
                     dtype='datetime64[s]')

    for ind_0 in range(m):
        for ind_1 in range(n):
            for ind_2 in range(p):

                hgt_pt, lat_pt, lon_pt = (hgt_mesh[ind_0, ind_1, ind_2],
                                          lat_mesh[ind_0, ind_1, ind_2],
                                          lon_mesh[ind_0, ind_1, ind_2])

                input_vec = np.array([np.deg2rad(lon_pt),
                                      np.deg2rad(lat_pt),
                                      hgt_pt])

                aztime, sr = isce.geometry.geo2rdr(
                    input_vec, elp, orb, dop, 0.06, look,
                    threshold=residual_threshold,
                    maxiter=num_iteration,
                    delta_range=10.0)

                rng_seconds = sr / SPEED_OF_LIGHT
                aztime = aztime + rng_seconds
                aztime_isce = orb.reference_epoch + isce.core.TimeDelta(aztime)
                aztime_np = np.datetime64(aztime_isce.isoformat())
                az_arr[ind_0, ind_1, ind_2] = aztime_np
    return az_arr