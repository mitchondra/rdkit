
import fmcs
import unittest
import time

from rdkit import Chem
from rdkit.Chem import MCS

def load_smiles(text):
    mols = []
    for line in text.strip().splitlines():
        smiles = line.split()[0]
        mol = Chem.MolFromSmiles(smiles)
        assert mol is not None, smiles
        mols.append(mol)
    return mols

_ignore = object()
class MCSTestCase(unittest.TestCase):
    def assert_search(self, smiles, num_atoms, num_bonds, smarts=_ignore, **kwargs):
        result = MCS.FindMCS(smiles, **kwargs)
        self.assert_result(result, completed=1, num_atoms=num_atoms, num_bonds=num_bonds,
                           smarts=smarts)
        
    def assert_result(self, result, completed=_ignore, num_atoms=_ignore,
                      num_bonds=_ignore, smarts=_ignore):
        if completed is not _ignore:
            self.assertEquals(result.completed, completed)
        if num_atoms is not _ignore:
            self.assertEquals(result.num_atoms, num_atoms)
        if num_bonds is not _ignore:
            self.assertEquals(result.num_bonds, num_bonds)
        if smarts is not _ignore:
            self.assertEquals(result.smarts, smarts)

simple_mols = load_smiles("""
c1ccccc1O phenol
CO methanol""")


class TestMinAtoms(MCSTestCase):
    def test_min_atoms_2(self):
        self.assert_search(simple_mols, 2, 1, min_num_atoms=2)
        
    def test_min_atoms_3(self):
        self.assert_search(simple_mols, -1, -1, smarts=None, min_num_atoms=3)

    def test_min_atoms_1(self):
        try:
            result = MCS.FindMCS(simple_mols, min_num_atoms=1)
        except ValueError:
            pass
        else:
            raise AssertionError("should have raised an exception")

maximize_mols = load_smiles("""
C12CCC1CC2OCCCCCCC 2-rings-and-chain-with-O
C12CCC1CC2SCCCCCCC 2-rings-and-chain-with-S
""")

class TextMaximize(MCSTestCase):
    # C12CCC1CC2OCCCCCCC 2-rings-and-chain-with-O
    # C12CCC1CC2SCCCCCCC 2-rings-and-chain-with-S
    def test_maximize_default(self):
        # default maximizes the number of bonds
        self.assert_search(maximize_mols, 6, 7)
    def test_maximize_atoms(self):
        self.assert_search(maximize_mols, 7, 6, maximize="atoms")
    def test_maximize_bonds(self):
        self.assert_search(maximize_mols, 6, 7, maximize="bonds")
        
atomtype_mols = load_smiles("""
c1ccccc1O phenol
CCCCCCOn1cccc1 different-answers-depending-on-type
""")

class TestAtomTypes(MCSTestCase):
    # The tests compare:
    #   c1ccccc1O
    #   CCCCCCOn1cccc1
    def test_atom_compare_default(self):
        self.assert_search(atomtype_mols, 4, 3, smarts='[#6]:[#6]:[#6]:[#6]')
    def test_atom_compare_elements(self):
        self.assert_search(atomtype_mols, 4, 3, smarts='[#6]:[#6]:[#6]:[#6]', atom_compare="elements")

    def test_atom_compare_any(self):
        # Note: bond aromaticies must still match!
        # 'cccccO' matches 'ccccnO'
        self.assert_search(atomtype_mols, 6, 5, atom_compare="any")

    def test_atom_compare_any_bond_compare_any(self):
        # Linear chain of 7 atoms
        self.assert_search(atomtype_mols, 7, 6, atom_compare="any", bond_compare="any")
        
    def test_bond_compare_any(self):
        # Linear chain of 7 atoms
        self.assert_search(atomtype_mols, 7, 6, bond_compare="any")

isotope_mols = load_smiles("""
C1C[0N]CC[5C]1[1C][2C][2C][3C] C1223
C1CPCC[4C]1[2C][2C][1C][3C] C2213
""")

