from pathlib import Path
import numpy as np
import pytest
from powercatordanova import load_counts,analyze,components
P=Path(__file__).resolve().parents[1]/'examples'/'data_water_Chlorine.txt'
def test_load():
 d=load_counts(P)
 assert d.shape==(45,2,6)
 assert d.n_per_cell==1
 assert d.counts.sum()==90

def test_components_total():
 d=load_counts(P)
 total,a,b,ab,w=components(d.counts,ordinal=True)
 assert np.isclose(total,.3663,atol=.00015)
 assert np.isclose(a,.2463,atol=.00015)
 assert np.isclose(b,.01,atol=.00015)
 r=analyze(d,iterations=150,seed=3)
 assert np.isclose(r.observed['A']['si'],1.3601,atol=.0001)
 assert np.isclose(r.observed['B']['si'],2.4236,atol=.0001)

def test_simulation_reproducible():
 d=load_counts(P)
 a=analyze(d,iterations=250,seed=47)
 b=analyze(d,iterations=250,seed=47)
 assert np.array_equal(a.simulated['A'],b.simulated['A'])
 assert a.observed['AB'] is None
 assert 0<=a.p_values['A']<=1

def test_bad_input(tmp_path):
 p=tmp_path/'bad.csv';p.write_text('I,J,K,Y\na,b,1,-1')
 with pytest.raises(ValueError):load_counts(p)

def test_auto_bins_shrink_as_n_increases():
 from powercatordanova.charts import fd_edges
 rng=np.random.default_rng(17)
 small=rng.normal(size=10000)
 large=rng.normal(size=1000000)
 s=fd_edges(small);l=fd_edges(large)
 assert np.diff(l)[0]<np.diff(s)[0]

def test_chart_settings_do_not_mutate_analysis():
 from powercatordanova.charts import make_figure
 d=load_counts(P)
 r=analyze(d,iterations=200,seed=13)
 before=r.simulated['A'].copy()
 for bins in ('auto','manual'):
  for kind in ('PDF','CDF'):
   fig=make_figure(r,kind,bin_mode=bins,manual_bins=35,display_range='99',series='A',show_markers=True)
   assert len(fig.axes)==1
 assert np.array_equal(before,r.simulated['A'])


def test_kde_density_and_display_modes():
 from powercatordanova.charts import smoothed_density, make_figure
 d=load_counts(P)
 r=analyze(d,iterations=500,seed=53)
 orig=r.simulated['A'].copy()
 x,y=smoothed_density(orig,bandwidth_factor=1.0)
 assert np.all(np.isfinite(y)) and np.all(y>=0)
 assert .97<np.trapezoid(y,x)<1.03
 for mode in ('Both','Empirical','Smoothed'):
  fig=make_figure(r,kind='PDF',series='A',pdf_display=mode,smoothing=1.5)
  assert len(fig.axes)==1
 assert np.array_equal(orig,r.simulated['A'])

def test_reject_invalid_smoothing():
 from powercatordanova.charts import smoothed_density
 with pytest.raises(ValueError):smoothed_density([1,2,3],bandwidth_factor=0)


def test_reflected_kde_nonnegative_and_normalized():
 from powercatordanova.charts import smoothed_density
 rng=np.random.default_rng(127)
 for values in [rng.exponential(0.8, 20000), rng.uniform(0,0.2, 20000), np.zeros(300)]:
  x,y=smoothed_density(values)
  assert x[0]==0 and np.all(x>=0)
  assert np.all(np.isfinite(y)) and np.all(y>=0)
  assert 0.98 < np.trapezoid(y,x) < 1.02

def test_reflected_kde_boundary_density():
 from powercatordanova.charts import smoothed_density
 # With mass at zero, reflection yields nonzero density at the boundary.
 x,y=smoothed_density(np.zeros(1000))
 assert x[0]==0 and y[0]>0
