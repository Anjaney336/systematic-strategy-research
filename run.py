from pathlib import Path
import argparse,csv,json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from engine import account,metrics,walk_forward

def bootstrap_difference(a,b,seed=42):
 rng=np.random.default_rng(seed);d=a-b;n=len(d);samples=[]
 for _ in range(1000):
  starts=rng.integers(0,n,size=(n+19)//20);indices=np.concatenate([(s+np.arange(20))%n for s in starts])[:n];samples.append(np.mean(d[indices])*252)
 return {'annualized_mean_difference':float(np.mean(d)*252),'lower_95':float(np.quantile(samples,.025)),'upper_95':float(np.quantile(samples,.975)),'block_length':20,'resamples':1000,'conditional_on_selected_path':True}

def run():
 ap=argparse.ArgumentParser();ap.add_argument('--prices');args=ap.parse_args();root=Path(__file__).parent
 if args.prices:
  file=Path(args.prices);rows=list(csv.DictReader(file.open()));symbols=['DLF.NS','GODREJPROP.NS','PRESTIGE.NS','OBEROIRLTY.NS'];valid=[r for r in rows if all(r.get(s) for s in symbols)];dates=[r['Date'] for r in valid];p=np.array([[float(r[s]) for s in symbols] for r in valid]);dataset='historical';source={'name':'Yahoo Finance vendor-adjusted closes; fixed survivor universe','links':['https://finance.yahoo.com/quote/'+s+'/history/' for s in symbols],'access_date':'2026-10-24','sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
 else:
  rng=np.random.default_rng(20261024);n=1800;m=4;common=rng.normal(.00015,.01,(n,1));idio=rng.normal(0,.012,(n,m));p=100*np.exp(np.cumsum(common+idio,axis=0));dates=[str(i) for i in range(n)];dataset='synthetic';symbols=['A','B','C','D'];source={'name':'Seeded correlated geometric paths; assumed distribution','link':'https://github.com/Anjaney336/systematic-strategy-research/blob/main/run.py','access_date':'2026-10-24','seed':20261024}
 if args.prices:assert all(a<b for a,b in zip(dates,dates[1:])), 'dates must be unique and chronological'
 out=root/'results'/dataset;out.mkdir(parents=True,exist_ok=True);start=505;w,folds=walk_forward(p);result=account(p,w);r=result['returns'][start:]
 # Equal-weight buy-and-hold: allow weights to drift, no daily rebalancing.
 bench=np.zeros_like(p);bench[start]=np.ones(p.shape[1])/p.shape[1]
 for t in range(start+1,len(p)):
  ar=p[t-1]/p[t-2]-1;bench[t]=bench[t-1]*(1+ar)/(1+bench[t-1]@ar)
 br=account(p,bench)['returns'][start:];costs=[]
 for fee in [0,5,10,25,50]:costs.append({'cost_bps':fee,**metrics(account(p,w,fee)['returns'][start:])})
 report={'dataset':dataset,'source':source,'symbols':symbols,'start':dates[start],'end':dates[-1],'strategy':metrics(r),'benchmark':metrics(br),'paired_block_bootstrap':bootstrap_difference(r,br),'folds':folds,'cost_sensitivity':costs,'assumptions':{'train_observations':504,'test_observations':126,'candidate_rules':9,'vol_target':.12,'cost_bps_per_turnover':10,'cash_rate':0,'long_only':True,'max_gross':1,'signal_lag':'t-2 information, close t-1 execution, t return'},'limitations':['Retrospective pseudo-OOS, not an unseen live experiment','Fixed present-day survivor universe; selection bias','Adjusted close execution proxy, no actual fill, impact, taxes or capacity','Conditional bootstrap does not correct research-selection bias','No guarantee of positive performance']}
 for name,records in [('folds',folds),('cost_sensitivity',costs)]:
  with (out/(name+'.csv')).open('w',newline='') as f:wr=csv.DictWriter(f,fieldnames=records[0]);wr.writeheader();wr.writerows(records)
 with (out/'ledger.csv').open('w',newline='') as f:
  wr=csv.writer(f);wr.writerow(['date','strategy_return','benchmark_return','exposure','turnover','nav']);wr.writerows(zip(dates[start:],r,br,w[start:].sum(axis=1),result['turnover'][start:],np.cumprod(1+r)))
 (out/'summary.json').write_text(json.dumps(report,indent=2));fig,axs=plt.subplots(2,1,figsize=(10,6),sharex=True)
 for values,label in [(r,'Selected strategy'),(br,'Buy and hold')]:
  nav=np.cumprod(1+values);axs[0].plot(nav,label=label);axs[1].plot(nav/np.maximum.accumulate(np.r_[1.,nav])[1:]-1,label=label)
 axs[0].set(ylabel='Growth of 1',title=dataset.title()+' chronological evaluation after costs');axs[0].legend();axs[1].set(ylabel='Drawdown',xlabel='Evaluation observation');fig.tight_layout();fig.savefig(out/'performance.svg');plt.close(fig)
 print(json.dumps({k:report[k] for k in ['dataset','strategy','benchmark','paired_block_bootstrap']},indent=2))
if __name__=='__main__':run()
