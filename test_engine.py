import unittest
import numpy as np
from engine import targets,account,walk_forward,metrics
class EngineTests(unittest.TestCase):
 def setUp(self):self.p=100*np.exp(np.cumsum(np.random.default_rng(8).normal(0,.01,(700,3)),axis=0))
 def test_signal_causality(self):
  altered=self.p.copy();altered[400:]*=2;np.testing.assert_array_equal(targets(self.p)[:402],targets(altered)[:402])
 def test_selection_excludes_execution_close(self):
  p=self.p.copy();p[504:]*=1.7;a,fa=walk_forward(self.p);b,fb=walk_forward(p);self.assertEqual(fa[0],fb[0]);np.testing.assert_array_equal(a[505],b[505])
 def test_walk_forward_selection_causality(self):
  p=self.p.copy();p[600:]*=2;a,fa=walk_forward(self.p);b,fb=walk_forward(p);self.assertEqual(fa[0],fb[0]);np.testing.assert_array_equal(a[:602],b[:602])
 def test_cash(self):np.testing.assert_array_equal(account(self.p,np.zeros_like(self.p))['returns'],0)
 def test_hand_account(self):
  p=np.array([[100.],[110.],[121.]]);w=np.ones_like(p);self.assertAlmostEqual(account(p,w,0)['nav'][-1],1.21)
 def test_costs_reduce_nav(self):
  w=targets(self.p);self.assertLess(account(self.p,w,20)['nav'][-1],account(self.p,w,0)['nav'][-1])
 def test_final_liquidation(self):
  p=np.ones((3,1))*100;w=np.ones_like(p);self.assertAlmostEqual(account(p,w,10)['nav'][-1],.999**2)
 def test_no_extra_buyhold_turnover(self):
  p=np.array([[100.],[110.],[121.]]);w=np.ones_like(p);self.assertAlmostEqual(account(p,w,0)['turnover'].sum(),2)
 def test_bounds(self):
  w=targets(self.p);self.assertTrue((w.sum(axis=1)<=1+1e-9).all());self.assertTrue((w>=0).all())
 def test_invalid_price(self):
  with self.assertRaises(ValueError):targets(np.zeros((20,2)))
 def test_invalid_weights(self):
  with self.assertRaises(ValueError):account(self.p,np.ones_like(self.p))
 def test_drawdown(self):self.assertAlmostEqual(metrics([.1,-.2])['max_drawdown'],-.2)
if __name__=='__main__':unittest.main()
