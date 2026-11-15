# LunarOps — Lunar South Pole Mission Dashboard

Interactive scientific visualization project for exploring lunar South Pole terrain, solar illumination, and geometric Earth visibility.

## Project contents

- **Angular dashboard** at the repository root, including the interactive Three.js lunar viewer and precomputed datasets in `public/data/`.
- **SOL scientific pipeline and documentation** in [`SOL-FINAL (NOV 2026)/`](SOL-FINAL%20(NOV%202026)/README.md).
- **Project overview and methodology** in [`README_SOL_Organized.md`](README_SOL_Organized.md).
- **Validation status** in [`VALIDATION_STATUS.md`](VALIDATION_STATUS.md).

## Run the dashboard

Requirements: Node.js and npm compatible with the versions in `package.json`.

```bash
npm ci
npm start
```

Open the local URL printed by Angular CLI (normally `http://localhost:4200/`). The dashboard reads its precomputed datasets from `public/data/` and the lunar model from `public/models/`.

## Build and tests

```bash
npm run build
npm test
```

The Python scientific pipeline, its dependencies, data preparation, and test instructions are documented in the SOL project README linked above. The raw LOLA DEM and SPICE kernels are external inputs and are not included in this repository.

## Scientific status

Validation of the current project version has been completed. The results are validated for the documented data, methods, assumptions, and simulation configurations. See [`VALIDATION_STATUS.md`](VALIDATION_STATUS.md) and the SOL documentation for scope and interpretation. Validation does not make this research and decision-support project a flight-certified or operational NASA system, and geometric Earth visibility is not a guarantee of radio communication.

## License and data acknowledgements

See the repository's Apache License 2.0 file and the SOL documentation's credits and data-source notes. NASA and third-party datasets, libraries, and assets remain subject to their respective terms and attribution requirements.
