"""Causal daily portfolio accounting. Signals use t-2; trade at close t-1."""
import numpy as np

def validate(p):
 p=np.asarray(p,float)
 if p.ndim!=2 or len(p)<3 or not np.isfinite(p).all() or (p<=0).any():raise ValueError('positive finite price matrix required')
 return p

def targets(prices,lookback=63,mode='momentum',vol_target=.12):
 p=validate(prices)
 if lookback<2 or mode not in ['momentum','reversion','trend']:raise ValueError('invalid specification')
 n,m=p.shape;w=np.zeros((n,m));r=p[1:]/p[:-1]-1
 for t in range(lookback+1,n):
  hist=p[:t-1] # latest observed close t-2; order executes t-1
  window=hist[-lookback:];ret=window[-1]/window[0]-1
  signal=(ret>0) if mode=='momentum' else ((window[-1]<window.mean(axis=0)) if mode=='reversion' else (window[-1]>window.mean(axis=0)))
  sigvol=np.std(r[max(0,t-1-lookback):t-2],axis=0,ddof=1)*np.sqrt(252)
  raw=signal.astype(float)/np.maximum(sigvol,.05)
  if raw.sum()>0:
   raw/=raw.sum();portfolio_vol=np.std(r[max(0,t-1-lookback):t-2]@raw,ddof=1)*np.sqrt(252)
   w[t]=raw*min(1,vol_target/max(portfolio_vol,.01))
 return w

def account(prices,weights,cost_bps=10):
 p=validate(prices);w=np.asarray(weights,float)
 if w.shape!=p.shape or not np.isfinite(w).all() or (w<0).any() or (w.sum(axis=1)>1+1e-9).any() or not 0<=cost_bps<10000:raise ValueError('invalid weights or costs')
 n,m=p.shape;ret=np.zeros(n);turn=np.zeros(n);cost=np.zeros(n);held=np.zeros(m)
 for t in range(1,n):
  turn[t]=np.abs(w[t]-held).sum();cost[t]=turn[t]*cost_bps/10000
  asset=p[t]/p[t-1]-1;gross=float(w[t]@asset)
  ret[t]=(1-cost[t])*(1+gross)-1
  held=w[t]*(1+asset)/(1+gross)
 # Final liquidation is charged explicitly at the final mark.
 liquidation=held.sum()*cost_bps/10000;ret[-1]=(1+ret[-1])*(1-liquidation)-1;cost[-1]+=liquidation;turn[-1]+=held.sum()
 return {'returns':ret,'turnover':turn,'cost_fraction':cost,'nav':np.cumprod(1+ret)}

def metrics(r):
 r=np.asarray(r);nav=np.cumprod(1+r);peak=np.maximum.accumulate(np.r_[1.,nav])[1:];sd=np.std(r,ddof=1)
 return {'observations':len(r),'total_return':float(nav[-1]-1),'cagr':float(nav[-1]**(252/len(r))-1),'sharpe_zero_rf':float(np.mean(r)/sd*np.sqrt(252)) if sd>0 else 0.,'max_drawdown':float(np.min(nav/peak-1))}

def walk_forward(p,train=504,test=126,cost_bps=10):
 p=validate(p);specs=[(m,l) for m in ['momentum','reversion','trend'] for l in [21,63,126]]
 ws=[targets(p,l,m) for m,l in specs];chosen=np.zeros_like(p);folds=[]
 for start in range(train+1,len(p),test):
  stop=min(len(p),start+test);scores=[]
  for weights in ws:
   # Recreate training accounting from cash, including deployment and liquidation.
   scores.append(metrics(account(p[start-train-1:start-1],weights[start-train-1:start-1],cost_bps)['returns'][1:])['sharpe_zero_rf'])
  winner=int(np.argmax(scores));chosen[start:stop]=ws[winner][start:stop]
  folds.append({'start':start,'stop':stop,'mode':specs[winner][0],'lookback':specs[winner][1],'training_sharpe':scores[winner]})
 return chosen,folds
