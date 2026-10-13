# PowerCAT / ORDANOVA

**Research preview v0.5.0 — statistical validation in progress.**

A Python desktop implementation for nominal and ordinal analysis of variance (CATANOVA / ORDANOVA), with interactive PDF/CDF plots and experiment-design review before analysis.

> **Important:** Monte Carlo p-values, critical values and power calculations have **not** been fully validated against the original Excel/VBA versions. Do not treat current numerical inference as certified or use it for consequential decisions without independent verification. This is a public source-code preview, **not** a validated scientific release.

## Research publications

The software is associated with these methodological publications; see them for scientific context and proper attribution:

1. **Gadrich, T., Marmor, Y. N. (2021).** Two-way ORDANOVA: Analyzing ordinal variation in a cross-balanced design. *Journal of Statistical Planning and Inference*, **215**, 330–343. https://doi.org/10.1016/j.jspi.2021.04.005
2. **Gadrich, T., Marmor, Y. N., Pennecchi, F. R., Hibbert, D. B., Semenova, A. A., Kuselman, I. (2024).** Power of a test for assessing interlaboratory consensus of nominal and ordinal characteristics of a substance, material, or object. *Metrologia*, **61**, 045004. https://doi.org/10.1088/1681-7575/ad5846

These are citations to papers, **not** a claim that this Python implementation has been validated by those papers.

## Get started (Python 3.10+)

Clone or download the repository, open a terminal in its root directory, then run:

```bash
python -m pip install -e .
python run_app.py
```

For development and tests:

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
```

On Windows, the executable can be built locally using `build_exe.bat` or remotely using **Actions → Build Windows preview → Run workflow**. The workflow-created EXE is a downloadable **Actions artifact**, not an official stable release.

## Supported workflows

- One-way and balanced two-way frequency-table inputs (examples under `examples/`).
- Nominal or ordinal mode selection.
- Pre-analysis experiment-design summary, user confirmation, and input validation.
- Observed decomposition including A×B interaction for supported replicated two-way designs.
- Interactive PDF/CDF charts, empirical histograms, optional boundary-corrected smoothed curves, image export.

## Known limitations

- **Monte Carlo inferential outputs remain under VBA parity investigation.**
- One-way simulation is a preliminary implementation.
- Unbalanced two-way designs are not supported.
- The Python design-review UI follows the original VBA concept but is not guaranteed to reproduce every original rule/dialogue exactly.
- Not all original Excel/VBA functionalities have been independently verified.

## Repository layout

- `src/powercatordanova/` — application and numerical code
- `run_app.py` — GUI launcher
- `examples/` — research example input files
- `tests/` — regression and structural checks
- `.github/workflows/` — CI tests and on-demand Windows EXE build
- `CITATION.cff` — GitHub citation metadata for the Python software

## Cite

Use GitHub's **Cite this repository** feature to cite this software preview. Cite the relevant methodology paper(s) above when using CATANOVA / ORDANOVA academically. **No software DOI has been issued yet.**

## License

MIT (see `LICENSE`). Original VBA workbooks are not included in this repository pending separate provenance and licensing review.
