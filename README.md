# S1_azimuth_time_grid

This repo uses `isce3` to generate an azimuth timing array using `geo2rdr` based on:

1. (center) time of acquisition
2. A lat/lon/height grid

Uses packages for obtaining orbit files for correct position/time. If not avaiable, will throw error.
Expected to use `ARIA-S1-GUNW` for inputs above.

The motiviation for this package is to do basic interpolation for different phase screens across a geographic cube. 
This is originally based on code from RAiDER. Joint work of Charlie Marshak, Sim Sangha, and David Bekaert.

## Installation

1. `mamba env update -f environment.yml`
2. `pip install .`
3. `conda activate azimuth-timing`
4. `python -m ipykernel install --user --name azimuth-timing`

Use the notebook `API.npynb` to explore the basic API