# $Id$
#
#  Copyright (C) 2002-2008  greg Landrum and Rational Discovery LLC
#
#   @@ All Rights Reserved @@
#  This file is part of the RDKit.
#  The contents are covered by the terms of the BSD license
#  which is included in the file license.txt, found at the root
#  of the RDKit source tree.
#
"""unit testing code for the signatures

"""
import unittest
import os.path
from rdkit import RDConfig
from rdkit.Chem import ChemicalFeatures
from rdkit import Chem
from rdkit.Chem.Pharm2D import Generate, SigFactory, Matcher, Gobbi_Pharm2D


class TestCase(unittest.TestCase):

  def setUp(self):
    fdefFile = os.path.join(RDConfig.RDCodeDir, 'Chem', 'Pharm2D', 'test_data', 'BaseFeatures.fdef')
    featFactory = ChemicalFeatures.BuildFeatureFactory(fdefFile)
    self.factory = SigFactory.SigFactory(featFactory, minPointCount=2, maxPointCount=3)
    self.factory.SetBins([(0, 2), (2, 5), (5, 8)])
    self.factory.Init()

  def test1(self):
    """ simple tests

    """
    mol = Chem.MolFromSmiles('OCC(=O)CCCN')
    self.factory.skipFeats = ['Donor']
    self.factory.Init()
    self.assertEqual(self.factory.GetSigSize(), 510)
    Generate._verbose = False
    sig = Generate.Gen2DFingerprint(mol, self.factory)
    Generate._verbose = False
    tgt = (1, 2, 11, 52, 117)
    onBits = sig.GetOnBits()
    self.assertEqual(tuple(onBits), tgt)
    self.assertEqual(len(onBits), len(tgt))

    bitMatches = ([((0, ), (3, ))],
                  [((0, ), (7, )), ((3, ), (7, ))],
                  [((0, ), (3, ), (7, ))], )
    for i in range(len(onBits)):
      bit = onBits[i]
      matches = Matcher.GetAtomsMatchingBit(self.factory, bit, mol)
      #print bit,matches
      #tgt = bitMatches[i]
      #self.assertEqual(matches,tgt)

  def test2Bug28(self):
    smi = 'Cc([s]1)nnc1SCC(\CS2)=C(/C([O-])=O)N3C(=O)[C@H]([C@@H]23)NC(=O)C[n]4cnnn4'
    mol = Chem.MolFromSmiles(smi)
    factory = Gobbi_Pharm2D.factory
    factory.SetBins([(2, 3), (3, 4), (4, 5), (5, 8), (8, 100)])
    sig = Generate.Gen2DFingerprint(mol, factory)
    onBits = sig.GetOnBits()
    for bit in onBits:
      atoms = Matcher.GetAtomsMatchingBit(factory, bit, mol, justOne=1)
      self.assertTrue(len(atoms))

  def test3Roundtrip(self):
    """ longer-running Bug 28 test
    """
    from rdkit import RDConfig
    import os
    nToDo = 20
    with open(os.path.join(RDConfig.RDDataDir, 'NCI', 'first_5K.smi'), 'r') as inF:
      inD = inF.readlines()[:nToDo]
    factory = Gobbi_Pharm2D.factory
    factory.SetBins([(2, 3), (3, 4), (4, 5), (5, 8), (8, 100)])
    for line in inD:
      smi = line.split('\t')[0]
      mol = Chem.MolFromSmiles(smi)
      sig = Generate.Gen2DFingerprint(mol, factory)
      onBits = sig.GetOnBits()
      for bit in onBits:
        atoms = Matcher.GetAtomsMatchingBit(factory, bit, mol, justOne=1)
        assert len(atoms), 'bit %d failed to match for smi %s' % (bit, smi)


if __name__ == '__main__':
  unittest.main()
