# 🌕 SOL — Lunar Solar Illumination & Direct-to-Earth Visibility Planner

**An Autonomous Environmental Analysis and Mission-Planning Prototype for the Lunar South Pole**

**NASA Space Apps Challenge 2026**  
**Challenge Domain:** Planetary Exploration, Artemis & Commercial Lunar Payload Services (CLPS)  
**Development Location:** Mozambique  
**Institution:** Faculty of Medicine, Eduardo Mondlane University (UEM)  
**Version:** 0.2 — Scientific Prototype

## Contents

- [1. Project Overview](#-1-project-overview)
- [2. The Problem](#-2-the-problem)
- [3. Project Objectives](#-3-project-objectives)
- [4. Scientific Data and NASA Resources](#️-4-scientific-data-and-nasa-resources)
- [5. Scientific Methodology](#-5-scientific-methodology)
- [6. Computational Architecture](#-6-computational-architecture)
- [7. Case Study: Lunar South Pole Candidate Sites](#-7-case-study-lunar-south-pole-candidate-sites)
- [8. Sensitivity Analysis](#-8-sensitivity-analysis)
- [9. Scientific Outputs](#-9-scientific-outputs)
- [10. Validation and Testing](#-10-validation-and-testing)
- [11. Assumptions and Limitations](#️-11-assumptions-and-limitations)
- [12. Installation and Reproducibility](#-12-installation-and-reproducibility)
- [13. Future Development](#-13-future-development)
- [14. Team and Contributions](#-14-team-and-contributions)
- [15. Artificial Intelligence Assistance Disclosure](#-15-artificial-intelligence-assistance-disclosure)
- [16. Credits and Acknowledgements](#-16-credits-and-acknowledgements)
- [17. Conclusion](#-17-conclusion)

---

## 🌑 1. Project Overview

SOL (Solar Illumination & Direct-to-Earth Visibility Planner) is a computational platform designed to investigate two fundamental environmental constraints affecting robotic and human exploration of the lunar South Pole:

- The availability of direct solar illumination at a selected lunar surface location.
- The geometric visibility of Earth from that location, considering surrounding lunar topography.

Developed as a scientific and engineering prototype for the NASA Space Apps Challenge 2026, SOL integrates high-resolution lunar elevation data, numerical terrain-obstruction algorithms, planetary ephemerides, and interactive scientific visualization.

The platform combines publicly available scientific resources from:

- NASA Lunar Reconnaissance Orbiter (LRO).
- Lunar Orbiter Laser Altimeter (LOLA).
- NASA Navigation and Ancillary Information Facility (NAIF).
- NASA Jet Propulsion Laboratory (JPL).
- NASA Planetary Data System (PDS).

Its primary objective is to transform complex lunar topographic and astronomical information into interpretable environmental intelligence that can support preliminary landing-site assessment and lunar surface mission planning.

SOL is designed as a research and decision-support prototype. It is not an operational NASA flight-control system, and its preliminary results must not be interpreted as flight-certified mission predictions.

---

## 🚀 2. The Problem

The lunar South Pole represents one of the most challenging environments for future lunar exploration.

Unlike locations at lower lunar latitudes, polar regions experience extremely low solar elevation angles. The Sun can remain close to the local horizon, allowing distant crater rims, ridges, and elevated terrain to obstruct direct sunlight.

Two major operational challenges emerge.

### 2.1. Solar Energy Availability

Solar-powered landers, rovers, instruments, and surface infrastructure depend on adequate illumination to generate electrical energy.

Extended periods of darkness can:

- Reduce available electrical power.
- Limit scientific operations.
- Increase battery discharge.
- Create thermal-management challenges.
- Interrupt surface activities.

Identifying locations with favorable illumination characteristics is therefore an important component of preliminary lunar mission planning.

### 2.2. Direct-to-Earth Communication

Lunar surface missions also require reliable communication with Earth.

Although the Moon has no significant atmosphere, local terrain can obstruct the geometric line of sight between a lander and Earth.

A crater rim or elevated ridge may prevent direct visibility even when Earth is geometrically above the lunar horizon.

Consequently, solar illumination and Earth visibility must be evaluated independently.

SOL addresses both constraints through a shared topographic and astronomical analysis framework.

---

## 🎯 3. Project Objectives

The project was developed around five principal objectives:

- Reconstruct the local topographic horizon around selected lunar South Pole locations.
- Calculate the apparent positions of the Sun and Earth using NASA planetary ephemerides.
- Determine direct solar visibility and geometric Earth visibility over configurable observation periods.
- Compare candidate landing locations under consistent simulation conditions.
- Present environmental information through an interactive web-based scientific dashboard.

The intended application is preliminary environmental assessment for lunar surface missions, particularly those associated with Artemis and Commercial Lunar Payload Services (CLPS) exploration objectives.

---

## 🛰️ 4. Scientific Data and NASA Resources

SOL uses publicly available planetary science datasets and astronomical resources.

| Resource | Application |
| --- | --- |
| LRO LOLA | Lunar surface elevation and topographic reconstruction |
| LDEM_875S_20M | High-resolution South Pole digital elevation model |
| NASA NAIF SPICE | Planetary positions, lunar orientation, and reference frames |
| DE440 | Planetary and lunar ephemerides |
| JPL Horizons | Independent reference for astronomical calculations |
| NASA PDS Geosciences Node | Access to planetary elevation products |
| LROC QuickMap | Lunar cartographic reference and contextual analysis |

### 4.1. Lunar Topographic Data

The principal elevation dataset is:

| Parameter | Description |
| --- | --- |
| Dataset | LDEM_875S_20M |
| Instrument | Lunar Orbiter Laser Altimeter (LOLA) |
| Spacecraft | Lunar Reconnaissance Orbiter (LRO) |
| Nominal spatial resolution | 20 metres per pixel |
| Coverage | 87.5°S to 90°S |
| Projection | South Polar Stereographic |
| Reference radius | 1,737,400 metres |
| Grid dimensions | 7,584 × 7,584 pixels |

Original elevation samples are stored as 16-bit integer values with a nominal scale factor of 0.5 and an offset of 1,737,400 metres.

SOL applies the dataset's elevation scaling and converts the resulting values into elevations relative to the reference lunar sphere.

The model does not currently use an independently applied lunar geoid or selenoid correction.

Primary data source:

[LOLA South Pole data](https://imbrium.mit.edu/BROWSE/LOLA_GDR/POLAR/SOUTH_POLE)

Additional access is available through the NASA PDS Geosciences Node.

### 4.2. NASA NAIF SPICE Kernels

Astronomical calculations use the following resources:

| Kernel | Purpose |
| --- | --- |
| de440s.bsp | Planetary and lunar ephemerides |
| naif0012.tls | Leap-second conversions |
| pck00011.tpc | Planetary constants |
| moon_pa_de440_200625.bpc | Lunar physical orientation |
| moon_de440_250416.tf | Lunar reference-frame definitions |

The calculations use the MOON_ME reference frame, representing the lunar Mean Earth / Polar Axis orientation.

These kernels provide the astronomical and reference-frame information required to calculate the apparent positions of the Sun and Earth relative to a selected lunar surface observer.

Official kernel repository:

[NASA NAIF generic kernels](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/)

### 4.3. JPL Horizons

NASA JPL Horizons is identified as the independent reference system for cross-validation of astronomical position calculations.

[NASA JPL Horizons](https://ssd.jpl.nasa.gov/horizons/)

The project includes an automated validation utility:

`tests/validate_jpl.py`

This script is designed to compare SOL-generated astronomical coordinates against independent Horizons reference values.

The validation procedure is described in Section 10.

---

## 🔬 5. Scientific Methodology

SOL integrates three principal computational stages:

- Lunar terrain reconstruction and horizon profiling.
- Astronomical position calculations.
- Solar and Earth visibility assessment.

### 5.1. Coordinate System and Site Definition

The project uses a South Polar Stereographic coordinate system centered on the lunar South Pole.

The reference lunar radius is:

\(R_{\mathrm{Moon}} = 1{,}737{,}400\,\mathrm{m}\)

For a selected lunar latitude and east longitude, the projected radial distance is calculated using:

\(\rho = 2R_{\mathrm{Moon}}\tan\left(90^\circ + \frac{\phi}{2}\right)\)

The projected coordinates are:

\(x = \rho\sin(\lambda),\quad y = \rho\cos(\lambda)\)

Where:

- \(\phi\) is lunar latitude.
- \(\lambda\) is east longitude.
- \(\rho\) is projected radial distance.

The projection convention and longitude orientation must remain consistent with the DEM metadata.

The observer elevation is calculated by adding the selected antenna mast height to the interpolated ground elevation.

The current default mast height is 2 metres.

### 5.2. Sub-Pixel Terrain Interpolation

SOL uses bilinear interpolation to estimate terrain elevations at positions between DEM grid cells.

Instead of selecting the nearest elevation sample, the algorithm evaluates the four surrounding pixels.

For interpolation coordinates \(u\) and \(v\), the estimated elevation is:

\(Z(u,v)=(1-u)(1-v)Z_{00}+u(1-v)Z_{10}+(1-u)vZ_{01}+uvZ_{11}\)

This provides a continuous approximation of terrain elevation and reduces artificial discontinuities associated with nearest-neighbour sampling.

No smoothing or void-filling procedure is currently applied.

### 5.3. Terrain Horizon Reconstruction

The local horizon is reconstructed using a numerical ray-marching algorithm.

From the observer position, the algorithm evaluates 720 azimuth directions covering 360 degrees.

The angular resolution is:

\(\Delta\alpha = 0.5^\circ\)

For each azimuth:

- Terrain is sampled along the corresponding direction.
- The maximum analysis distance is 70 kilometres.
- The sampling interval is 40 metres.
- Elevations are obtained through bilinear interpolation.
- The apparent elevation angle of each terrain sample is calculated.
- The maximum apparent elevation determines the local horizon.

The spherical curvature correction is approximated by:

\[\theta(d,\alpha)=\arctan\left(\frac{Z(d,\alpha)-Z_{\mathrm{observer}}}{d}\right)-\frac{d}{2R_{\mathrm{Moon}}}\]

Where:

- \(Z(d,\alpha)\) is the sampled terrain elevation.
- \(Z_{\mathrm{observer}}\) is observer elevation.
- \(d\) is horizontal distance.
- \(R_{\mathrm{Moon}}\) is the reference lunar radius.

The local horizon function is:

\[h_z(\alpha)=\max_d\theta(d,\alpha)\]

The resulting horizon profile describes the maximum terrain elevation angle in each azimuth direction.

This profile is subsequently used to determine whether the Sun and Earth are geometrically obstructed by surrounding terrain.

The curvature expression is an approximation and should not be interpreted as an exact spherical ray-intersection solution.

### 5.4. Astronomical Position Calculations

SOL uses NASA NAIF SPICE to calculate the apparent positions of the Sun and Earth relative to the selected lunar surface location.

The calculations use the DE440 planetary ephemeris and lunar orientation kernels.

The observer position is constructed using SPICE geometric reference-frame utilities.

The local coordinate system consists of:

- Up: Local radial direction.
- East: Local east direction.
- North: Local north direction.

Given a target position vector relative to the observer, the elevation angle is calculated as:

\[el=\arcsin\left(\frac{\vec v\cdot\hat u}{|\vec v|}\right)\]

The azimuth angle is:

\[az=\operatorname{atan2}(\vec v\cdot\hat e,\vec v\cdot\hat n)\pmod{360^\circ}\]

Where:

- \(\vec v\) is the target direction vector.
- \(\hat u\) is the local up vector.
- \(\hat e\) is the local east vector.
- \(\hat n\) is the local north vector.

The implementation uses SPICE spkpos calculations with light-time and stellar aberration correction (LT+S).

### 5.5. Solar Visibility

The Sun is represented as an extended optical disk rather than a point source.

Its adopted angular semi-diameter is:

\[R_{\odot}=0.267^\circ\]

The upper solar limb is considered visible when:

\[el_{\mathrm{Sun}}+R_{\odot}>h_z(az_{\mathrm{Sun}})\]

This provides a binary approximation of direct solar visibility.

The model does not calculate the precise fraction of the solar disk occulted by terrain.

It also does not currently model:

- Partial solar irradiance.
- Penumbra.
- Earthshine.
- Atmospheric effects.
### 5.6. Earth Visibility

Earth visibility is evaluated using its geometric center.

The visibility condition is:

\[el_{\mathrm{Earth}}>h_z(az_{\mathrm{Earth}})\]

When this condition is satisfied, the Earth center is geometrically above the local terrain horizon.

This calculation identifies potential direct-to-Earth line-of-sight opportunities.

Important distinction: Earth visibility is not equivalent to confirmed radio communication availability.

Actual communication also depends on antenna pointing, spacecraft hardware, ground-station visibility, link budgets, radio-frequency propagation, and operational constraints.

The current implementation evaluates geometric visibility rather than a complete telecommunications system.

---

## 🧠 6. Computational Architecture

SOL is organized into a modular architecture combining scientific processing, validation utilities, and web-based visualization.

### 6.1. Project Structure

```text
sol-final/
│
├── src/
│   └── process_lunar.py
│
├── tests/
│   ├── validate_jpl.py
│   └── compare_sites.py
│
├── training_modules/
│   └── [Scientific training modules and unit tests]
│
├── web/
│   ├── index.html
│   ├── app.js
│   ├── data_A.json
│   └── data_B.json
│
├── data/
│   ├── raw/
│   └── kernels/
│
├── archive/
│
├── requirements.txt
├── setup.ps1
├── abrir_site.bat
└── README.md
```

### 6.2. Backend Processing

The principal computational pipeline is implemented in Python.

It integrates:

- Raster data ingestion.
- Lunar coordinate transformations.
- Bilinear terrain interpolation.
- Topographic horizon reconstruction.
- SPICE astronomical calculations.
- Solar and Earth visibility evaluation.
- Statistical analysis.
- JSON data export.

The pipeline is designed to process individual candidate locations over configurable observation periods.

### 6.3. Frontend Visualization

The web interface provides an interactive environment for examining computed results.

Its principal components include:

- Dark-mode mission-control interface.
- Candidate site comparison.
- Lunar terrain visualization.
- Dynamic cartographic representations.
- Solar illumination statistics.
- Earth visibility statistics.
- Time-series analysis.

The interface consumes static JSON datasets generated by the scientific processing pipeline.

This separation allows the computational backend and visualization frontend to evolve independently.

---

## 🌕 7. Case Study: Lunar South Pole Candidate Sites

To demonstrate the platform's capabilities, two candidate locations were selected for comparative analysis.

The locations represent significantly different topographic environments.

### 7.1. Site A — Candidate Ridge Location

Coordinates:

| Parameter | Value |
| --- | --- |
| Latitude | 89.45°S |
| East longitude | 222.70° |
| Antenna mast height | 2 metres |

The selected location represents an elevated terrain environment near the lunar South Pole.

Its preliminary simulation indicates favorable direct solar visibility during the analyzed observation period.

### 7.2. Site B — Candidate Crater-Floor Location

Coordinates:

| Parameter | Value |
| --- | --- |
| Latitude | 89.90°S |
| East longitude | 129.20° |
| Antenna mast height | 2 metres |

The second location represents a deeply recessed terrain environment.

Its modeled horizon profile indicates substantial surrounding terrain obstruction.

The simulation identifies no direct solar or geometric Earth visibility during the analyzed period.

The candidate's precise geographic association with Shackleton Crater and its permanent-shadow classification require independent cartographic confirmation.

### 7.3. Comparative Results

Simulation configuration:

| Parameter | Configuration |
| --- | --- |
| Observation window | 30 days |
| Start date | 14 November 2026 UTC |
| Sampling interval | 30 minutes |
| Epoch count | 1,440 |
| Mast height | 2 metres |
| Terrain resolution | 20 metres |
| Horizon azimuth resolution | 0.5° |
| Maximum terrain range | 70 km |
| Terrain sampling interval | 40 metres |

Preliminary simulation results:

| Parameter | Site A | Site B |
| --- | --- | --- |
| Latitude | 89.45°S | 89.90°S |
| East longitude | 222.70° | 129.20° |
| Ground elevation above reference sphere | +1,955 m | -343 m |
| Observer elevation, including mast | +1,957 m | -341 m |
| Minimum horizon elevation | -2.85° | +4.41° |
| Maximum horizon elevation | +0.32° | +34.21° |
| Direct solar visibility | 100.0% | 0.0% |
| Geometric Earth visibility | 39.5% | 0.0% |
| Simultaneous Sun and Earth visibility | 39.5% | 0.0% |
| Longest interval without sunlight | 0.0 h | 720.0 h |
| Longest interval without Earth visibility | 341.5 h | 720.0 h |

These values are preliminary outputs from the current prototype and are not independently validated scientific conclusions.

### 7.4. Interpretation

Site A demonstrates favorable modeled illumination conditions during the selected 30-day window.

However, its Earth visibility is substantially lower than its solar visibility.

This illustrates an important mission-planning consideration: a location with continuous direct sunlight does not necessarily provide continuous communication opportunities with Earth.

Site B demonstrates the effect of surrounding terrain on both solar and Earth visibility.

Its high modeled horizon angles suggest significant topographic obstruction.

The comparison highlights the importance of considering illumination and communication geometry as separate mission-planning parameters.

Scientific caution: A 30-day simulation cannot establish permanent illumination conditions or permanent shadow classification. Longer simulations and independent topographic confirmation are required.

---

## 📊 8. Sensitivity Analysis

The prototype also supports investigations into the influence of antenna mast height and observation-window duration.

### 8.1. Antenna Mast Height

The following results illustrate the sensitivity of Site A to changes in observer height.

| Configuration | Solar visibility | Earth visibility |
| --- | --- | --- |
| 2 m mast | 100.0% | 39.5% |
| 5 m mast | 100.0% | 52.3% |
| 10 m mast | 100.0% | 57.6% |

Increasing observer height can improve geometric Earth visibility by allowing the observer to see above nearby terrain obstructions.

This demonstrates the importance of antenna placement and lander configuration in preliminary site assessment.

These results are geometric sensitivity experiments and do not represent verified antenna performance.

### 8.2. Observation-Window Duration

The 30-day and 365-day simulations produce different solar visibility statistics.

| Configuration | Solar visibility | Earth visibility |
| --- | --- | --- |
| Site A, 30 days, 2 m mast | 100.0% | 39.5% |
| Site A, 365 days, 2 m mast | 81.5% | 46.4% |
| Site B, 30 days, 2 m mast | 0.0% | 0.0% |
| Site B, 365 days, 2 m mast | 0.0% | 0.0% |

The Site A results demonstrate that continuous illumination during one observation window does not imply continuous illumination throughout the year.

Longer observation periods are therefore necessary when evaluating the suitability of locations for extended lunar surface operations.

---

## 📡 9. Scientific Outputs

The backend generates structured JSON datasets for the frontend dashboard.

Each dataset contains the following principal components.

### 9.1. Site Metadata

- Latitude.
- East longitude.
- Projected coordinates.
- Ground elevation.
- Observer elevation.
- Antenna mast height.

### 9.2. Statistical Metrics

- Solar visibility percentage.
- Geometric Earth visibility percentage.
- Simultaneous Sun and Earth visibility percentage.
- Longest continuous interval without direct sunlight.
- Longest continuous interval without geometric Earth visibility.

### 9.3. Horizon Profile

The horizon profile contains 720 azimuth samples covering 360 degrees.

Each sample represents the maximum apparent terrain elevation angle in its corresponding direction.

### 9.4. Astronomical Time Series

For each simulation epoch, the output contains:

- UTC timestamp.
- Solar azimuth and elevation.
- Earth azimuth and elevation.
- Local horizon elevation at the Sun's azimuth.
- Local horizon elevation at Earth's azimuth.
- Solar visibility flag.
- Earth visibility flag.

### 9.5. Terrain Preview

The exported terrain preview contains a decimated representation of the original LOLA elevation grid.

The current implementation uses every sixteenth DEM pixel, corresponding to approximately 320 metres between preview samples.

This preview is intended for visualization rather than high-resolution scientific reconstruction.

---

## 🧪 10. Validation and Testing

Scientific validation is an essential part of the development of SOL.

The project distinguishes between software verification, numerical testing, and independent scientific validation.

### 10.1. Automated Unit Tests

The `training_modules/` directory contains 14 automated unit tests covering synthetic terrain and geometric scenarios.

These tests evaluate computational behavior under controlled conditions, including:

- Flat terrain.
- Synthetic slopes.
- Geometric relationships.
- Horizon calculations.

The tests provide evidence of implementation consistency under the tested conditions.

They do not independently validate the real lunar DEM or the complete mission-environment predictions.

### 10.2. JPL Horizons Cross-Validation

The project includes `tests/validate_jpl.py`.

This script was developed to compare SOL-generated solar and Earth azimuth/elevation calculations with independent NASA JPL Horizons reference calculations.

The intended validation procedure includes:

- Selecting representative UTC epochs.
- Reconstructing the corresponding lunar observer location.
- Obtaining reference astronomical coordinates from JPL Horizons.
- Comparing calculated azimuth and elevation values.
- Evaluating angular discrepancies against predefined tolerances.

The validation script has been developed, but independent live-service validation results have not yet been established in the documented prototype release.

Therefore, no numerical accuracy claim is made for the JPL Horizons comparison.

### 10.3. Terrain Validation

The topographic horizon algorithm has been tested using synthetic terrain configurations.

An additional independent validation against NASA LOLA visibility products, particularly relevant GDRVIS products, is identified as a future verification step.

### 10.4. Validation Status

| Component | Current status |
| --- | --- |
| Synthetic terrain unit tests | Implemented; 14 tests reported passing |
| DEM ingestion | Implemented |
| Bilinear terrain interpolation | Implemented |
| Horizon reconstruction | Implemented |
| SPICE astronomical calculations | Implemented |
| JPL Horizons comparison | Script developed; independent results pending |
| Independent real-terrain horizon validation | Pending |
| Complete RF communication validation | Not implemented |

The project therefore remains a preliminary scientific prototype.

---

## ⚠️ 11. Assumptions and Limitations

The following limitations must be considered when interpreting SOL outputs.

### 11.1. Geographic Coverage

The current DEM covers the region from 87.5°S to the lunar South Pole.

Sites outside this coverage are not supported by the current processing configuration.

Terrain rays reaching the edge of the DEM are truncated, potentially underestimating the actual horizon.

### 11.2. Spatial Resolution

The 20-metre LOLA grid provides valuable regional topographic information.

However, smaller obstacles and narrow terrain features may not be represented adequately.

The 40-metre ray-marching interval can also skip features narrower than the sampling distance.

### 11.3. Local Terrain Geometry

The current observer vertical is defined using the reference spherical surface rather than the detailed local terrain normal.

This approximation may affect calculations on steep slopes.

### 11.4. Solar Disk Approximation

The Sun is represented by a fixed angular semi-diameter of 0.267°.

The current implementation does not calculate partial solar-disk occultation or actual solar-panel irradiance.

Binary visibility should not be interpreted as available electrical power.

### 11.5. Earth Disk Approximation

Earth is treated as a point source for geometric visibility calculations.

The actual apparent Earth disk is approximately 1.9° across as viewed from the Moon.

This approximation can influence visibility classification when Earth is close to a terrain horizon.

### 11.6. Communication Availability

Geometric Earth visibility does not guarantee an operational communication link.

The current implementation does not fully model:

- DSN ground-station visibility.
- Ground-station scheduling.
- Antenna pointing constraints.
- Lander antenna radiation patterns.
- Radio-frequency link budgets.
- Receiver noise and data-rate requirements.
- Operational power restrictions.

The reported Earth visibility percentages should therefore be interpreted as estimates of geometric line-of-sight opportunity.

### 11.7. Temporal Resolution

The default simulation uses a 30-minute sampling interval.

Shorter visibility transitions may occur between sampled epochs.

Consequently, the reported visibility intervals are temporally discretized approximations rather than continuous event solutions.

### 11.8. Observation Period

A 30-day simulation represents only a limited portion of the lunar illumination cycle.

Seasonal and longer-term environmental conclusions require extended simulations.

### 11.9. Coordinate Uncertainty

Azimuth becomes poorly conditioned close to the lunar South Pole.

The candidate coordinates and their geographical associations must also be independently confirmed against authoritative lunar cartographic references.

### 11.10. Environmental Models Not Yet Implemented

The current prototype does not implement:

- A complete GRAIL-derived selenoid correction.
- Forward-scattered dust twilight modelling.
- Operational RF communication simulation.

These remain potential extensions rather than validated capabilities of the current release.

---

## 💻 12. Installation and Reproducibility

SOL is designed to support reproducible scientific processing through locally stored planetary datasets and SPICE kernels.

### 12.1. Requirements

- Python 3.10 or later.
- Windows PowerShell or a compatible Python environment.
- Access to the LOLA elevation dataset.
- Required NASA NAIF SPICE kernels.
- Internet access for downloading dependencies and kernels.
### 12.2. Installation

Run the setup script:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

The setup script installs the required Python dependencies and retrieves the configured SPICE kernels.

### 12.3. Dataset Preparation

Download the following LOLA files:

```text
ldem_875s_20m.img
ldem_875s_20m.lbl
```

Place them inside:

```text
data/raw/
```

The raw DEM and SPICE kernels are not included in the repository because of their size and independent distribution.

### 12.4. Generate a Simulation

Example for a 30-day simulation:

```bash
python src/process_lunar.py \
    --lat -89.45 \
    --lon 222.7 \
    --days 30 \
    --output web/data_A.json
```

Example for a 365-day simulation:

```bash
python src/process_lunar.py \
    --lat -89.45 \
    --lon 222.7 \
    --days 365 \
    --step 1800 \
    --mast 2 \
    --output web/data_A_365d.json
```

### 12.5. Run Unit Tests

```bash
cd training_modules
python -m pytest
```

### 12.6. Open the Dashboard

Execute:

```text
abrir_site.bat
```

The local web interface is served at:

```text
http://localhost:8080
```

Reproducibility note: Exact numerical reproduction depends on the original DEM files, kernel versions, configuration parameters, software dependencies, coordinate conventions, and simulation timestamps.

---

## 🔭 13. Future Development

SOL is designed as a modular platform that can be extended as additional scientific datasets and computational capabilities become available.

### 13.1. Higher-Resolution Terrain Analysis

Potential developments include:

- Additional LOLA elevation products.
- Improved DEM coverage.
- Advanced terrain interpolation.
- Independent horizon validation.
- Local slope and surface-normal calculations.
### 13.2. Advanced Solar Energy Modelling

Potential developments include:

- Solar irradiance estimation.
- Solar-panel orientation.
- Panel efficiency and temperature effects.
- Battery charging and discharge models.
- Energy storage and operational scheduling.
### 13.3. Advanced Communication Modelling

Potential developments include:

- Extended Earth-disk occultation.
- Antenna orientation and pointing.
- RF link-budget calculations.
- DSN ground-station visibility.
- Communication-window optimization.
### 13.4. Expanded Astronomical Simulations

Potential developments include:

- Multi-year simulation windows.
- Higher temporal resolution.
- Additional lunar locations.
- Improved event-time calculations.
- Automated JPL Horizons validation.
### 13.5. Mission Planning Integration

Future versions could combine illumination, communication, energy, and terrain constraints into a unified mission-planning framework.

This would allow users to evaluate candidate locations according to different operational priorities and mission requirements.

---

## 👥 14. Team and Contributions

SOL was developed collaboratively by three Mozambican medical students from the Faculty of Medicine, Eduardo Mondlane University (UEM), Mozambique.

The project reflects an interdisciplinary approach to scientific innovation, combining computational methods, planetary science, engineering concepts, and scientific communication.

### Abudala Sualé

**Lunar Data Scientist & Computational Astrodynamics — Backend Lead**

**Principal responsibilities:**

- LOLA DEM ingestion and processing.
- Topographic horizon reconstruction.
- Bilinear terrain interpolation.
- Spherical curvature correction.
- NASA NAIF SPICE integration.
- Astronomical position calculations.
- Memory optimization.
- Scientific data export.

### Suneila dos Anjos

**Planetary Interface & Data Visualization Scientist — Frontend Lead**

**Principal responsibilities:**

- Interactive mission-control dashboard.
- User interface and experience design.
- Dark-mode interface development.
- Dynamic lunar cartographic visualization.
- Plotly-based data visualization.
- Frontend data integration.
- Responsive interface development.
- GitHub Pages deployment.

### Dionísio Pelembe

**Mission Science & Technical Communications Lead**

**Principal responsibilities:**

- Mission-planning problem formulation.
- Scientific documentation.
- Technical methodology organization.
- Comparative mission analysis.
- Scientific consistency review.
- Presentation and pitch development.
- Project communication and documentation.

All three team members contributed to the development and overall scientific direction of SOL.

---

## 🤖 15. Artificial Intelligence Assistance Disclosure

In accordance with the principles of transparency and responsible scientific communication, the team acknowledges the use of artificial intelligence tools during development.

The following tools were used as interactive coding, analytical, debugging, and editorial assistants:

- Google DeepMind Antigravity
- Plotlit
- OpenAI Codex
- GitHub Copilot Code
- Anthropic Claude
- DeepSeek

### Scope of AI Assistance

### Computational Refactoring

Support with NumPy vectorization, mathematical refactoring, and bilinear interpolation implementation.

### Memory Optimization

Assistance with raster processing strategies, including the use of raw 16-bit DEM buffers to reduce memory consumption.

### Software Testing

Assistance in structuring automated test cases, validation utilities, and sensitivity-analysis workflows.

### Debugging and Code Review

Assistance in reviewing code baselines, identifying implementation inconsistencies, and improving computational organization.

### Documentation and Communication

Support with technical writing, scientific documentation, presentation structure, and project communication.

### Human Responsibility

The team retained responsibility for project conception, scientific decisions, data selection, local execution, interpretation of results, and final technical decisions.

AI tools were used as development assistants and not as independent scientific authorities.

All scientific claims remain subject to the limitations and validation status documented in this README.

---

## 🌍 16. Credits and Acknowledgements

The team acknowledges the scientific and technical contributions of the following organizations and missions:

- NASA Lunar Reconnaissance Orbiter mission.
- NASA Lunar Orbiter Laser Altimeter science team.
- NASA Planetary Data System.
- NASA Navigation and Ancillary Information Facility.
- NASA Jet Propulsion Laboratory.
- NASA JPL Horizons.
- Arizona State University Lunar Reconnaissance Orbiter Camera team.

The project also relies on open-source scientific software and computational libraries, including:

- Python.
- NumPy.
- Rasterio.
- SpiceyPy.
- Astroquery.
- Plotly.js.
- Pytest.

All third-party datasets, kernels, libraries, and resources remain subject to their respective distribution terms and licenses.

---

## 🌕 17. Conclusion

SOL demonstrates how publicly available planetary science datasets, astronomical calculations, and computational terrain analysis can be integrated into a practical lunar environmental assessment platform.

By combining LOLA elevation data, NASA NAIF SPICE ephemerides, numerical horizon reconstruction, and astronomical visibility calculations, the project provides a framework for investigating two important constraints on lunar surface exploration:

Direct solar illumination and geometric Earth visibility.

The preliminary case study demonstrates that favorable solar illumination does not necessarily guarantee favorable communication geometry.

This distinction is particularly relevant to the assessment of candidate locations in the lunar South Pole region.

Although further validation and additional environmental modelling are necessary, SOL establishes a modular foundation for future research into lunar surface mission planning.

🇲🇿 Developed in Mozambique. Inspired by science. Designed for the future of lunar exploration.

**SOL Development Team**

- Abudala Sualé
- Dionísio Pelembe
- Suneila dos Anjos

**Faculty of Medicine**  
Eduardo Mondlane University  
Mozambique

**SOL — NASA Space Apps Challenge 2026**  
Scientific Prototype — Version 0.2

### Scientific and Operational Disclaimer

Scientific results presented in this repository are preliminary and have not been independently validated in their entirety.

SOL is an educational and research prototype. It is not an official NASA product, does not constitute an operational mission-planning system, and must not be used as the sole basis for real lunar mission decisions.

All environmental predictions should be interpreted within the assumptions, numerical approximations, and limitations documented in this repository.

Exploring the Moon begins with understanding its environment.
```

message.txt

34 KB
