# What changed from the submitted university notebook?

This public version is **a revision of the author's original advanced data
visualisation coursework on exoplanets**, not a claim that the data or plots
originate from a new independent astronomical survey.

### Preserved
- The original scientific question and luminosity-based filtering idea.
- The relative stellar-luminosity calculation from radius and temperature.
- The initial fixed flux limits (1.10 / 0.53 of Earth's irradiation).
- Stellar-category distribution, mass–temperature scatter, comparisons by
  category, Plotly treemap and Seaborn heatmap.

### Corrected
- Absolute `C:/Users/...` path replaced with a portable project-relative path.
- Catalogue's `Solar System`, `Controversial`, `Retracted planet candidate`,
  and `Kepler Objects of Interest` entries excluded from the principal sample;
  explicit `Confirmed planets` tag required.
- Original `True / False` habitability result replaced with a three-state
  geometric HZ membership classification: inside, outside, insufficient data.
- Plots renamed to avoid implying proof of habitability.
- Histograms / plots now distinguish the denominator of evaluable planets
  from the full confirmed sample.
- Stellar types labelled **approximate mass-based bins** rather than measured
  spectral classes.
- Repeated planets from the same sky position are not separately plotted as
  independent stars in the stellar mass / temperature scatterplot.
- Interactive treemap aggregated by category and classification rather than
  creating thousands of unreadable planet-name leaves.
- Reasoning about physical habitability and observational selection effects
  carefully separated from what the supplied catalogue actually demonstrates.
- Explicit raw data attribution and upstream licence notice added.
- Reusable functions, saved figures, validation tests and reproducible
  notebook added.

### Reference totals (this frozen snapshot)

| Scope | Total |
|---|---:|
| All source records | 5,414 |
| Original coursework geometric hits (all record types) | 76 |
| Confirmed exoplanet records | 5,288 |
| Evaluable confirmed records | 2,176 |
| Inside the simplified HZ, confirmed | 70 |
| Outside the simplified HZ, confirmed | 2,106 |
| Insufficient input data, confirmed | 3,112 |

**The 70 inside objects are not established to be habitable or Earth-like.**
