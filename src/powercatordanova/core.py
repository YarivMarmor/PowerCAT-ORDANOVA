"""PowerCAT/ORDANOVA research port, with source-style SI calculations.

Caution: Monte Carlo estimates have not yet been independently validated
against all Excel configurations. No arbitrary 50,000-run limit.
"""
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from scipy.stats import chi2

@dataclass
class Design:
    labels_i: list
    labels_j: list
    labels_k: list
    counts: np.ndarray
    @property
    def shape(self): return self.counts.shape
    @property
    def two_way(self): return len(self.labels_j)>1
    @property
    def n_per_cell(self):
        totals=self.counts.sum(axis=2)
        return int(totals[0,0]) if np.all(totals==totals[0,0]) else None


def load_counts(path):
    """Read VBA I,J,K,Y or I,K,Y comma-delimited input; UTF-16/UTF-8 supported."""
    p=Path(path)
    raw=p.read_bytes()
    if raw.startswith((b'\xff\xfe',b'\xfe\xff')): text=raw.decode('utf-16')
    elif raw.startswith(b'\xef\xbb\xbf'): text=raw.decode('utf-8-sig')
    else:
        try:text=raw.decode('utf-8')
        except UnicodeError:text=raw.decode('cp1252')
    lines=[s.strip() for s in text.splitlines() if s.strip()]
    # Existing VBA datasets use both I,J,K,Y and K,M,L,N headers,
    # and the count column is variously called Y, N or DATA.
    headers=[x.strip().upper() for x in lines[0].split(',')]
    if len(headers) not in (3,4):
        raise ValueError('Expected three (one-way) or four (two-way) columns')
    if len(set(headers)) != len(headers):
        raise ValueError('Duplicate column names')
    # The original files encode factors by position, not by a universal letter.
    # Validate the measurement column but do not rename factor levels.
    if headers[-1] not in ('Y','N','DATA','COUNT'):
        raise ValueError(f'Unrecognized frequency column: {headers[-1]}')
    rows=[]
    for n,line in enumerate(lines[1:],2):
        chunks=[x.strip() for x in line.split(',')]
        if len(chunks)!=len(headers):raise ValueError(f'Line {n}: wrong number of columns')
        i,j,k,y=(chunks if len(headers)==4 else [chunks[0],'(one-way)',chunks[1],chunks[2]])
        value=float(y)
        if not np.isfinite(value) or value<0 or value!=int(value):raise ValueError(f'Line {n}: Y must be a nonnegative integer')
        rows.append((i,j,k,int(value)))
    if not rows:raise ValueError('No data rows')
    def distinct(seq):return list(dict.fromkeys(seq))
    I=distinct(r[0] for r in rows);J=distinct(r[1] for r in rows);K=distinct(r[2] for r in rows)
    def ordered(seq):
        # Sort numeric levels numerically; preserve semantic category order as
        # supplied by the input file (especially essential for ordinal data).
        try:return sorted(seq,key=lambda z:float(z))
        except ValueError:return list(seq)
    I=ordered(I);J=ordered(J);K=ordered(K)
    arr=np.zeros((len(I),len(J),len(K)),dtype=np.int64)
    ia={v:i for i,v in enumerate(I)}; ja={v:i for i,v in enumerate(J)};ka={v:i for i,v in enumerate(K)}
    seen=set()
    for a,b,c,v in rows:
        key=(a,b,c)
        if key in seen:raise ValueError(f'Duplicate design cell {key}')
        seen.add(key);arr[ia[a],ja[b],ka[c]]=v
    if len(seen)!=arr.size:raise ValueError('Incomplete factorial table: missing I,J,K combinations')
    if np.any(arr.sum(axis=2)==0):raise ValueError('Empty I,J cell')
    return Design(I,J,K,arr)


