# Methodology and scientific scope

## Objective

Explore which objects in a **historical Open Exoplanet Catalogue snapshot** lie
within a **simplified, luminosity-scaled circumstellar habitable-zone interval**.
This is an educational screening exercise and a data-visualisation project;
**it does not identify proven habitable worlds**.

## 1. Sample definition and dataset quality

The snapshot has 5,414 records in its original CSV (25 source columns). The
catalogue has separate status tags in its `list` field, including confirmed
planets, controversial objects, retracted candidates and Solar System bodies.
We retain only objects whose comma-separated `list` tags include the exact tag
`Confirmed planets` for the principal exoplanet analysis:

- 5,288 confirmed exoplanet records.
- 2,176 have all three required positive, finite values: host-star radius,
  host-star temperature, and orbital semi-major axis.
- 3,112 have insufficient information to be evaluated by this model.
- Among the 2,176 evaluable records, 70 fall inside the chosen interval and
  2,106 outside.

The original coursework calculated 76 inside this interval across the **entire
catalogue**, including one Solar System body (Earth) and non-confirmed records.
The code preserves that historical comparison (`original_all_records_inside`),
while the primary results exclude these categories.

## 2. Relative stellar luminosity

We estimate the host star's bolometric luminosity using the Stefan–Boltzmann
relation, **with both stellar radius and stellar temperature**:

`L/L_sun = (R_star/R_sun)^2 * (T_star/5778 K)^4`

The source's `hoststar_radius` is measured in solar radii and
`hoststar_temperature` in Kelvin. We use 5778 K for the Sun's effective
temperature as in the original exercise.

## 3. Fixed-flux habitable-zone approximation

Preserving the original educational thresholds, the assumed irradiance limits
are 1.10 and 0.53 times Earth's incident stellar flux:

`HZ_inner (AU) = sqrt((L/L_sun) / 1.10)`

`HZ_outer (AU) = sqrt((L/L_sun) / 0.53)`

Equivalently, approximate stellar irradiance for a planet is:

`S/S_earth = (L/L_sun) / (a/AU)^2`

An **evaluable** planet is inside the model interval if
`HZ_inner <= semimajoraxis <= HZ_outer`, inclusive. A planet missing *any*
input stays in `Insufficient data`, rather than becoming a false negative.
The semi-major axis is used as a single proxy for distance; this ignores
orbital variation and can be misleading for highly eccentric planets.

These fixed limits intentionally match the coursework, **not** a fully
calibrated, temperature-dependent Kopparapu et al. habitable-zone model. Modern
radiative-convective limits depend on stellar effective temperature,
planetary mass, and atmospheric assumptions. Do not cite 1.10 and 0.53 as
universal physical constants or assert that every planet meeting them has
liquid water.

## 4. Stellar-mass categories are only proxies

The original project grouped host stars into O/B/A/F/G/K/M-style categories
from **mass alone**. This is a pedagogical approximation, **not a measured
spectral classification**. We preserve the original cutoffs for continuity:

| Mass (solar units) | Bin |
|---:|:---|
| > 16 | O |
| > 2.1 – 16 | B |
| > 1.4 – 2.1 | A |
| > 1.04 – 1.4 | F |
| > 0.8 – 1.04 | G |
| > 0.45 – 0.8 | K |
| >= 0.08 – 0.45 | M |
| Missing / < 0.08 | Unknown |

**Mass-based spectral bins must not be mistaken for actual stellar spectra.**
The mass–temperature scatter plot uses unique sky coordinate pairs as a
*proxy* for distinct host systems, because the flat file does not reliably
include host-star IDs. These are not guaranteed unique stars; the chart title
and caption disclose this limitation. Its axis choices preserve the original
student's astronomical convention (higher temperature on the left).

## 5. What the plots mean

- **Distribution:** number of *planet records* in each host-star mass bin, not
  the universal occurrence frequency of exoplanets around stellar types.
- **Status by mass bin:** three possible outcomes, including missing input.
- **Heatmap:** percentages by evaluable records in each bin, with raw numbers
  written inside cells; rows without evaluable records are blank.
- **Treemap:** an interactive breakdown of confirmed records by estimated
  stellar mass bin and HZ classification. It is aggregated for readability
  instead of plotting thousands of individually named planet leaves.
- **Scatter:** stellar mass vs temperature, one record per distinct sky
  coordinate, not one dot per planet.
- **Irradiance distribution and orbital plot:** geometric demonstration of
  the simplified fixed-flux cutoffs; no planetary climate simulation.

## 6. Essential limitations

1. **Within a zone is not proof of habitability.** Water, atmosphere,
   planetary size/composition, magnetic environment, stability and other
   features remain unknown or unused. Giant planets can also pass this filter.
2. **Selection effects:** transit and radial-velocity detections preferentially
   find some kinds of planets. This catalogue is neither a random survey nor a
   census of planetary occurrence rates.
3. **Missing data:** 3,112 confirmed exoplanets cannot be evaluated.
   Therefore, 70/2,176 = 3.22% describes only the *evaluable subset*.
4. **Binaries / multi-star systems:** flattening an OEC stellar system into
   a CSV can lose binary architecture. The simple single-star luminosity
   model can be inadequate for these systems.
5. **Eccentricity:** the semi-major axis alone does not provide instantaneous
   irradiation; high-eccentricity objects may spend significant time outside
   the interval.
6. **Catalogue age:** this is a snapshot with discoveries through 2023, not
   current information about confirmed planets in 2026.

## References and data provenance

- Open Exoplanet Catalogue tables:
  https://github.com/OpenExoplanetCatalogue/oec_tables
- Main catalogue field descriptions, units and binary-system caveat:
  https://github.com/OpenExoplanetCatalogue/open_exoplanet_catalogue
- Kopparapu et al. (2014), *Habitable Zones Around Main-sequence Stars:
  Dependence on Planetary Mass*, ApJ Letters 787, L29.
  https://doi.org/10.1088/2041-8205/787/2/L29
