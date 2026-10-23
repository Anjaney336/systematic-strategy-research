"""Map causal portfolio targets to integer orders and a reconciled cash ledger.

Displayed depth and spread are scenario assumptions, not historical quotes.
"""
from dataclasses import dataclass
from pathlib import Path
import argparse
import csv
import hashlib
import json
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from execution.book import Book
from engine import validate, walk_forward


@dataclass(frozen=True)
class ExecutionConfig:
    capital: float = 1_000_000
    fee_bps: float = 10
    half_spread_bps: float = 5
    depth_units: int = 100

    def validate(self):
        if not all(math.isfinite(x) for x in [self.capital,self.fee_bps,self.half_spread_bps]) or self.capital<=0 or not 0<=self.fee_bps<1000 or not 0<=self.half_spread_bps<1000 or type(self.depth_units) is not int or self.depth_units<=0:
            raise ValueError('invalid execution configuration')


def simulate(prices,weights,config=ExecutionConfig()):
    prices=validate(prices);weights=np.asarray(weights,float);config.validate()
    if weights.shape!=prices.shape or not np.isfinite(weights).all() or (weights<0).any() or (weights.sum(axis=1)>1+1e-9).any():
        raise ValueError('invalid portfolio weights')
    cash=config.capital;positions=np.zeros(prices.shape[1],dtype=int);orders=[];ledger=[]
    for t in range(1,len(prices)):
        marks=prices[t-1];pre=cash+positions@marks
        targets=np.floor(weights[t]*pre/marks).astype(int)
        # Sell first to release funds; buys cannot borrow.
        requests=[(j,int(targets[j]-positions[j])) for j in range(len(positions))]
        requests.sort(key=lambda x:x[1])
        fees=slippage=0.
        for j,request in requests:
            if request==0:continue
            side='B' if request>0 else 'S'
            tick=max(1,round(marks[j]*100*(1+(1 if side=='B' else -1)*config.half_spread_bps/1e4)))
            quote=tick/100;quantity=abs(request)
            if side=='B':quantity=min(quantity,max(0,math.floor(cash/(quote*(1+config.fee_bps/1e4)))))
            if not quantity:
                orders.append(dict(step=t,instrument=j,side=side,requested=abs(request),submitted=0,filled=0,price=quote,fee=0.,reason='cash_limit'));continue
            book=Book(max_quantity=max(quantity,config.depth_units,10000))
            book.apply(dict(type='NEW',ts=t,order_id='maker',side='S' if side=='B' else 'B',price=tick,qty=config.depth_units,tif='GTC'))
            response=book.apply(dict(type='NEW',ts=t,order_id='portfolio',side=side,price=tick,qty=quantity,tif='IOC'))
            filled=sum(x['qty'] for x in response['trades']);fee=filled*quote*config.fee_bps/1e4;sign=1 if side=='B' else -1
            cash-=sign*filled*quote+fee;positions[j]+=sign*filled;fees+=fee;slippage+=sign*filled*(quote-marks[j])
            orders.append(dict(step=t,instrument=j,side=side,requested=abs(request),submitted=quantity,filled=filled,price=quote,fee=fee,reason='daily'))
        post=cash+positions@marks
        residual=post-(pre-fees-slippage)
        if cash < -1e-6 or (positions<0).any() or abs(residual)>1e-6:raise AssertionError('cash/inventory/wealth reconciliation failed')
        nav=cash+positions@prices[t]
        ledger.append(dict(step=t,cash=cash,holdings_value=float(positions@prices[t]),nav=float(nav),fees=fees,slippage=slippage,reconciliation_residual=float(residual)))
    # Terminal liquidation assumes an auction with enough capacity; separately labelled.
    terminal_cost=0.
    for j,qty in enumerate(positions):
        if not qty:continue
        quote=prices[-1,j]*(1-config.half_spread_bps/1e4);fee=qty*quote*config.fee_bps/1e4
        cash+=qty*quote-fee;terminal_cost+=qty*(prices[-1,j]-quote)+fee
        orders.append(dict(step=len(prices)-1,instrument=j,side='S',requested=int(qty),submitted=int(qty),filled=int(qty),price=float(quote),fee=float(fee),reason='terminal_auction_assumed_capacity'))
    return {'ledger':ledger,'orders':orders,'terminal_cash':float(cash),'terminal_cost':float(terminal_cost),'total_return':float(cash/config.capital-1)}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prices');args=parser.parse_args()
    if args.prices:
        file=Path(args.prices);rows=list(csv.DictReader(file.open()));symbols=['DLF.NS','GODREJPROP.NS','PRESTIGE.NS','OBEROIRLTY.NS'];rows=[r for r in rows if all(r.get(s) for s in symbols)]
        assert all(a['Date']<b['Date'] for a,b in zip(rows,rows[1:]));prices=np.array([[float(r[s]) for s in symbols] for r in rows]);mode='historical'
        source={'name':'Yahoo Finance adjusted-close cache; hypothetical execution','urls':['https://finance.yahoo.com/quote/'+s+'/history/' for s in symbols],'access_date':'2026-10-24','sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
    else:
        rng=np.random.default_rng(20261024);prices=100*np.exp(np.cumsum(rng.normal(.0002,.012,(900,4)),axis=0));mode='synthetic';source={'name':'Seeded synthetic geometric prices','url':'https://github.com/Anjaney336/systematic-strategy-research/blob/main/execution_bridge.py','access_date':'2026-10-24','seed':20261024}
    weights,folds=walk_forward(prices);out=Path(__file__).parent/'results/execution'/mode;out.mkdir(parents=True,exist_ok=True);scenarios=[];fig,ax=plt.subplots(figsize=(10,4.5))
    for depth in [25,100,1000]:
        result=simulate(prices,weights,ExecutionConfig(depth_units=depth));daily=[o for o in result['orders'] if o['reason']!='terminal_auction_assumed_capacity'];requested=sum(o['requested'] for o in daily);filled=sum(o['filled'] for o in daily)
        scenarios.append({'depth_units':depth,'return_after_terminal_cost':result['total_return'],'filled_units':filled,'requested_units':requested,'unit_fill_ratio':filled/requested if requested else 1.,'terminal_cost':result['terminal_cost']})
        ax.plot([r['step'] for r in result['ledger']],[r['nav']/1e6 for r in result['ledger']],label=f'Depth {depth}')
        for name,records in [('orders',result['orders']),('ledger',result['ledger'])]:
            with (out/f'{name}_{depth}.csv').open('w',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=records[0]);writer.writeheader();writer.writerows(records)
    report={'source':source,'scenarios':scenarios,'folds':len(folds),'assumptions':{'fee_bps':10,'half_spread_bps':5,'depth_units':[25,100,1000],'capital':1_000_000},'limits':'Synthetic displayed depth, adjusted-close marks, tick rounding and terminal auction capacity. No market impact, latency, empirically observed order book, taxes or trading-size feasibility. Curves are pre-liquidation; reported returns include final liquidation.'}
    (out/'summary.json').write_text(json.dumps(report,indent=2));ax.set(xlabel='Observation',ylabel='NAV / initial capital',title='Causal targets → integer orders → fills → reconciled cash');ax.legend();fig.tight_layout();fig.savefig(out/'execution.svg');plt.close(fig);print(json.dumps(report,indent=2))

if __name__=='__main__':main()
