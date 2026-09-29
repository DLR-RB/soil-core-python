import unittest
from soil.data import Path, Sample, Value, SampleTree, Timestamp

class TestCoreDataTypes(unittest.TestCase):

    def test_path_creation(self):
        path = Path.of("sensor", "temperature")
        
        self.assertEqual(len(path), 2)
        self.assertEqual(path[0], "sensor")
        self.assertEqual(path[1], "temperature")
        self.assertFalse(path.isEmpty)

    def test_append_to_path(self):
        base_path = Path.of("house")
        full_path = base_path.appending("room1")
        
        self.assertEqual(full_path.size, 2)
        self.assertEqual(full_path, ['house', 'room1'])

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