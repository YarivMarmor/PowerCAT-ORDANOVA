from pathlib import Path
from powercatordanova.core import load_counts
from powercatordanova.validation import validate_design
P=Path(__file__).resolve().parents[1]/'examples'
def test_wine():
    p=validate_design(load_counts(P/'two_way_ORDANOVA_with_interaction__wine Data Calculation(1).txt'))
    assert p.ready and p.factors==2 and p.interaction and p.observations==72

def test_water_no_interaction():
    p=validate_design(load_counts(P/'data_water_Chlorine.txt'))
    assert p.ready and not p.interaction and p.observations==90

def test_oneway():
    p=validate_design(load_counts(P/'one_way_CATANOVA_Data_Departments.txt'),'Nominal')
    assert p.ready and p.factors==1 and p.model=='One-way CATANOVA'

def test_unbalanced_rejected():
    from powercatordanova.core import Design
    import numpy as np
    d=Design(['A','B'],['x','y'],['low','high'],np.array([[[1,2],[1,3]],[[3,1],[1,2]]]))
    p=validate_design(d)
    assert not p.ready and any('Unbalanced' in e for e in p.errors)

def test_invalid_mode():
    p=validate_design(load_counts(P/'data_water_Chlorine.txt'),'Other')
    assert not p.ready
