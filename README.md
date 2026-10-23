# Systematic Strategies & Execution

[Open the research dashboard](https://anjaney336.github.io/portfolio/research/systematic-strategy-research/) · [Earlier component methodology](docs/PRE_CONSOLIDATION.md)

## Research question and scope
Combines systematic strategy research with the execution lab. Portfolio targets now become cash-constrained integer orders; IOC fills respect assumed depth, and every trading step reconciles fees, slippage, holdings and cash.

## Results
On the same historical price path, depth assumptions materially change fills and exposure. The 100-unit scenario fills about 49.98% of requested units and returns 13.20% cumulatively after terminal costs. This is a hypothetical execution replay, not observed fill performance.

## Calculation conventions
Signals and selection exclude the execution-day close. Orders target floor(weight × pre-trade equity / price). Sells release cash before buys; buys cannot borrow. Wealth after fills = wealth before fills − fees − execution slippage. A separately labelled terminal auction closes positions.

## Data and sources
Yahoo Finance adjusted-price cache for DLF, Godrej Properties, Prestige and Oberoi; accessed 24 October 2026. Exact input hash and URLs in result JSON. Depth/spread scenarios are synthetic.

## Reproduce
Python 3.12. Install `requirements.txt`, then run `python reproduce.py`. Default tests/research run offline; historical runs need the local authorized cache. New entry point: `execution_bridge.py`. Add `--prices /path/to/prices.csv` for historical strategy/derivative experiments.

## Verification
40 tests across the consolidated reproduction command. CI runs the same command. See ENGINEERING.md for boundaries and release checks. The dashboard displays bundled reports; change its view selector to compare analyses, and download CSV/JSON evidence.

## Limits
Depth, spreads and terminal auction capacity are invented scenarios. Better returns under lower liquidity can reflect delayed exposure, not better execution. No calibrated market impact, tax, latency or capacity claims.

## Lineage and authorship
Consolidates existing research modules; original repositories remain as history. This is AI-assisted portfolio research, not code represented as deployed at a financial institution.
