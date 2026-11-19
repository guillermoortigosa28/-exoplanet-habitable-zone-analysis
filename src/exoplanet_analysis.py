"""Reproducible exoplanet catalogue and simplified habitable-zone analysis.

Originally conceived as a university data-visualisation project; this cleaned
version retains its mass-binned stellar plots, scatter plot, treemap, and heatmap.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
import pandas as pd
import plotly.express as px
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw' / 'open_exoplanet_catalogue.csv'
FIGURES = ROOT / 'figures'
PROCESSED = ROOT / 'data' / 'processed'

SUN_TEMPERATURE_K = 5778.0
INNER_FLUX_EARTH = 1.10
OUTER_FLUX_EARTH = 0.53
BIN_ORDER = ['O', 'B', 'A', 'F', 'G', 'K', 'M', 'Unknown']
STATUS_ORDER = ['Inside estimated HZ', 'Outside estimated HZ', 'Insufficient data']
STATUS_COLORS = {
    'Inside estimated HZ': '#148f77',
    'Outside estimated HZ': '#e19265',
    'Insufficient data': '#9aabc0',
}
BIN_COLORS = {
    'O': '#5685d6', 'B': '#6b9fe3', 'A': '#8fb4de', 'F': '#eabf77',
    'G': '#e6a652', 'K': '#da8f58', 'M': '#c76c5b', 'Unknown': '#8fa1b6',
}


def load_catalogue(path: str | Path = RAW) -> pd.DataFrame:
    """Read the supplied historic comma-separated OEC snapshot."""
    path = Path(path)
    frame = pd.read_csv(path)
    required = {'name', 'list', 'hoststar_mass', 'hoststar_radius',
                'hoststar_temperature', 'semimajoraxis', 'discoverymethod',
                'system_rightascension', 'system_declination'}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f'Missing expected columns: {sorted(missing)}')
    if frame['name'].duplicated().any():
        raise ValueError('Duplicate object names: inspect catalogue before analysing.')
    for col in ['hoststar_mass', 'hoststar_radius', 'hoststar_temperature',
                'semimajoraxis', 'eccentricity', 'mass', 'radius']:
        if col in frame:
            frame[col] = pd.to_numeric(frame[col], errors='coerce')
    return frame


def mass_bin(mass: float) -> str:
    """Approximate class from stellar mass; NOT an observed spectral class."""
    if pd.isna(mass) or mass < 0.08:
        return 'Unknown'
    if mass > 16:
        return 'O'
    if mass > 2.1:
        return 'B'
    if mass > 1.4:
        return 'A'
    if mass > 1.04:
        return 'F'
    if mass > 0.8:
        return 'G'
    if mass > 0.45:
        return 'K'
    return 'M'


def is_confirmed(value: object) -> bool:
    """Check exact catalogue tag, excluding controversial/KOI/solar records."""
    if pd.isna(value):
        return False
    return 'Confirmed planets' in {tag.strip() for tag in str(value).split(',')}


def analyse_catalogue(catalogue: pd.DataFrame) -> pd.DataFrame:
    """Derive relative luminosity, approximate HZ boundaries and 3-state label.

    Validity depends on *positive, finite* radius, temperature, and semi-major
    axis. Never silently interpret missing parameter values as outside the HZ.
    """
    frame = catalogue.copy()
    frame['is_confirmed'] = frame['list'].map(is_confirmed)
    frame['stellar_mass_bin'] = frame['hoststar_mass'].map(mass_bin)
    needed = ['hoststar_radius', 'hoststar_temperature', 'semimajoraxis']
    valid = frame[needed].notna().all(axis=1)
    valid &= np.isfinite(frame[needed]).all(axis=1)
    valid &= frame[needed].gt(0).all(axis=1)

    radius = frame['hoststar_radius'].where(frame['hoststar_radius'] > 0)
    temperature = frame['hoststar_temperature'].where(frame['hoststar_temperature'] > 0)
    axis = frame['semimajoraxis'].where(frame['semimajoraxis'] > 0)
    frame['stellar_luminosity_solar'] = radius**2 * (temperature / SUN_TEMPERATURE_K)**4
    frame['hz_inner_au'] = np.sqrt(frame['stellar_luminosity_solar'] / INNER_FLUX_EARTH)
    frame['hz_outer_au'] = np.sqrt(frame['stellar_luminosity_solar'] / OUTER_FLUX_EARTH)
    frame['incident_flux_earth'] = frame['stellar_luminosity_solar'] / (axis**2)

    # All catalogue records are labelled for transparency; only confirmed
    # exoplanets enter the primary inference.
    inside = (valid & axis.ge(frame['hz_inner_au'])
              & axis.le(frame['hz_outer_au']))
    frame['hz_status'] = 'Insufficient data'
    frame.loc[valid, 'hz_status'] = 'Outside estimated HZ'
    frame.loc[inside, 'hz_status'] = 'Inside estimated HZ'
    frame['hz_status'] = pd.Categorical(frame['hz_status'],
                                        categories=STATUS_ORDER, ordered=True)
    frame['can_evaluate'] = valid
    return frame


def confirmed_only(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.loc[frame['is_confirmed']].copy()


def summary_counts(frame: pd.DataFrame) -> dict[str, int]:
    valid = frame.loc[frame['is_confirmed']]
    by = valid['hz_status'].value_counts()
    return {
        'catalogue_records': len(frame),
        'confirmed_exoplanets': len(valid),
        'evaluable': int(valid['can_evaluate'].sum()),
        'inside': int(by.get('Inside estimated HZ', 0)),
        'outside': int(by.get('Outside estimated HZ', 0)),
        'insufficient': int(by.get('Insufficient data', 0)),
        'original_all_records_inside': int((frame['hz_status'] == 'Inside estimated HZ').sum()),
    }


def make_tables(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    selected = confirmed_only(frame)
    summary = (selected.groupby(['stellar_mass_bin', 'hz_status'], observed=False)
               .size().unstack('hz_status', fill_value=0)
               .reindex(BIN_ORDER, fill_value=0)
               .reindex(columns=STATUS_ORDER, fill_value=0))
    summary.index.name = 'stellar_mass_bin'
    candidates = selected.loc[selected['hz_status'] == 'Inside estimated HZ',
        ['name', 'stellar_mass_bin', 'hoststar_mass', 'hoststar_radius',
         'hoststar_temperature', 'semimajoraxis', 'stellar_luminosity_solar',
         'hz_inner_au', 'hz_outer_au', 'incident_flux_earth', 'eccentricity',
         'mass', 'radius', 'discoverymethod']].copy()
    candidates = candidates.sort_values('incident_flux_earth')
    return summary, candidates


def _style():
    sns.set_theme(style='whitegrid', context='notebook', font_scale=1.0)
    plt.rcParams.update({
        'font.family': 'DejaVu Sans', 'figure.facecolor': '#ffffff',
        'axes.facecolor': '#ffffff', 'axes.spines.top': False,
        'axes.spines.right': False, 'axes.titleweight': 'bold',
        'axes.titlesize': 14, 'axes.labelcolor': '#334155',
        'grid.alpha': .23, 'savefig.facecolor': 'white',
    })


def _save(fig: plt.Figure, filename: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / filename, dpi=170, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def plot_mass_distribution(selected: pd.DataFrame):
    counts = selected['stellar_mass_bin'].value_counts().reindex(BIN_ORDER, fill_value=0)
    fig, ax = plt.subplots(figsize=(9.5, 5))
    bars = ax.bar(counts.index, counts.values, color=[BIN_COLORS[x] for x in BIN_ORDER])
    ax.bar_label(bars, padding=3, fontsize=9)
    ax.set(title='Confirmed exoplanets by host-star mass bin',
           xlabel='Approximate mass-based bin (NOT observed spectral type)',
           ylabel='Number of planet records')
    ax.set_ylim(0, counts.max()*1.15)
    _save(fig, '01_stellar_mass_bins.png')


def _deduplicate_hosts(selected: pd.DataFrame) -> pd.DataFrame:
    subset = selected.loc[
        selected['hoststar_mass'].between(.1, 2.5, inclusive='neither')
        & selected['hoststar_temperature'].between(3000, 7500, inclusive='neither')
    ].copy()
    # Source lists planets, not host stars: a reliable stellar key is not
    # provided. Sky coordinates are used as a PROXY for host-system identity.
    has_coord = (subset['system_rightascension'].notna()
                 & subset['system_declination'].notna())
    subset['host_system_proxy'] = np.where(
        has_coord,
        subset['system_rightascension'].astype(str) + ' / ' + subset['system_declination'].astype(str),
        'unique-name:' + subset['name'].astype(str),
    )
    return subset.drop_duplicates('host_system_proxy')


def plot_stellar_scatter(selected: pd.DataFrame):
    hosts = _deduplicate_hosts(selected)
    fig, ax = plt.subplots(figsize=(9,5.6))
    ax.scatter(hosts['hoststar_temperature'], hosts['hoststar_mass'], s=11,
               c='#4387b5', alpha=.45, linewidths=0)
    ax.set_yscale('log')
    ax.invert_xaxis()
    ax.set(title='Stellar mass vs temperature · host-system proxies',
           xlabel='Effective stellar temperature (K) · hotter to the left',
           ylabel='Host-star mass (solar masses, log scale)')
    ax.text(.01, .02, f'{len(hosts):,} coordinate-unique host-system proxies; 0.1–2.5 M☉ / 3000–7500 K',
            transform=ax.transAxes, fontsize=8.5, color='#64748b')
    _save(fig,'02_stellar_scatter.png')


def plot_hz_status(summary: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10.7, 5.5))
    bottom = np.zeros(len(summary))
    for status in STATUS_ORDER:
        values = summary[status].to_numpy()
        ax.bar(summary.index, values, bottom=bottom, color=STATUS_COLORS[status],
               label=status, edgecolor='white', linewidth=.4)
        bottom += values
    ax.set(title='Confirmed exoplanets · estimated HZ status by stellar mass bin',
           xlabel='Approximate stellar mass bin', ylabel='Number of planet records')
    ax.legend(loc='upper right', bbox_to_anchor=(1.0,1.0),frameon=True, fontsize=9)
    _save(fig,'03_hz_status_by_mass_bin.png')


def plot_hz_heatmap(summary: pd.DataFrame):
    evaluable = summary[STATUS_ORDER[:2]].sum(axis=1)
    percentage = (100 * summary[STATUS_ORDER[:2]].div(evaluable.replace(0,np.nan),axis=0))
    percentage = percentage.replace([np.inf,-np.inf], np.nan)
    fig,ax=plt.subplots(figsize=(8.6, 5.3))
    sns.heatmap(percentage, cmap='YlGnBu', vmin=0,vmax=100,
                annot=summary[STATUS_ORDER[:2]].astype(str),fmt='',
                linewidths=.6,linecolor='white',cbar_kws={'label':'Percentage within evaluable mass-bin records'},ax=ax)
    ax.set(title='Estimated HZ status by host-star mass bin',
           xlabel='Classification · cell labels are absolute planet counts', ylabel='Approximate stellar mass bin')
    ax.set_xticklabels(['Inside HZ','Outside HZ'], rotation=0)
    _save(fig,'04_hz_heatmap.png')


def plot_insolation(selected: pd.DataFrame):
    valid = selected[selected['can_evaluate']].copy()
    flux = valid['incident_flux_earth']
    finite = flux[np.isfinite(flux) & (flux>0)]
    fig,ax=plt.subplots(figsize=(9.5,5))
    lower=max(float(finite.quantile(.002)), 1e-4)
    upper=min(float(finite.quantile(.99)), 1e5)
    ax.hist(finite.clip(lower=lower,upper=upper), bins=np.logspace(np.log10(lower),np.log10(upper),54),
            color='#5986aa', alpha=.85)
    ax.axvspan(OUTER_FLUX_EARTH,INNER_FLUX_EARTH,alpha=.24,color='#34b69c',label='Simplified HZ flux band')
    ax.axvline(OUTER_FLUX_EARTH,color='#148f77',linestyle='--',lw=1.4)
    ax.axvline(INNER_FLUX_EARTH,color='#148f77',linestyle='--',lw=1.4)
    ax.set_xscale('log')
    ax.set(title='Incident stellar flux across evaluable confirmed exoplanets',
           xlabel='Incident flux relative to Earth (log scale)',ylabel='Number of exoplanets')
    ax.legend(loc='upper left')
    ax.text(.99,.97,'Extreme values clipped to display range\n(not removed from the analysis)',
            ha='right',va='top',transform=ax.transAxes,fontsize=8.5,color='#64748b')
    _save(fig,'05_incident_flux_distribution.png')


def plot_orbit_hz(selected: pd.DataFrame):
    valid = selected.loc[selected['can_evaluate']].copy()
    x=valid['stellar_luminosity_solar']
    y=valid['semimajoraxis']
    good=np.isfinite(x)&np.isfinite(y)&x.gt(0)&y.gt(0)
    valid=valid.loc[good]
    lo=max(1e-4,float(valid['stellar_luminosity_solar'].quantile(.002)))
    hi=min(1e4,float(valid['stellar_luminosity_solar'].quantile(.998)))
    xx=np.logspace(np.log10(lo),np.log10(hi),200)
    fig,ax=plt.subplots(figsize=(9.5,6.0))
    ax.fill_between(xx,np.sqrt(xx/INNER_FLUX_EARTH),np.sqrt(xx/OUTER_FLUX_EARTH),
                    color='#b5e9d8',alpha=.7,label='Simplified HZ')
    outside=valid[valid.hz_status == 'Outside estimated HZ']
    inside=valid[valid.hz_status == 'Inside estimated HZ']
    ax.scatter(outside['stellar_luminosity_solar'],outside['semimajoraxis'],
               s=9,alpha=.24,color='#b66c49',label='Outside HZ',rasterized=True)
    ax.scatter(inside['stellar_luminosity_solar'],inside['semimajoraxis'],
               s=38,alpha=.9,edgecolor='white',linewidth=.4,color='#148f77',label='Inside HZ')
    ax.set_xscale('log');ax.set_yscale('log')
    ax.set_xlim(lo,hi)
    ax.set_ylim(.003,1e4)
    ax.set(title='Orbits and simplified habitable-zone boundaries',
           xlabel='Host-star luminosity (solar units, log scale)',
           ylabel='Orbital semi-major axis (AU, log scale)')
    ax.legend(loc='lower right',frameon=True,fontsize=9)
    _save(fig,'06_orbital_distance_vs_luminosity.png')


def plot_detection_methods(selected: pd.DataFrame):
    valid = selected[selected['can_evaluate']]
    methods=(valid.assign(discoverymethod=valid['discoverymethod'].fillna('Unknown'))
             .groupby(['discoverymethod', 'hz_status'],observed=False)
             .size().unstack(fill_value=0))
    methods=methods.sort_values(STATUS_ORDER[1],ascending=False).head(6)
    fig,ax=plt.subplots(figsize=(9,5))
    bottom=np.zeros(len(methods))
    for status in STATUS_ORDER[:2]:
        val=methods[status].values
        ax.barh(methods.index,val,left=bottom,color=STATUS_COLORS[status],label=status)
        bottom += val
    ax.invert_yaxis()
    ax.set(title='Observational mix: detection methods among evaluable records',
           xlabel='Number of confirmed exoplanets',ylabel='Detection method')
    ax.legend(fontsize=8)
    _save(fig,'07_discovery_methods.png')


def plot_treemap_preview(summary: pd.DataFrame):
    # Static preview for GitHub; interactive official treemap is written below.
    # Segment size proportional to all confirmed records in that mass bin.
    totals=summary.sum(axis=1)
    fig,ax=plt.subplots(figsize=(10.5,5.1))
    from matplotlib.patches import Rectangle
    total=totals.sum()
    y=0
    # One horizontal band per mass bin, with 3 status segments
    for mass_bin in BIN_ORDER:
        row=summary.loc[mass_bin]
        if totals[mass_bin]==0:continue
        h=float(totals[mass_bin])/total
        x=0
        for status in STATUS_ORDER:
            value=row[status]
            w=value/totals[mass_bin]
            ax.add_patch(Rectangle((x,y),w,h,facecolor=STATUS_COLORS[status],edgecolor='white',lw=1))
            if w>.06 and h>.04:
                ax.text(x+w/2,y+h/2,f'{value}',ha='center',va='center',fontsize=9,fontweight='bold',color='#102a36')
            x+=w
        ax.text(-.02,y+h/2,mass_bin,ha='right',va='center',fontweight='bold',fontsize=10)
        y+=h
    ax.set(xlim=(-.07,1.01),ylim=(0,1),title='Hierarchical breakdown · mass bin × HZ status')
    ax.set_yticks([])
    ax.set_xlabel('Fraction of each stellar mass bin (each row height = share of records)')
    ax.xaxis.set_ticks([0,.25,.5,.75,1.0])
    ax.set_xticklabels(['0%','25%','50%','75%','100%'])
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=STATUS_COLORS[s],label=s) for s in STATUS_ORDER],
              bbox_to_anchor=(.5,-.14),loc='upper center',ncol=3,frameon=False,fontsize=8)
    _save(fig,'08_treemap_static_preview.png')


def make_interactive(selected: pd.DataFrame,summary: pd.DataFrame):
    FIGURES.mkdir(parents=True,exist_ok=True)
    table=(summary.stack().reset_index(name='planets')
           .rename(columns={'hz_status':'classification'}))
    table=table[table.planets>0]
    fig=px.treemap(table,path=[px.Constant('Confirmed exoplanets'),'stellar_mass_bin','classification'],
                   values='planets',color='classification',color_discrete_map=STATUS_COLORS,
                   title='Confirmed exoplanets by stellar mass bin and simplified HZ status')
    fig.update_traces(root_color='#edf2f7',textinfo='label+value+percent parent')
    fig.update_layout(margin=dict(t=60,b=10,l=10,r=10),font_family='Arial')
    fig.write_html(FIGURES/'interactive_treemap.html',include_plotlyjs=True,full_html=True)
    hosts=_deduplicate_hosts(selected)
    fig2=px.scatter(hosts,x='hoststar_temperature',y='hoststar_mass',
                    hover_name='name',color='stellar_mass_bin',
                    category_orders={'stellar_mass_bin':BIN_ORDER},color_discrete_map=BIN_COLORS,
                    labels={'hoststar_temperature':'Effective temperature (K)',
                            'hoststar_mass':'Host-star mass (solar units)'},
                    title='Mass and temperature — coordinate-unique host-system proxies',
                    log_y=True, opacity=.65)
    fig2.update_xaxes(autorange='reversed')
    fig2.write_html(FIGURES/'interactive_stellar_scatter.html',include_plotlyjs=True,full_html=True)


def write_outputs(frame: pd.DataFrame):
    _style()
    selected = confirmed_only(frame)
    summary,candidates=make_tables(frame)
    PROCESSED.mkdir(parents=True,exist_ok=True)
    FIGURES.mkdir(parents=True,exist_ok=True)
    summary.to_csv(PROCESSED/'hz_status_by_stellar_mass_bin.csv')
    candidates.to_csv(PROCESSED/'confirmed_inside_estimated_hz.csv', index=False)
    plot_mass_distribution(selected)
    plot_stellar_scatter(selected)
    plot_hz_status(summary)
    plot_hz_heatmap(summary)
    plot_insolation(selected)
    plot_orbit_hz(selected)
    plot_detection_methods(selected)
    plot_treemap_preview(summary)
    make_interactive(selected,summary)
    return summary,candidates


def main() -> None:
    parser=argparse.ArgumentParser(description='Run exoplanet HZ exploratory analysis')
    parser.add_argument('--data',type=Path,default=RAW)
    args=parser.parse_args()
    all_records=analyse_catalogue(load_catalogue(args.data))
    counts=summary_counts(all_records)
    write_outputs(all_records)
    print('Snapshot results (fixed irradiance thresholds):')
    for k,v in counts.items():
        print(f'  {k}: {v}')
    print(f'Generated outputs in {FIGURES} and {PROCESSED}')


if __name__ == '__main__':
    main()
