# Validation report

The project was tested against the **bundled historical catalogue snapshot**, not a live feed.

## Execution checks

- Python **3.13.5** was used for the validation run.
- Notebook `notebooks/Exoplanet_Habitable_Zone_Analysis.ipynb`: all **12 code cells** executed successfully using a clean kernel with working directory set to the **repository root**.
- Same notebook: all **12 code cells** executed successfully using a clean kernel with working directory set to **`notebooks/`**.
- All **6 regression/edge-case tests** passed with `python -m pytest -q`.
- Script `python src/exoplanet_analysis.py` executed successfully and regenerated the PNGs, interactive offline Plotly HTML files, and processed CSVs.
- No external download, credential, or personal `C:` path is required.

## Snapshot assertions

| Assertion | Expected result |
|---|---:|
| Source records | 5,414 |
| Confirmed exoplanets | 5,288 |
| Confirmed with complete positive finite input | 2,176 |
| Inside the simplified geometric zone | 70 |
| Outside the simplified geometric zone | 2,106 |
| Missing/invalid required input | 3,112 |
| Original unfiltered all-status geometric hits | 76 |

The filters **do not verify habitability**; results depend on educational fixed irradiance thresholds and this specific dated catalogue snapshot.

## How to repeat the checks

From the root of this repository:

```bash
pip install -r requirements.txt
python -m pytest -q
python src/exoplanet_analysis.py
```

Open the Jupyter notebook and run **Kernel → Restart & Run All**. The notebook regenerates the charts; its saved outputs are already embedded for browsing on GitHub.
