# PowerCAT / ORDANOVA

## Download for Windows

**[Download PowerCAT / ORDANOVA v0.5.0 — Windows EXE](https://github.com/YarivMarmor/PowerCAT-ORDANOVA/releases/download/v0.5.0-preview/PowerCAT_ORDANOVA.exe)**

Standalone Windows application. No Python or Jupyter installation required.

**Research preview v0.5.0 — statistical validation in progress.**

**Research Preview:** Statistical validation against the original Excel/VBA implementations is still in progress.


A Python desktop implementation for nominal and ordinal analysis of variance (CATANOVA / ORDANOVA), with interactive PDF/CDF plots and experiment-design review before analysis.

> **Important:** Monte Carlo p-values, critical values and power calculations have **not** been fully validated against the original Excel/VBA versions. Do not treat current numerical inference as certified or use it for consequential decisions without independent verification. This is a public source-code preview, **not** a validated scientific release.

## Research publications

The software is associated with these methodological publications; see them for scientific context and proper attribution:

1. **Gadrich, T., Marmor, Y. N. (2021).** Two-way ORDANOVA: Analyzing ordinal variation in a cross-balanced design. *Journal of Statistical Planning and Inference*, **215**, 330–343. https://doi.org/10.1016/j.jspi.2021.04.005
2. **Gadrich, T., Marmor, Y. N., Pennecchi, F. R., Hibbert, D. B., Semenova, A. A., Kuselman, I. (2024).** Power of a test for assessing interlaboratory consensus of nominal and ordinal characteristics of a substance, material, or object. *Metrologia*, **61**, 045004. https://doi.org/10.1088/1681-7575/ad5846

These are citations to papers, **not** a claim that this Python implementation has been validated by those papers.

## Windows installation and security notice

1. Download `PowerCAT_ORDANOVA.exe` from the official GitHub Release.
2. Save the file to a folder on your computer.
3. Run the application by double-clicking the EXE.

### First-time launch: Windows SmartScreen

The Windows executable is currently distributed without a digital code-signing certificate.

As a result, Windows may display an "Unknown publisher" or "Windows protected your PC" warning when launching the application for the first time.

If you downloaded the file from this official repository, have verified that it is the expected executable, and your organization's security policy permits it, you may select **More info > Run anyway**, if this option is available.

You can also scan the file with Windows Security or your antivirus software before running it.

Do not disable Windows Defender, SmartScreen, or other system-wide security protections.

**Note:** An unsigned executable is not necessarily unsafe, but the absence of a digital signature means that Windows cannot verify its publisher.

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
