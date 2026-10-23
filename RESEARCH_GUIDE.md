# Systematic Strategies & Execution — calculation and decision guide

Does a selected strategy survive costs, limited liquidity and cash constraints?

## Specify the information set

Nine candidate rules are selected using trailing training data. Selection and signals exclude the execution-day close; the historical evaluation is retrospective, not an untouched live test.

## Separate signal quality from execution

The costed strategy produces about 1.95% CAGR versus 21.29% for its benchmark over the reported sample. The negative benchmark comparison is retained. The execution bridge is a separate integer-order experiment, not the same return series.

## Turn targets into orders

Target units are rounded down; sells release cash before buys. IOC orders receive partial fills when assumed displayed depth is insufficient. Requested, submitted and filled quantities remain in the journal.

## Reconcile the result

Check cash, inventory, fees and slippage after every step. The 100-unit depth replay has a 49.98% unit fill ratio and 13.20% cumulative return after terminal costs. Other depth assumptions change exposure, so higher returns are not proof of execution skill.

## Calculation

Target units = floor(weight × pre-trade equity / reference price); post-fill wealth = pre-fill wealth − fees − slippage; cash ≥ 0 and holdings ≥ 0.

## Graph interpretation

### Orders and fills: historical price replay

Compare the same signal targets under three assumed depth levels. The paths differ because unfilled orders change subsequent holdings and cash. Curves precede final liquidation; headline returns include the separately charged terminal auction.

### Strategy versus benchmark

The historical strategy trails buy-and-hold despite a smaller maximum drawdown. Inspect both opportunity cost and loss reduction. The zero-risk-free Sharpe and conditional bootstrap are diagnostics, not a correction for research-selection bias.

### Paired execution robustness

Each point aggregates 100 paired synthetic paths. The vertical axis is TWAP minus immediate implementation shortfall in basis points; negative values favour TWAP in this simulator. The result depends on the synthetic price process, fees and assumed depth.

## Review evidence

engine.py · execution_bridge.py · test_bridge.py · execution/ · results/execution/historical/

Demonstrates: Causal research, market microstructure, execution decisions and P&L reconciliation.

All values are existing recorded outputs. No new performance experiment was run for this presentation update. Refer to the README and result JSON for data sources, access dates, units and limitations.