class TestIsotopes(MCSTestCase):
    # C1C[0N]CC[5C]1[1C][2C][2C][3C] C1223
    # C1CPCC[4C]1[2C][2C][1C][3C] C2213
    def test_without_isotope(self):
        # The entire system, except the N/P in the ring
        self.assert_search(isotope_mols, num_atoms=9, num_bonds=8)

    def test_isotopes(self):
        # 5 atoms of class '0' in the ring
        self.assert_search(isotope_mols, 5, 4, atom_compare="isotopes")

    def test_isotope_complete_ring_only(self):
        # the 122 in the chain
        self.assert_search(isotope_mols, 3, 2, atom_compare="isotopes", complete_rings_only=True)

bondtype_mols = load_smiles("""
C1CCCCC1OC#CC#CC#CC#CC#CC first
c1ccccc1ONCCCCCCCCCC second
""")

class TestBondTypes(MCSTestCase):
    # C1CCCCC1OC#CC#CC#CC#CC#CC 
    # c1ccccc1ONCCCCCCCCCC second
    def test_bond_compare_default(self):
        # Match the 'CCCCCC' part of the first ring, with the second's tail
        self.assert_search(bondtype_mols, 6, 5)
    def test_bond_compare_bondtypes(self):
        # Repeat of the previous
        self.assert_search(bondtype_mols, 6, 5, bond_compare="bondtypes")

    def test_bond_compare_any(self):
        # the CC#CC chain matches the CCCC tail
        self.assert_search(bondtype_mols, 10, 9, bond_compare="any")
        
    def test_atom_compare_elements_bond_compare_any(self):
        self.assert_search(bondtype_mols, 10, 9, atom_compare="elements", bond_compare="any")

    def test_atom_compare_any_bond_compare_any(self):
        # complete match!
        self.assert_search(bondtype_mols, 18, 18, atom_compare="any", bond_compare="any")

valence_mols = load_smiles("""
CCCCCCCCN
CCC[CH-]CCCC
""")
class TestValences(MCSTestCase):
    def test_valence_compare_default(self):
        # match 'CCCCCCCC'
        self.assert_search(valence_mols, 8, 7)
    def test_valence_compare_valence(self):
        # match 'CCCC'
        self.assert_search(valence_mols, 4, 3, match_valences=True)
    def test_valence_compare_valence(self):
        # match 'CCCCN' to '[CH-]CCCC' (but in reverse)
        self.assert_search(valence_mols, 5, 4, match_valences=True, atom_compare="any")
    
        


ring_mols = load_smiles("""
C12CCCC(N2)CCCC1 6-and-7-bridge-rings-with-N
C1CCCCN1 6-ring
C1CCCCCN1 7-ring
C1CCCCCCCC1 9-ring
NC1CCCCCC1 N+7-ring
C1CC1CCCCCC 3-ring-with-tail
C12CCCC(O2)CCCC1 6-and-7-bridge-rings-with-O
""")


def SELECT(mols, *offsets):
    return [mols[offset-1] for offset in offsets]

class TestRingMatchesRingOnly(MCSTestCase):
    # C12CCCC(N2)CCCC1 6-and-7-bridge-rings-with-N
    # C1CCCCN1 6-ring
    # C1CCCCCN1 7-ring
    # C1CCCCCCCC1 9-ring
    # NC1CCCCCC1 N+7-ring
    # C1CC1CCCCCC 3-ring-with-tail
    # C12CCCC(O2)CCCC1 6-and-7-bridge-rings-with-O
    def test_default(self):
        # Should match 'CCCCC'
        self.assert_search(ring_mols, 5, 4)
    def test_ring_only(self):
        # Should match "CCC"
        self.assert_search(ring_mols, 3, 2, ring_matches_ring_only=True)
    def test_ring_only_select_1_2(self):
        # Should match "C1CCCCCN1"
        self.assert_search(SELECT(ring_mols, 1, 2), 6, 6, ring_matches_ring_only=True)
    def test_ring_only_select_1_3(self):
        # Should match "C1CCCCCCN1"
        self.assert_search(SELECT(ring_mols, 1, 3), 7, 7, ring_matches_ring_only=True)
    def test_ring_only_select_1_4(self):
        # Should match "C1CCCCCCCC1"
        self.assert_search(SELECT(ring_mols, 1, 4), 9, 9, ring_matches_ring_only=True)
    def test_select_1_5(self):
        # Should match "NCCCCCC"
        self.assert_search(SELECT(ring_mols, 1, 5), 8, 7, ring_matches_ring_only=False)
    def test_ring_only_select_1_5(self):
        # Should match "CCCCCC"
        self.assert_search(SELECT(ring_mols, 1, 5), 7, 6, ring_matches_ring_only=True)
    def test_select_1_6(self):
        # Should match "CCCCCCCCC" by breaking one of the 3-carbon ring bonds
        self.assert_search(SELECT(ring_mols, 1, 6), 9, 8)
    def test_ring_only_select_1_6(self):
        # Should match "CCC" from the three atom ring
        self.assert_search(SELECT(ring_mols, 1, 6), 3, 2, ring_matches_ring_only=True)
    def test_ring_only_select_1_7(self):
        # Should match the outer ring "C1CCCCCCCC1"
        self.assert_search(SELECT(ring_mols, 1, 7), 9, 9)
    def test_ring_only_select_1_7_any_atoms(self):
        # Should match everything
        self.assert_search(SELECT(ring_mols, 1, 7), 10, 11, ring_matches_ring_only=True, atom_compare="any")

