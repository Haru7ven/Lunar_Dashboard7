# SOL: illumination and Earth-visibility planner for the lunar South Pole

Version 0.2 (prototype). Results are preliminary and not validated against an independent reference (section 7).

This folder contains the analysis pipeline, derived datasets, a standalone web page, tests, and the earlier versions of the code and data.

## 1. Purpose

For a chosen landing site near the lunar South Pole, the module computes the local terrain horizon from a LOLA digital elevation model, the direction of the Sun and of the Earth as seen from the site over time (NASA NAIF SPICE), and the intervals during which each body is above the local horizon. Outputs are summary metrics, time series and a decimated terrain grid, written as JSON files that a web dashboard can load.

## 2. Layout and quick start

```
sol-final/
  src/process_lunar.py      pipeline: DEM, horizon, SPICE, metrics, JSON
  tests/validate_jpl.py     Sun az-el from a JSON compared with JPL Horizons (needs internet)
  tests/compare_sites.py    summary table of two JSON files
  training_modules/         small from-scratch modules (horizon, ephemeris) with 14 pytest unit tests
  web/                      standalone page: index.html, app.js, data_A.json, data_B.json
  data/raw/, data/kernels/  DEM and SPICE kernels (not committed)
  archive/                  earlier versions of code, data and interface, kept unchanged
  setup.ps1, abrir_site.bat, requirements.txt
```

