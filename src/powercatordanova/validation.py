"""Preflight design checks for PowerCAT / ORDANOVA.

These checks reproduce the Excel workflow's data summary and model choice,
with additional explicit Python-side input diagnostics. They do not certify
Monte Carlo agreement with either workbook.
"""
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class Preflight:
    model: str
    factors: int
    levels_a: int
    levels_b: int
    categories: int
    observations: int
    sample_min: int
    sample_max: int
    replication: str
    interaction: bool
    errors: tuple
    warnings: tuple
    @property
    def ready(self): return not self.errors


def validate_design(design, mode='Ordinal'):
    i,j,k=design.shape
    totals=design.counts.sum(axis=2)
    n_min=int(np.min(totals)); n_max=int(np.max(totals))
    errors=[]; warnings=[]
    if mode not in ('Ordinal','Nominal'):
        errors.append('Choose Ordinal or Nominal before analysis.')
    if i<2: errors.append('Factor A needs at least two distinct levels.')
    if k<2: errors.append('The response needs at least two categories.')
    if j>1 and j<2: errors.append('Factor B needs at least two levels.')
    if n_min<=0:errors.append('Every design cell must contain at least one observation.')
    if j>1 and n_min!=n_max:
        errors.append('Unbalanced two-factor designs are not supported by this engine. Do not alter genuine observations merely to equalize sample sizes.')
    if k>1 and (np.asarray(design.counts).sum(axis=(0,1))==0).any():
        warnings.append('At least one response category has no observations. Verify the category definitions.')
    if j==1:
        replication='Group sizes vary' if n_min!=n_max else f'{n_min} observations per group'
        warnings.append('One-factor Monte Carlo statistics have not been fully validated against VBA.')
    elif n_min==1 and n_max==1:
        replication='One observation per A x B cell; interaction not separately estimable'
    else:
        replication=f'{n_min} observations per cell' if n_min==n_max else f'{n_min}-{n_max} observations per cell'
    warnings.append('Monte Carlo p-values, critical values and power remain under VBA validation.')
    return Preflight(('Two-way' if j>1 else 'One-way')+' '+('ORDANOVA' if mode=='Ordinal' else 'CATANOVA'),
                     2 if j>1 else 1,i,j,k,int(design.counts.sum()),n_min,n_max,replication,
                     j>1 and n_min>1,tuple(errors),tuple(warnings))
