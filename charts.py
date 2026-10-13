"""Presentation-only plotting. None of these options affect statistical results."""
import numpy as np
from matplotlib.figure import Figure
from scipy.ndimage import gaussian_filter1d

COLORS = {'A': 'tab:red', 'B': '#262626', 'AB': 'tab:blue'}


def fd_edges(values, max_bins=2500):
    """Robust Freedman-Diaconis edges with fallback for discrete/degenerate data."""
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if not values.size:
        raise ValueError('No finite simulation values')
    lo, hi = float(values.min()), float(values.max())
    if hi == lo:
        return np.array([lo - .5, hi + .5])
    q25, q75 = np.percentile(values, [25, 75]); iqr = q75 - q25
    if iqr > 0:
        width = 2.0 * iqr / np.cbrt(values.size)
        count = int(np.ceil((hi - lo) / width))
    else:
        count = int(np.ceil(np.sqrt(values.size)))
    count = max(1, min(max_bins, count))
    return np.linspace(lo, hi, count + 1)


def chart_bounds(distributions, display_range='99.5'):
    """Compute shared x-axis limits from *all selected* distributions."""
    values = [np.asarray(v)[np.isfinite(v)] for v in distributions if len(v)]
    if not values:
        return None
    if display_range == 'full':
        lo = min(float(v.min()) for v in values)
        hi = max(float(v.max()) for v in values)
    else:
        mass = float(display_range) / 100
        lower, upper = (1-mass)/2, (1+mass)/2
        lo = min(float(np.quantile(v, lower)) for v in values)
        hi = max(float(np.quantile(v, upper)) for v in values)
    padding = max((hi-lo)*.035, 1e-8)
    return lo-padding, hi+padding


def smoothed_density(values, bandwidth_factor=1.0, grid_points=1600):
    """Fast binned Gaussian KDE for display; never used for inference.

    Uses Silverman's robust bandwidth and reflects Gaussian mass at x=0.
    A histogram convolution provides fast approximate boundary-corrected KDE.
    O(n + grid_points), practical even for millions of Monte Carlo values.
    """
    vals = np.asarray(values, dtype=float)
    vals = vals[np.isfinite(vals)]
    if not vals.size:
        raise ValueError('No finite values')
    if not 0.2 <= float(bandwidth_factor) <= 5:
        raise ValueError('Smoothing bandwidth factor must be between 0.2 and 5')
    if np.any(vals < 0):
        raise ValueError('Boundary-reflected density expects nonnegative statistics')
    lo, hi = 0.0, float(vals.max())
    if hi == 0:
        hi = 1.0
    n = len(vals)
    sigma = float(np.std(vals, ddof=1)) if n > 1 else 0.0
    q25, q75 = np.percentile(vals, [25, 75])
    iqr_sigma = float((q75-q25)/1.349)
    scales = [v for v in (sigma, iqr_sigma) if v > 0]
    scale = min(scales) if scales else max((hi-lo)/6, 1e-8)
    h = max(0.9*scale*n**(-.2)*float(bandwidth_factor), 1e-10)
    # Reflection at the mathematical lower bound (0): scipy's 'reflect'
    # mirrors histogram mass across the left edge before Gaussian convolution.
    # The right-hand padding keeps the reflected upper edge outside the data.
    padding = max(5*h, hi*.01)
    edges = np.linspace(0.0, hi+padding, int(grid_points)+1)
    hist, _ = np.histogram(vals, bins=edges, density=True)
    dx = float(edges[1]-edges[0])
    smooth = gaussian_filter1d(hist, sigma=max(h/dx,.01), mode='reflect', truncate=4)
    x = (edges[:-1]+edges[1:])/2
    # Integrate on the nonnegative half-line only. Histogram center integration
    # misses the half-bin from zero to x[0]; include it for normalization.
    area = np.trapezoid(smooth, x) if hasattr(np, 'trapezoid') else np.trapz(smooth, x)
    area += smooth[0] * x[0]
    if area > 0:
        smooth /= area
    # Include exact boundary x=0 for a line that starts at the physical bound.
    return np.r_[0.0, x], np.r_[smooth[0], smooth]


def make_figure(analysis, kind='CDF', bin_mode='auto', manual_bins=80,
                display_range='99.5', series='Both', show_markers=False,
                pdf_display='Both', smoothing=1.0):
    kind = kind.upper()
    if pdf_display not in ('Both', 'Empirical', 'Smoothed'):
        raise ValueError('PDF display must be Both, Empirical or Smoothed')
    if kind not in ('PDF', 'CDF'):
        raise ValueError('kind must be PDF or CDF')
    if bin_mode not in ('auto', 'manual'):
        raise ValueError('Invalid bin mode')
    if not 2 <= int(manual_bins) <= 5000:
        raise ValueError('Manual bins must be 2 to 5000')
    if display_range not in ('full','99','99.5'):
        raise ValueError('Unknown display range')
    keys = [k for k in ('A','B','AB') if k in analysis.simulated and (series=='Both' or series==k)]
    fig = Figure(figsize=(9, 4.7), dpi=105, layout='constrained')
    ax = fig.add_subplot(111)
    plotted = []
    for key in keys:
        vals = np.asarray(analysis.simulated[key], dtype=float)
        vals = vals[np.isfinite(vals)]
        if not vals.size:
            continue
        plotted.append(vals)
        if kind=='CDF':
            x, counts = np.unique(vals,return_counts=True)
            y = np.cumsum(counts)/len(vals)
            ax.step(x,y,where='post',label=key,color=COLORS[key],linewidth=1.6)
        else:
            if pdf_display in ('Both','Empirical'):
                edges = fd_edges(vals) if bin_mode=='auto' else np.linspace(vals.min()-.000001, vals.max()+.000001, int(manual_bins)+1)
                ax.hist(vals,bins=edges,density=True,histtype='step',label=f'{key} empirical',color=COLORS[key],linewidth=1.55)
            if pdf_display in ('Both','Smoothed'):
                x, y = smoothed_density(vals, bandwidth_factor=float(smoothing))
                ax.plot(x,y,linestyle='--',linewidth=2.0,color=COLORS[key],label=f'{key} smoothed (KDE)')
        if show_markers:
            obs = analysis.observed.get(key)
            if obs is not None:
                ax.axvline(obs['si'],color=COLORS[key],linestyle=':',alpha=.75,linewidth=1.4)
            if key in analysis.critical:
                ax.axvline(analysis.critical[key],color=COLORS[key],linestyle='--',alpha=.85,linewidth=1.4)
    bounds=chart_bounds(plotted,display_range)
    if bounds:
        ax.set_xlim(max(0.0, bounds[0]), max(0.01, bounds[1]))
    if kind=='CDF':
        ax.set_ylim(0, 1.01)
    ax.set_xlabel('Significance index')
    ax.set_ylabel('Empirical cumulative probability' if kind=='CDF' else 'Empirical density')
    ax.set_title(f'{analysis.mode.upper()} - {kind}, {analysis.iterations:,} simulations')
    ax.grid(alpha=.2)
    if plotted:ax.legend(title='Component / curve')
    return fig