def components(proportions,ordinal=True,balanced_oneway=True):
    """Vectorized source-inspired component computations for balanced designs.

    proportions: (..., I, J, K) probability vectors per I,J cell.
    Returns total, A, B, AB, W as arrays over leading dimensions.
    """
    q=np.asarray(proportions,dtype=float)
    i,j,k=q.shape[-3:]
    if k<2 or i<2:raise ValueError('At least two groups and two categories needed')
    x=np.cumsum(q,axis=-1) if ordinal else q
    factor=(4 if ordinal else k)/(k-1)
    grand=x.mean(axis=(-3,-2))
    amean=x.mean(axis=-2)
    bmean=x.mean(axis=-3)
    total=factor*np.sum(grand*(1-grand),axis=-1)
    a=factor*np.sum((amean-grand[...,None,:])**2,axis=(-2,-1))/i
    b=factor*np.sum((bmean-grand[...,None,:])**2,axis=(-2,-1))/j
    ab=factor*np.sum((x-amean[..., :,None,:]-bmean[...,None,:,:]+grand[...,None,None,:])**2,axis=(-3,-2,-1))/(i*j)
    within=factor*np.sum(x*(1-x),axis=(-3,-2,-1))/(i*j)
    return total,a,b,ab,within



@dataclass
class Analysis:
    design:Design
    mode:str
    alpha:float
    w:float
    iterations:int
    seed:int
    observed:dict
    critical:dict
    p_values:dict
    power:dict
    simulated:dict
    simulated_adjusted:dict


def _oneway_components(counts, ordinal):
    """Weighted one-way decomposition for unequal group sizes.

    One-way MATLAB/VBA components are computed from category proportions
    weighted by each group's empirical sample fraction.
    """
    counts=np.asarray(counts,dtype=float)
    n=counts.sum(axis=-1)
    weights=n/n.sum(axis=-1,keepdims=True)
    p=counts/n[...,None]
    z=np.cumsum(p,axis=-1) if ordinal else p
    grand=np.sum(weights[...,None]*z,axis=-2)
    k=z.shape[-1]
    factor=(4 if ordinal else k)/(k-1)
    total=factor*np.sum(grand*(1-grand),axis=-1)
    a=factor*np.sum(weights[...,None]*(z-grand[...,None,:])**2,axis=(-2,-1))
    within=factor*np.sum(weights[...,None]*z*(1-z),axis=(-2,-1))
    return total,a,within


def analyze(design, mode='Ordinal', alpha=.05, w=.3, iterations=10000, seed=12345, batch=1000, progress=None):
    """Run source-style balanced two-way Monte Carlo; detailed parity still under validation."""
    if mode not in ('Ordinal','Nominal'):raise ValueError('mode must be Ordinal or Nominal')
    if not 0<alpha<1 or w<0 or iterations<100 or batch<1:raise ValueError('Invalid alpha, w, iterations or batch')
    I,J,K=design.shape; n=design.n_per_cell
    if not design.two_way:
        return _analyze_oneway(design,mode,alpha,w,iterations,seed,batch,progress)
    if n is None:raise ValueError('Two-way core requires equal sample sizes for each I,J combination; unbalanced two-way is not yet validated')
    if I<2 or J<2:raise ValueError('Two-way analysis requires >=2 levels for both factors')
    rng=np.random.default_rng(seed)
    obs_p=design.counts/n
    comp=components(obs_p,ordinal=(mode=='Ordinal'))
    total,sa,sb,sab,sw=[float(z) for z in comp]
    without=n==1
    # VBA boolean True evaluates to -1 (not Python +1).
    denom_n=I*J*n + (-1 if without else 0) if mode=='Ordinal' else I*J*n-1
    dftotal=total if total>0 else .0001
    def indices(a,b,ab,total):
        total=np.maximum(total,1e-4)
        a_si=(a/(I-1))/(total/denom_n)
        b_si=(b/(J-1))/(total/denom_n)
        ab_si=(ab/((I-1)*(J-1)))/(total/(I*J*n if mode=='Ordinal' else I*J*n-1)) if not without else None
        return a_si,b_si,ab_si
    a_si,b_si,ab_si=indices(sa,sb,sab,dftotal)
    # VBA suppresses interaction for n==1 and attributes residual as total-A-B.
    observed={'A':{'variation':sa,'df':I-1,'si':a_si},'B':{'variation':sb,'df':J-1,'si':b_si},'AB':None if without else {'variation':sab,'df':(I-1)*(J-1),'si':ab_si},'Within':{'variation':total-sa-sb if without else sw,'df':I*J*n-1-(I-1)-(J-1) if without else I*J*(n-1)},'Total':{'variation':total,'df':I*J*n-1}}
    pooled=design.counts.sum(axis=(0,1)).astype(float);pooled/=pooled.sum()
    distributions={'A':[],'B':[],'AB':[]}
    finished=0
    while finished<iterations:
        size=min(batch,iterations-finished)
        # multinomial yields independent cell counts under common pooled null.
        draws=rng.multinomial(n,pooled,size=(size,I,J))/n
        c=components(draws,ordinal=(mode=='Ordinal'))
        si=indices(c[1],c[2],c[3],c[0])
        for key,vals in zip(('A','B','AB'),si):
            if vals is not None:distributions[key].append(np.asarray(vals))
        finished+=size
        if progress:progress(finished,iterations)
    dist={key:np.concatenate(v) for key,v in distributions.items() if v}
    critical={};pvals={};power={};adjusted={}
    for key in ('A','B','AB'):
        if key not in dist:continue
        v=dist[key]
        if mode=='Ordinal':
            crit=float(np.percentile(v,100*(1-alpha)))
            p=float(np.count_nonzero(v>=observed[key]['si'])/iterations)
        else:
            df=observed[key]['df']*(K-1)
            crit=float(chi2.ppf(1-alpha,df)/df)
            p=float(chi2.sf(observed[key]['si']*df,df))
        critical[key]=crit;pvals[key]=p
        a_factor={'A':I-1,'B':J-1,'AB':(I-1)*(J-1)}[key]
        alt=v*(1+(w*w*I*J*n)/(a_factor*(K-1)))
        adjusted[key]=alt
        power[key]=float(np.count_nonzero(alt>crit)/iterations)
    return Analysis(design,mode,alpha,w,iterations,seed,observed,critical,pvals,power,dist,adjusted)


