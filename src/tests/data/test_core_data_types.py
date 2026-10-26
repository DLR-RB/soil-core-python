import unittest

from soil.data import Sample, SampleTree, Timestamp, Value


class TestCoreDataTypes(unittest.TestCase):

    def test_sample_with_value(self):        
        value = Value(23.5)
        ts = Timestamp.current() 
        sample = Sample(value, ts)
        
        self.assertEqual(sample.value.value, 23.5)

    def test_empty_tree(self):
        empty_tree = SampleTree.empty()
        
        self.assertTrue(empty_tree.isEmpty)

    def test_non_empty_tree_has_samples(self):
        ts = Timestamp.current()
        sample = Sample(Value(100), ts)
        
        my_tree = SampleTree.create(samples=[sample])
        
        self.assertFalse(my_tree.isEmpty)
        
        self.assertEqual(len(my_tree.samples), 1)
        self.assertEqual(my_tree.samples[0].value.value, 100)

if __name__ == '__main__':
    unittest.main()