class TestCompleteRingsOnly(MCSTestCase):
    # C12CCCC(N2)CCCC1 6-and-7-bridge-rings-with-N
    # C1CCCCN1 6-ring
    # C1CCCCCN1 7-ring
    # C1CCCCCCCC1 9-ring
    # NC1CCCCCC1 N+7-ring
    # C1CC1CCCCCC 3-ring-with-tail
    # C12CCCC(O2)CCCC1 6-and-7-bridge-rings-with-O
    def test_ring_only(self):
        # No match: "CCC" is not in a ring
        self.assert_search(ring_mols, -1, -1, complete_rings_only=True)
    def test_ring_only_select_1_2(self):
        # Should match "C1CCCCCN1"
        self.assert_search(SELECT(ring_mols, 1, 2), 6, 6, complete_rings_only=True)
    def test_ring_only_select_1_3(self):
        # Should match "C1CCCCCCN1"
        self.assert_search(SELECT(ring_mols, 1, 3), 7, 7, complete_rings_only=True)
    def test_ring_only_select_1_4(self):
        # Should match "C1CCCCCCCC1"
        self.assert_search(SELECT(ring_mols, 1, 4), 9, 9, complete_rings_only=True)
    def test_ring_only_select_1_5(self):
        # No match: "CCCCCC" is not in a ring
        self.assert_search(SELECT(ring_mols, 1, 5), -1, -1, complete_rings_only=True)
    def test_ring_only_select_1_7(self):
        # Should match the outer ring "C1CCCCCCCC1"
        self.assert_search(SELECT(ring_mols, 1, 7), 9, 9, complete_rings_only=True)
    def test_ring_only_select_1_7_any_atoms(self):
        # Should match everything
        self.assert_search(SELECT(ring_mols, 1, 7), 10, 11, complete_rings_only=True, atom_compare="any")

    def test_ring_to_nonring_bond(self):
        # Should allow the cO in phenol to match the CO in the other structure
        self.assert_search(atomtype_mols, 2, 1, complete_rings_only=True)

lengthy_mols = load_smiles("""
N1(C(c2c(cc3c(c2)OCO3)CC1)c4cc(c(c(c4)OC)O)OC)C(=O)OC CHEMBL311765
N1(C(c2c(cc(cc2)O)CC1)c3ccc(cc3)OCCN4CCCC4)C(=O)OCC CHEMBL94080
""")

class TestTimeout(MCSTestCase):
    ## ### This test not longer times out. Need to find a new test case.
    ## # this should take 12+ seconds to process. Give it 0.1 seconds.
    ## def test_timeout(self):
    ##     t1 = time.time()
    ##     result = MCS.FindMCS(lengthy_mols, timeout=0.1)
    ##     self.assert_result(result, completed=0, num_atoms=-1, num_bonds=-1)
    ##     t2 = time.time()
    ##     self.assertTrue(t2-t1 < 0.5, t2-t1)

    # Check for non-negative values
    def test_timeout_negative(self):
        try:
            MCS.FindMCS(lengthy_mols, timeout=-1)
        except ValueError:
            pass
        else:
            raise AssertionError("bad range check for timeout")

if __name__ == "__main__":
    unittest.main()