1. Install Python 3.10 or later and run `powershell -ExecutionPolicy Bypass -File .\setup.ps1` (packages and five SPICE kernels).
2. Place `ldem_875s_20m.img` and `ldem_875s_20m.lbl` in `data/raw/` (about 110 MB). Source: LRO LOLA Gridded Data Record, South Pole, 20 m per pixel, 87.5 S to the pole (https://imbrium.mit.edu/BROWSE/LOLA_GDR/POLAR/SOUTH_POLE, also through the PDS Geosciences Node ODE).
3. Generate a dataset: `python src/process_lunar.py --lat -89.45 --lon 222.7 --days 30 --output web/data_A.json`.
4. View the page: double-click `abrir_site.bat` (serves `web/` at http://localhost:8080).
5. Unit tests: `cd training_modules` and `python -m pytest`.

Raw datasets and kernels are not committed; they are referenced by source.

## 3. Data and kernels

| Item | Product |
|---|---|
| Terrain | LRO LOLA PDS4 GDR shape map, `ldem_875s_20m` (GDRDEM), 7584 x 7584 pixels, 20 m per pixel |
| Leap seconds (LSK) | `naif0012.tls` |
| Planetary ephemeris (SPK) | `de440s.bsp` (DE440, short version, 1849 to 2150) |
| Planetary constants (PCK) | `pck00011.tpc` |
| Lunar orientation (binary PCK) | `moon_pa_de440_200625.bpc` |
| Lunar frame kernel (FK) | `moon_de440_250416.tf` (defines `MOON_ME`) |

Kernels are downloaded from https://naif.jpl.nasa.gov/pub/naif/generic_kernels/.

## 4. Method

### 4.1. DEM and coordinate reference system

The DEM is read with rasterio from the `.lbl` label. The CRS reported by the label is a polar stereographic projection on a Moon sphere of radius 1737400 m (latitude of origin -90, central meridian 0, false easting and northing 0). Pixel size is 20 m and the grid bounds are +/- 75840 m in both axes, so the model covers from 87.5 S to the pole. Stored values are 16-bit integers with scale 0.5 and offset 1737400 m; nodata is -32768. SOL uses height = raw x 0.5, in metres above the 1737.4 km reference sphere. Heights are not referenced to a geoid.

### 4.2. Site definition

A site is given by latitude (negative south) and east longitude (0 to 360 degrees). Its projected position is computed on the sphere as rho = 2 R tan((90 + lat) / 2), x = rho sin(lon), y = rho cos(lon), with R = 1737400 m and unit scale factor at the pole. The terrain height is obtained by bilinear interpolation of the four surrounding DEM cells (half-pixel offset applied), and the observer height is ground height plus a mast height (default 2 m).

### 4.3. Terrain horizon

For each of 720 azimuths (0.5 degree step, clockwise from local north), a ray is marched from the site in the projected plane from 20 m to 70 km in 40 m steps. Local north points away from the pole (increasing latitude) and local east points toward increasing east longitude. At each step the elevation angle of the terrain sample is atan2(h - h_observer, d) - d / (2R), where the last term removes the curvature drop of the reference sphere. The horizon at that azimuth is the maximum of these angles. Cells with no data and positions outside the DEM are ignored, so rays do not see past the edge of the model. A sample is also ignored when any of its four neighbouring cells is nodata. The horizon at an arbitrary azimuth is obtained by linear interpolation with period 360 degrees.

### 4.4. Sun and Earth directions (SPICE)

Positions of the Sun and of the Earth relative to the Moon centre are obtained with `spkpos` in the `MOON_ME` (mean Earth / polar axis) frame, with light-time and stellar aberration correction (`LT+S`). The site vector is built with `georec` from longitude, latitude and observer height on a sphere of 1737.4 km. The local frame is up = site vector normalised, east = (0,0,1) x up normalised, north = up x east. Azimuth is atan2(v . east, v . north) modulo 360 and elevation is asin(v . up / |v|), where v is the body vector minus the site vector. Elevations are geometric (the Moon has no significant atmosphere).

### 4.5. Visibility and metrics

- Sun visible: sun elevation + 0.267 degrees is above the horizon at the Sun azimuth (upper limb of a disc of fixed angular radius 0.267 degrees). The test is binary; the fraction of the disc that is occulted is not computed.
- Earth visible: Earth elevation (centre of the disc, treated as a point) is above the horizon at the Earth azimuth.
- `sun_pct`, `earth_pct`, `both_pct`: percentage of epochs in the window in which the condition holds.
- `max_dark_h`, `max_noearth_h`: longest continuous run of epochs without Sun or without Earth, in hours. Runs are counted inside the window and are truncated at its edges, so a value equal to the window length means that the whole window is in that state.

### 4.6. Time

Epochs are UTC strings converted with the leap seconds kernel. Default window: 2026-11-14T00:00:00 UTC for 30 days at 1800 s steps (1440 epochs). The window length is a command line argument.

## 5. Geometric Earth visibility and communication availability

SOL computes geometric line of sight: the Earth centre is above the local horizon at the site. This is a necessary condition for direct-to-Earth (DTE) communication and not a measure of communication availability. Actual availability also depends on:

- which ground stations can see the Moon at that moment (Earth rotation, station elevation masks, antenna schedules);
- the link budget (transmit power, antenna gains, path loss at about 384,400 km, receiver noise, data rate and required margin);
- lander antenna type, pointing and gimbal limits, lander tilt on local slopes, and obstruction of the antenna by the lander body;
- the size of the Earth disc (about 1.9 degrees across) relative to a nearby ridge, which matters when the Earth is within a degree or two of the horizon;
- power availability for the radio (linked to illumination) and operational scheduling.

None of these is modelled. Reported Earth-visibility percentages are therefore upper bounds on geometric opportunity.

## 6. Assumptions and limitations

1. The DEM stops at 87.5 S. Sites outside it are not supported, and rays toward the model edge are truncated, which underestimates the horizon for sites near the boundary. Evaluating candidates over the whole polar region requires the 85 S or 80 S products (the 80 S file is about 4.2 GB).
2. Stereographic coordinates use unit scale at the pole; the distortion is of the order of 0.05 percent at the distances used.
3. The DEM is sampled by bilinear interpolation, without smoothing or void filling. Close to the observer (the first few pixels) the horizon on steep slopes is resolution-limited: the earlier nearest-neighbour version gave a maximum horizon of 45.7 degrees at Site B and 43.2 percent Earth visibility at Site A, against 34.2 degrees and 39.5 percent with bilinear sampling (files in `archive/`). Earth-visibility percentages should be quoted with an uncertainty of several percentage points.
4. Heights are relative to a sphere, and the local vertical is the spherical normal, not the terrain normal.
5. The Sun is a disc of constant radius (0.267 degrees); no penumbra, partial illumination, earthshine, or scattered light. Illumination is binary and does not represent solar-panel power.
6. The Earth is a point.
7. The horizon is computed out to 70 km and a 40 m step can skip features narrower than the step. The mast height is a free parameter and affects results strongly near the horizon.
8. The default window covers about one synodic month; it does not represent seasonal or multi-year variation. Use 365 days or more before drawing conclusions.
9. Azimuth is poorly conditioned very close to the pole; sites within a few kilometres of it should be interpreted with care.
10. Site coordinates in the shipped examples are approximate and must be confirmed against the DEM before use.

## 7. Validation status

Not validated against an independent reference. `tests/validate_jpl.py` samples epochs from a JSON file and compares the Sun and Earth azimuth and elevation with JPL Horizons for the same topocentric lunar position (tolerance 0.1 degrees); it has not been run against the live service. The horizon has no independent reference here; a possible cross-check is the LOLA average Sun visibility product (GDRVIS) from ODE. `training_modules` has 14 unit tests (flat terrain, synthetic slopes and geometry) that pass; they test the logic on synthetic data and do not validate the real DEM results.

Results of the comparison with Horizons: **to be added after the first run**.

## 8. Preliminary results (not validated)

Window: 2026-11-14 to 2026-12-13 UTC, 30 minute steps, mast 2 m, bilinear DEM sampling.

| Quantity | Site A | Site B |
|---|---|---|
| Latitude, longitude | -89.45, 222.7 E | -89.9, 129.2 E |
| Observer altitude (ground + mast) | 1957 m | -341 m |
| Horizon range | -2.85 to 0.32 degrees | 4.41 to 34.21 degrees |
| Sun visible | 100.0 % | 0.0 % |
| Earth visible (geometric) | 39.5 % | 0.0 % |
| Sun and Earth together | 39.5 % | 0.0 % |
| Longest period without Sun | 0.0 h | 720.0 h (whole window) |
| Longest period without Earth | 341.5 h | 720.0 h (whole window) |

Sensitivity to mast height and window length (same pipeline, same DEM; computed on 15 November 2026):

| Case | Sun visible | Earth visible | Longest without Sun | Longest without Earth |
|---|---|---|---|---|
| Site A, 30 days, mast 2 m | 100.0 % | 39.5 % | 0.0 h | 341.5 h |
| Site A, 30 days, mast 5 m | 100.0 % | 52.3 % | 0.0 h | 293.5 h |
| Site A, 30 days, mast 10 m | 100.0 % | 57.6 % | 0.0 h | 263.0 h |
| Site A, 365 days, mast 2 m | 81.5 % | 46.4 % | 232.5 h | 365.5 h |
| Site B, 30 days, mast 2 m | 0.0 % | 0.0 % | 720.0 h | 720.0 h |
| Site B, 30 days, mast 10 m | 0.0 % | 0.0 % | 720.0 h | 720.0 h |
| Site B, 365 days, mast 2 m | 0.0 % | 0.0 % | 8760.0 h | 8760.0 h |

Mast height and window length change the results far more than the DEM sampling method. The 100 % Sun value at Site A holds only for the 30 day window; over 365 days it is 81.5 %. The 365 day datasets are `web/data_A_365d.json` and `web/data_B_365d.json`.

Site coordinates are approximate and the names "Connecting Ridge" and "Shackleton" are not confirmed against the DEM. The window is about one synodic month.

## 9. Configuration

```
python src/process_lunar.py --lat -89.45 --lon 222.7 --days 365 --step 1800 --mast 2 --output web/data_A.json
```

Options: `--lat`, `--lon` (east, 0 to 360), `--date` (UTC start, default 2026-11-14T00:00:00), `--days` (default 30), `--step` (seconds, default 1800), `--mast` (m, default 2), `--dem`, `--kernels`, `--output`. Fixed constants are at the top of the script (reference radius, solar radius 0.267 degrees, horizon azimuth step 0.5 degrees, range 70 km, step 40 m, terrain preview stride 16). Not implemented: a batch run over a list of candidate sites and terrain slope metrics; `tests/compare_sites.py` only tabulates two existing files.

## 10. Output JSON specification

Each file has `site`, `stats`, `az`, `hor`, `time_series`, `dem`, `mx`, `my`. Fields are described below.

### 10.1. `site`

| Field | Unit | Meaning |
|---|---|---|
| `lat` | degrees | latitude, negative south |
| `lon` | degrees | east longitude, 0 to 360 |
| `x`, `y` | km | polar stereographic coordinates relative to the pole, x = rho sin(lon) and y = rho cos(lon) (section 4.2) |
| `alt` | m | observer height above the 1737.4 km sphere (ground + mast) |
| `ground_alt` | m | ground height above the same sphere |
| `mast` | m | observer height above ground |

### 10.2. `stats`

| Field | Unit | Meaning |
|---|---|---|
| `sun_pct` | percent of epochs | Sun visible (upper limb) |
| `earth_pct` | percent of epochs | Earth centre above horizon |
| `both_pct` | percent of epochs | both conditions at the same epoch |
| `max_dark_h` | hours | longest continuous interval without Sun inside the window |
| `max_noearth_h` | hours | longest continuous interval without Earth inside the window |

### 10.3. Horizon arrays (length 720)

| Field | Unit | Meaning |
|---|---|---|
| `az` | degrees | azimuth, 0 to 359.5, step 0.5, clockwise from local north |
| `hor` | degrees | terrain horizon elevation angle at that azimuth |

### 10.4. `time_series` (length N epochs, N = 1440 for 30 days at 30 min)

| Field | Unit | Meaning |
|---|---|---|
| `t` | UTC ISO 8601 string | epoch |
| `sun_az`, `sun_el` | degrees | Sun azimuth and geometric elevation (disc centre) |
| `ear_az`, `ear_el` | degrees | Earth azimuth and geometric elevation (disc centre) |
| `hz_s`, `hz_e` | degrees | local horizon at the Sun azimuth and at the Earth azimuth |
| `sun_vis`, `ear_vis` | 0 or 1 | visibility flags defined in section 4.5 |

### 10.5. Terrain grid

| Field | Unit | Shape | Meaning |
|---|---|---|---|
| `mx` | km | 474 | x coordinate of each column, ascending |
| `my` | km | 474 | y coordinate of each row, ascending |
| `dem` | m | 474 x 474 | height above the 1737.4 km sphere; `dem[i][j]` is at (`mx[j]`, `my[i]`) |

The grid is the 7584 x 7584 DEM taken at every 16th pixel (320 m spacing, no averaging), with missing cells set to the minimum height.

## 11. Notes for a web dashboard consumer

- Data files are static JSON (about 1.5 MB each). In Angular 18 and later the contents of `public/` are served from the application root, so the request URL is `data/data_A.json` and not `public/data/data_A.json`; confirm against the `assets` setting in `angular.json`. For a GitHub Pages project site use relative URLs and build with the matching `--base-href`.
- Plotly.js is larger than the default Angular bundle budgets; either raise the budgets or load it from a script tag.
- Azimuth is clockwise from local north, where north points away from the pole. Use the horizontal plane (`x`, `y`, km from the pole) and height as vertical axis, and exaggerate heights visually with a label.
- To place a site on a 3D lunar model, use latitude and east longitude on a sphere. The axis convention, scale and prime meridian of the model must be checked against known features before markers are trusted.
- The terrain grid is the largest part of each file and is identical for sites in the same DEM; it can be split into one shared file.
- Do not copy the raw DEM or kernels into the frontend. Reference the sources in sections 2 and 3.

## 12. Authorship, AI assistance and provenance

Author of the pipeline and datasets: Abudala Sualé, Dionisio Pelembe and Suneila Dos Anjos. The code, the standalone page and this document were developed with substantial assistance from AI tools: Claude (Anthropic) and Anti-Gravity to revise all of the code baselines and make specific corrections to debug.
## 13. Credits and licences

LOLA data: NASA PDS Geosciences Node and the LOLA science team. SPICE toolkit and kernels: NASA NAIF / JPL. Libraries: SpiceyPy, rasterio, numpy, astroquery, Plotly.js. Code licence: to be chosen by the team before publication.
