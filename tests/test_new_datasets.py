from pathlib import Path
import numpy as np
import pytest
from powercatordanova.core import load_counts, analyze

EXAMPLES=Path(__file__).resolve().parents[1]/'examples'
DATA=sorted(EXAMPLES.glob('*.txt'))

@pytest.mark.parametrize('path',DATA,ids=lambda p:p.name)
def test_all_import_and_simulate(path):
    d=load_counts(path)
    assert int(d.counts.sum())>0
    mode='Nominal' if 'CATANOVA' in path.name and 'ORDANOVA' not in path.name else 'Ordinal'
    r=analyze(d,mode=mode,iterations=100,seed=123)
    assert 'A' in r.simulated
    assert 'B' in r.simulated if d.two_way else 'B' not in r.simulated
    if d.two_way and d.n_per_cell>1:
        assert 'AB' in r.simulated

def test_wine_ordinal_observed_excel_reference():
    f=EXAMPLES/'two_way_ORDANOVA_with_interaction__wine Data Calculation(1).txt'
    r=analyze(load_counts(f),iterations=100,seed=123)
    for k,ss,si in [('A',.0347,4.3028),('B',.1011,12.5259),('AB',.0085,1.0518)]:
        assert abs(r.observed[k]['variation']-ss)<.00005
        assert abs(r.observed[k]['si']-si)<.00005
    assert abs(r.observed['Within']['variation']-.4367)<.00005
    assert abs(r.observed['Total']['variation']-.5810)<.00005

def test_water_observed_reference():
    r=analyze(load_counts(EXAMPLES/'data_water_Chlorine.txt'),iterations=100)
    assert r.observed['AB'] is None
    assert abs(r.observed['A']['si']-1.3601)<.00005
    assert abs(r.observed['B']['si']-2.4236)<.00005