def _analyze_oneway(design, mode, alpha, w, iterations, seed, batch, progress):
    """One-way weighted analysis; simulation requires comparison against VBA.

    The source workbook's random generator does not preserve unequal input
    group sizes. Here group sizes are held fixed, intentionally; reference
    parity has NOT yet been established. Display this as a research preview.
    """
    if not 0<alpha<1 or w<0 or iterations<100 or batch<1:
        raise ValueError('Invalid alpha, w, iterations or batch')
    I,J,K=design.shape
    if I<2 or K<2:raise ValueError('Need >=2 groups and >=2 categories')
    c=design.counts[:,0,:]
    group_n=c.sum(axis=1)
    total_n=int(group_n.sum())
    ordinal=mode=='Ordinal'
    total,ss_a,ss_w=[float(x) for x in _oneway_components(c,ordinal)]
    denom=max(total,1e-4)
    si=(ss_a/(I-1))/(denom/(total_n-1))
    observed={'A':{'variation':ss_a,'df':I-1,'si':si},
              'B':None,'AB':None,
              'Within':{'variation':ss_w,'df':total_n-I},
              'Total':{'variation':total,'df':total_n-1}}
    pooled=c.sum(axis=0)/total_n
    rng=np.random.default_rng(seed)
    sim=[];done=0
    while done<iterations:
        size=min(batch,iterations-done)
        draw=np.stack([rng.multinomial(int(ni),pooled,size=size)
                       for ni in group_n],axis=1)
        st,sa,_=_oneway_components(draw,ordinal)
        sim.append((sa/(I-1))/(np.maximum(st,1e-4)/(total_n-1)))
        done+=size
        if progress:progress(done,iterations)
    v=np.concatenate(sim)
    if ordinal:
        crit=float(np.percentile(v,100*(1-alpha)))
        p=float(np.mean(v>=si))
    else:
        df=(I-1)*(K-1)
        crit=float(chi2.ppf(1-alpha,df)/df)
        p=float(chi2.sf(si*df,df))
    adjusted=v*(1+w*w*total_n/((I-1)*(K-1)))
    power=float(np.mean(adjusted>crit))
    return Analysis(design,mode,alpha,w,iterations,seed,observed,
                    {'A':crit},{'A':p},{'A':power},{'A':v},{'A':adjusted})
