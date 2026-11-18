import os
import tempfile
import unittest

from plantguard.assistant import generate_report
from plantguard.data import LABELS, make_dataset, normalize_features, train_test_split
from plantguard.model import NeuralNetwork


class PlantGuardTests(unittest.TestCase):
    def test_training_improves_or_learns(self):
        X_raw, y = make_dataset(600, seed=1)
        X = normalize_features(X_raw)
        X_train, y_train, X_test, y_test = train_test_split(X, y, test_ratio=0.2, seed=1)
        model = NeuralNetwork(input_size=4, hidden_size=10, output_size=len(LABELS), seed=1)
        model.train(X_train, y_train, epochs=120, learning_rate=0.07, verbose_every=0)
        acc = model.evaluate(X_test, y_test)
        self.assertGreater(acc, 0.55)

    def test_save_load_and_report(self):
        X_raw, y = make_dataset(300, seed=2)
        X = normalize_features(X_raw)
        model = NeuralNetwork(input_size=4, hidden_size=8, output_size=len(LABELS), seed=2)
        model.train(X, y, epochs=80, learning_rate=0.07, verbose_every=0)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "w.json")
            model.save(path)
            loaded = NeuralNetwork.load(path)
        probs = loaded.predict_proba(normalize_features([[55, 24, 60, 50]])[0])
        self.assertEqual(len(probs), len(LABELS))
        self.assertAlmostEqual(sum(probs), 1.0, places=5)
        report = generate_report([55, 24, 60, 50], probs)
        self.assertIn("Predicted status", report)
        self.assertIn("Recommended actions", report)


if __name__ == "__main__":
    unittest.main()
