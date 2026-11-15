# SOL analysis module

Version 0.1 (prototype). Results are preliminary and not yet validated against an independent reference (section 7).

This document describes only the SOL analysis module: the processing pipeline, the derived JSON datasets and the validation script. It does not describe other parts of the repository.

## 1\. Purpose

For a chosen landing site near the lunar South Pole, the module computes the local terrain horizon from a LOLA digital elevation model, the direction of the Sun and of the Earth as seen from the site over time (NASA NAIF SPICE), and the intervals during which each body is above the local horizon. Outputs are summary metrics, time series and a decimated terrain grid, written as JSON files that a web dashboard can load.

## 2\. Layout and quick start

```
analysis/
  run.py            pipeline (DEM, horizon, SPICE, metrics, JSON)
  validar.py        Sun/Earth az-el comparison against JPL Horizons (not yet run against the live service)
  setup.ps1         installs Python packages and downloads the five SPICE kernels (Windows PowerShell)
  requirements.txt  spiceypy, rasterio, numpy, astroquery
  data/raw/         ldem\_875s\_20m.img and .lbl (not committed, about 110 MB)
  data/kernels/     SPICE kernels (not committed, downloaded by setup.ps1)
  preview/          local test page written by run.py (not committed)
```

Derived datasets are written to `public/data/` (see section 9) and are the only outputs meant for the frontend.

