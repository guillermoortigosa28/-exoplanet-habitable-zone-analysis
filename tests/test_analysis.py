"""Data-specific regression and synthetic edge-case tests."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from exoplanet_analysis import (  # noqa: E402
    analyse_catalogue, confirmed_only, is_confirmed,
    load_catalogue, make_tables, mass_bin, summary_counts,
)


def test_confirmed_tag_excludes_other_categories():
    assert is_confirmed('Confirmed planets')
    assert is_confirmed('Confirmed planets, Planets in binary systems, S-type')
    assert not is_confirmed('Retracted planet candidate')
    assert not is_confirmed('Controversial')
    assert not is_confirmed('Solar System')
    assert not is_confirmed('Unconfirmed planets')


def test_mass_binning_is_approximate_and_complete():
    assert mass_bin(1.0) == 'G'
    assert mass_bin(.3) == 'M'
    assert mass_bin(1.42) == 'A'
    assert mass_bin(np.nan) == 'Unknown'
    assert mass_bin(.02) == 'Unknown'


def test_one_au_solar_radius_and_temp_is_inside():
    sample = pd.DataFrame({
        'name': ['test-earthlike', 'missing', 'close-in', 'withdrawn'],
        'list': ['Confirmed planets', 'Confirmed planets', 'Confirmed planets',
                 'Retracted planet candidate'],
        'hoststar_mass': [1.0]*4,
        'hoststar_radius': [1.0]*4,
        'hoststar_temperature': [5778.0]*4,
        'semimajoraxis': [1.0, np.nan, .2, 1.0],
    })
    enriched = analyse_catalogue(sample)
    assert enriched.iloc[0]['hz_status'] == 'Inside estimated HZ'
    assert np.isclose(enriched.iloc[0]['stellar_luminosity_solar'], 1.0)
    assert enriched.iloc[1]['hz_status'] == 'Insufficient data'
    assert enriched.iloc[2]['hz_status'] == 'Outside estimated HZ'
    assert not enriched.iloc[3]['is_confirmed']


def test_nonpositive_fields_do_not_count_as_evaluable():
    sample = pd.DataFrame({
        'name': ['bad-temperature', 'bad-radius', 'bad-axis'],
        'list': ['Confirmed planets']*3,
        'hoststar_mass': [1.0]*3,
        'hoststar_radius': [1.0, 0, 1.0],
        'hoststar_temperature': [0.0, 5778, 5778],
        'semimajoraxis': [1.0, 1.0, 0],
    })
    analysed=analyse_catalogue(sample)
    assert not analysed['can_evaluate'].any()
    assert (analysed['hz_status']=='Insufficient data').all()


def test_original_snapshot_numbers_are_reproducible():
    source=load_catalogue()
    enriched=analyse_catalogue(source)
    counts=summary_counts(enriched)
    assert counts == {
        'catalogue_records': 5414,
        'confirmed_exoplanets': 5288,
        'evaluable': 2176,
        'inside': 70,
        'outside': 2106,
        'insufficient': 3112,
        'original_all_records_inside': 76,
    }
    summary,candidates=make_tables(enriched)
    assert summary.to_numpy().sum()==5288
    assert len(candidates)==70
    assert candidates['name'].is_unique
    assert (candidates['incident_flux_earth'].between(.53, 1.1)).all()


def test_confirmed_only_has_no_solar_system_entries():
    enriched=analyse_catalogue(load_catalogue())
    confirmed=confirmed_only(enriched)
    assert 'Earth' not in set(confirmed['name'])
    assert 'Gliese 581 g' not in set(confirmed['name'])
