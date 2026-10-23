import unittest
import numpy as np
from execution_bridge import simulate,ExecutionConfig

class BridgeTests(unittest.TestCase):
    def setUp(self):self.prices=np.ones((6,2))*100;self.weights=np.ones((6,2))*.5
    def test_cash_conservation(self):
        r=simulate(self.prices,self.weights,ExecutionConfig(fee_bps=0,half_spread_bps=0));self.assertAlmostEqual(r['terminal_cash'],1e6)
    def test_no_borrow(self):self.assertTrue(all(r['cash']>=0 for r in simulate(self.prices,self.weights)['ledger']))
    def test_depth_limit(self):
        r=simulate(self.prices,self.weights,ExecutionConfig(depth_units=3));self.assertTrue(all(o['filled']<=3 for o in r['orders'] if o['reason']=='daily'))
    def test_costs(self):self.assertLess(simulate(self.prices,self.weights)['terminal_cash'],1e6)
    def test_accounting(self):self.assertTrue(all(abs(r['reconciliation_residual'])<1e-7 for r in simulate(self.prices,self.weights)['ledger']))
    def test_terminal_identity(self):
        r=simulate(self.prices,self.weights);self.assertAlmostEqual(r['terminal_cash'],r['ledger'][-1]['nav']-r['terminal_cost'])
    def test_future_mutation(self):
        p=self.prices.copy();p[4:]*=2;a=simulate(self.prices,self.weights);b=simulate(p,self.weights);self.assertEqual(a['ledger'][:3],b['ledger'][:3])
    def test_invalid_depth(self):
        with self.assertRaises(ValueError):simulate(self.prices,self.weights,ExecutionConfig(depth_units=0))

if __name__=='__main__':unittest.main()