1. Install Python 3.10 or later.
2. Place `ldem\_875s\_20m.img` and `ldem\_875s\_20m.lbl` in `data/raw/`. Source: LRO LOLA Gridded Data Record, South Pole, 20 m per pixel, 87.5 S to the pole (https://imbrium.mit.edu/BROWSE/LOLA\_GDR/POLAR/SOUTH\_POLE, also available through the PDS Geosciences Node ODE).
3. From the `analysis` folder run `powershell -ExecutionPolicy Bypass -File .\\setup.ps1`.
4. Run `$env:SOL\_OUT = "..\\public\\data"` and then `python run.py -89.45 222.7 365 A 2`.

Raw datasets and kernels are not committed; they are referenced by source.

## 3\. Data and kernels

|Item|Product|
|-|-|
|Terrain|LRO LOLA PDS4 GDR shape map, `ldem\_875s\_20m` (GDRDEM), 7584 x 7584 pixels, 20 m per pixel|
|Leap seconds (LSK)|`naif0012.tls`|
|Planetary ephemeris (SPK)|`de440s.bsp` (DE440, short version, 1849 to 2150)|
|Planetary constants (PCK)|`pck00011.tpc`|
|Lunar orientation (binary PCK)|`moon\_pa\_de440\_200625.bpc`|
|Lunar frame kernel (FK)|`moon\_de440\_250416.tf` (defines `MOON\_ME`)|

Kernels are downloaded from https://naif.jpl.nasa.gov/pub/naif/generic\_kernels/.

## 4\. Method

### 4.1. DEM and coordinate reference system

The DEM is read with rasterio from the `.lbl` label. The CRS reported by the label is a polar stereographic projection on a Moon sphere of radius 1737400 m (latitude of origin -90, central meridian 0, false easting and northing 0). Pixel size is 20 m and the grid bounds are +/- 75840 m in both axes, so the model covers from 87.5 S to the pole. Stored values are 16-bit integers with scale 0.5 and offset 1737400 m; nodata is -32768. SOL uses height = raw x 0.5, in metres above the 1737.4 km reference sphere. Heights are not referenced to a geoid.

### 4.2. Site definition

A site is given by latitude (negative south) and east longitude (0 to 360 degrees). Its projected position is computed on the sphere as rho = 2 R tan((90 + lat) / 2), x = rho sin(lon), y = rho cos(lon), with R = 1737400 m and unit scale factor at the pole. The ground height is read from the DEM at that pixel (nearest neighbour) and the observer height is ground height plus a mast height (default 2 m).

### 4.3. Terrain horizon

For each of 720 azimuths (0.5 degree step, clockwise from local north), a ray is marched from the site in the projected plane from 20 m to 70 km in 40 m steps. Local north points away from the pole (increasing latitude) and local east points toward increasing east longitude. At each step the elevation angle of the terrain sample is atan2(h - h\_observer, d) - d / (2R), where the last term removes the curvature drop of the reference sphere. The horizon at that azimuth is the maximum of these angles. Cells with no data and positions outside the DEM are ignored, so rays do not see past the edge of the model. The horizon at an arbitrary azimuth is obtained by linear interpolation with period 360 degrees.

### 4.4. Sun and Earth directions (SPICE)

Positions of the Sun and of the Earth relative to the Moon centre are obtained with `spkpos` in the `MOON\_ME` (mean Earth / polar axis) frame, with light-time and stellar aberration correction (`LT+S`). The site vector is built with `georec` from longitude, latitude and observer height on a sphere of 1737.4 km. The local frame is up = site vector normalised, east = (0,0,1) x up normalised, north = up x east. Azimuth is atan2(v . east, v . north) modulo 360 and elevation is asin(v . up / |v|), where v is the body vector minus the site vector. Elevations are geometric (the Moon has no significant atmosphere).

### 4.5. Visibility and metrics

* Sun visible: sun elevation + 0.267 degrees is above the horizon at the Sun azimuth (upper limb of a disc of fixed angular radius 0.267 degrees). The test is binary; the fraction of the disc that is occulted is not computed.
* Earth visible: Earth elevation (centre of the disc, treated as a point) is above the horizon at the Earth azimuth.
* `sun\_pct`, `earth\_pct`, `both\_pct`: percentage of epochs in the window in which the condition holds.
* `max\_dark\_h`, `max\_noearth\_h`: longest continuous run of epochs without Sun or without Earth, in hours. Runs are counted inside the window and are truncated at its edges, so a value equal to the window length means that the whole window is in that state.

### 4.6. Time

Epochs are UTC strings converted with the leap seconds kernel. Default window: 2026-11-14T00:00:00 UTC for 30 days at 1800 s steps (1440 epochs). The window length is a command line argument.

## 5\. Geometric Earth visibility and communication availability

SOL computes geometric line of sight: the Earth centre is above the local horizon at the site. This is a necessary condition for direct-to-Earth (DTE) communication and not a measure of communication availability. Actual availability also depends on:

* which ground stations can see the Moon at that moment (Earth rotation, station elevation masks, antenna schedules);
* the link budget (transmit power, antenna gains, path loss at about 384,400 km, receiver noise, data rate and required margin);
* lander antenna type, pointing and gimbal limits, lander tilt on local slopes, and obstruction of the antenna by the lander body;
* the size of the Earth disc (about 1.9 degrees across) relative to a nearby ridge, which matters when the Earth is within a degree or two of the horizon;
* power availability for the radio (linked to illumination) and operational scheduling.

None of these is modelled. Reported Earth-visibility percentages are therefore upper bounds on geometric opportunity.

## 6\. Assumptions and limitations

1. The DEM stops at 87.5 S. Sites outside it are not supported, and rays toward the model edge are truncated, which underestimates the horizon for sites near the boundary. Evaluating candidates over the whole polar region requires the 85 S or 80 S products (the 80 S file is about 4.2 GB).
2. Stereographic coordinates use unit scale at the pole; the distortion is of the order of 0.05 percent at the distances used.
3. The DEM is sampled by nearest neighbour; no interpolation, smoothing or void filling.
4. Heights are relative to a sphere, and the local vertical is the spherical normal, not the terrain normal.
5. The Sun is a disc of constant radius (0.267 degrees); no penumbra, partial illumination, earthshine, or scattered light. Illumination is binary and does not represent solar-panel power.
6. The Earth is a point.
7. The horizon is computed out to 70 km and a 40 m step can skip features narrower than the step. The mast height is a free parameter and affects results strongly near the horizon.
8. The default window covers about one synodic month; it does not represent seasonal or multi-year variation. Use 365 days or more before drawing conclusions.
9. Azimuth is poorly conditioned very close to the pole; sites within a few kilometres of it should be interpreted with care.
10. Site coordinates in the shipped examples are approximate and must be confirmed against the DEM before use.

## 7\. Validation status

Not yet validated. `validar.py` compares azimuth and elevation of the Sun and of the Earth computed with SPICE against JPL Horizons for five epochs, using a tolerance of 0.1 degrees. It was written without access to the live service and has not been run against it. The comparison covers body directions only; the horizon has no independent reference in this repository. A possible cross-check is the LOLA average Sun visibility product (GDRVIS) available through ODE.

Results of the comparison: **to be added after the first run**.

## 8\. Preliminary results (not validated)

Window: 2026-11-14 to 2026-12-13 UTC, mast 2 m.

|Quantity|Site A|Site B|
|-|-|-|
|Latitude, longitude|-89.45, 222.7 E|-89.9, 129.2 E|
|Observer altitude|1958 m|-338 m|
|Horizon range|about -2.8 to 0.2 degrees|about 4.4 to 45.7 degrees|
|Sun visible|100.0 %|0.0 %|
|Earth visible|43.2 %|0.0 %|
|Sun and Earth together|43.2 %|0.0 %|
|Longest period without Sun|0.0 h|720.0 h (whole window)|
|Longest period without Earth|330.0 h|720.0 h (whole window)|

These values are from `data\_A.json` and `data\_B.json` in `public/data/`. The location names ("Connecting Ridge", "Shackleton") are not confirmed against the DEM.

## 9\. Configuration

```
python run.py \[LAT] \[LON] \[DAYS] \[NAME] \[MAST\_m]
```

All arguments are optional (defaults: -89.45, 222.7, 30 days, no JSON written, 2 m). When NAME is given, `data\_NAME.json` is written to the folder in the environment variable `SOL\_OUT` (default `web/` inside `analysis/`). A test page is always written to `preview/index.html`. Fixed parameters are at the top of `run.py` (start epoch, 1800 s step, kernel list, solar radius). Not yet implemented: a site list file and a batch script that runs several candidate sites and writes a comparison table (illumination, longest darkness, horizon, Earth visibility, terrain constraints such as local slope).

## 10\. Output JSON specification

The JSON files currently in `public/data/` use a nested layout with a `time\_series` object. The `run.py` in this repository writes the same fields at the top level and adds optional terrain arrays (`x3`, `y3`, `z3`). A consumer should read `data.time\_series || data` to accept both layouts. The shipped JSON files were produced by an earlier version of the pipeline and have not been regenerated with this `run.py`; regenerating them and comparing the `stats` block is the first reproducibility check.

### 10.1. `site`

|Field|Unit|Meaning|
|-|-|-|
|`lat`|degrees|latitude, negative south|
|`lon`|degrees|east longitude, 0 to 360|
|`x`, `y`|km|polar stereographic coordinates relative to the pole, x = rho sin(lon) and y = rho cos(lon) (section 4.2)|
|`alt`|m|observer height above the 1737.4 km sphere (ground + mast)|
|`ground\_alt`|m|ground height above the same sphere|
|`mast`|m|observer height above ground|

### 10.2. `stats`

|Field|Unit|Meaning|
|-|-|-|
|`sun\_pct`|percent of epochs|Sun visible (upper limb)|
|`earth\_pct`|percent of epochs|Earth centre above horizon|
|`both\_pct`|percent of epochs|both conditions at the same epoch|
|`max\_dark\_h`|hours|longest continuous interval without Sun inside the window|
|`max\_noearth\_h`|hours|longest continuous interval without Earth inside the window|

### 10.3. Horizon arrays (length 720)

|Field|Unit|Meaning|
|-|-|-|
|`az`|degrees|azimuth, 0 to 359.5, step 0.5, clockwise from local north|
|`hor`|degrees|terrain horizon elevation angle at that azimuth|

### 10.4. `time\_series` (length N epochs, N = 1440 for 30 days at 30 min)

|Field|Unit|Meaning|
|-|-|-|
|`t`|UTC ISO 8601 string|epoch|
|`sun\_az`, `sun\_el`|degrees|Sun azimuth and geometric elevation (disc centre)|
|`ear\_az`, `ear\_el`|degrees|Earth azimuth and geometric elevation (disc centre)|
|`hz\_s`, `hz\_e`|degrees|local horizon at the Sun azimuth and at the Earth azimuth|
|`sun\_vis`, `ear\_vis`|0 or 1|visibility flags defined in section 4.5|

### 10.5. Terrain grid

|Field|Unit|Shape|Meaning|
|-|-|-|-|
|`mx`|km|474|x coordinate of each column, ascending|
|`my`|km|474|y coordinate of each row, ascending|
|`dem`|m|474 x 474|height above the 1737.4 km sphere; `dem\[i]\[j]` is at (`mx\[j]`, `my\[i]`)|

The grid is the 7584 x 7584 DEM taken at every 16th pixel (320 m spacing, no averaging), with missing cells set to the minimum height. `run.py` also writes `x3`, `y3` (km, 237 values each, every 32nd pixel) and `z3` (km, 237 x 237) for a 3D terrain view.

## 11\. Notes for a web dashboard consumer

* Data files are static JSON (about 1.5 MB each). In Angular 18 and later the contents of `public/` are served from the application root, so the request URL is `data/data\_A.json` and not `public/data/data\_A.json`; confirm against the `assets` setting in `angular.json`. For a GitHub Pages project site use relative URLs and build with the matching `--base-href`.
* Plotly.js is larger than the default Angular bundle budgets; either raise the budgets or load it from a script tag.
* Azimuth is clockwise from local north, where north points away from the pole. Use the horizontal plane (`x`, `y`, km from the pole) and height as vertical axis, and exaggerate heights visually with a label.
* To place a site on a 3D lunar model, use latitude and east longitude on a sphere. The axis convention, scale and prime meridian of the model must be checked against known features before markers are trusted.
* The terrain grid is the largest part of each file and is identical for sites in the same DEM; it can be split into one shared file.
* Do not copy the raw DEM or kernels into the frontend. Reference the sources in sections 2 and 3.

## 12\. Authorship and AI assistance

Author of this module: Abudala Sualé, Dionísio Pelembe, Suneila dos Anjos Machanguana

The pipeline code, the standalone planner page and this document were developed with assistance from AI tools: Claude (Anthropic) was used to revise code and documentation and Anti-Gravity (to fix specific bugs meanwhile running the code). The author ran the calculations, reviewed the outputs and made the decisions on scope and sites. Statements in this document describe what the code does as written and have not been independently verified.

## 13\. Credits and licences

LOLA data: NASA PDS Geosciences Node and the LOLA science team. SPICE toolkit and kernels: NASA NAIF / JPL. Libraries: SpiceyPy, rasterio, numpy, astroquery, Plotly.js. Code licence: to be chosen by the team before publication.

