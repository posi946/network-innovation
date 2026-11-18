import argparse
import os
from typing import List

from .assistant import generate_report
from .data import FEATURE_NAMES, LABELS, make_dataset, normalize_features, train_test_split
from .model import NeuralNetwork


DEFAULT_WEIGHTS = "model_weights.json"


def _parse_features(values: List[str]) -> List[float]:
    if len(values) != len(FEATURE_NAMES):
        raise ValueError(
            f"Expected {len(FEATURE_NAMES)} values in order: {', '.join(FEATURE_NAMES)}"
        )
    return [float(v) for v in values]


def cmd_train(args: argparse.Namespace) -> None:
    X_raw, y = make_dataset(args.samples, seed=args.seed)
    X = normalize_features(X_raw)
    X_train, y_train, X_test, y_test = train_test_split(X, y, test_ratio=0.2, seed=args.seed)

    model = NeuralNetwork(input_size=len(FEATURE_NAMES), hidden_size=args.hidden, output_size=len(LABELS), seed=args.seed)
    print(f"Training PlantGuard on {len(X_train)} samples ({len(X_test)} test)...")
    model.train(X_train, y_train, epochs=args.epochs, learning_rate=args.lr, verbose_every=args.verbose_every)
    acc = model.evaluate(X_test, y_test)
    print(f"Test accuracy: {acc * 100:.2f}%")
    model.save(args.weights)
    print(f"Saved model to {args.weights}")


def _load_or_train(weights_path: str) -> NeuralNetwork:
    if os.path.exists(weights_path):
        return NeuralNetwork.load(weights_path)
    print(f"No weights found at {weights_path}. Training a quick model...")
    X_raw, y = make_dataset(1200, seed=42)
    X = normalize_features(X_raw)
    X_train, y_train, X_test, y_test = train_test_split(X, y, test_ratio=0.2, seed=42)
    model = NeuralNetwork(input_size=len(FEATURE_NAMES), hidden_size=12, output_size=len(LABELS), seed=42)
    model.train(X_train, y_train, epochs=250, learning_rate=0.06, verbose_every=50)
    acc = model.evaluate(X_test, y_test)
    print(f"Quick-train test accuracy: {acc * 100:.2f}%")
    model.save(weights_path)
    return model


def cmd_predict(args: argparse.Namespace) -> None:
    model = NeuralNetwork.load(args.weights) if os.path.exists(args.weights) else _load_or_train(args.weights)
    features = _parse_features(args.values)
    norm = normalize_features([features])[0]
    probs = model.predict_proba(norm)
    print(generate_report(features, probs))


def cmd_demo(args: argparse.Namespace) -> None:
    model = _load_or_train(args.weights)
    examples = [
        [55, 24, 60, 50],   # likely healthy
        [18, 27, 65, 35],   # likely needs water
        [85, 22, 45, 60],   # likely overwatered risk
        [50, 36, 92, 25],   # likely heat/light stress
    ]
    titles = ["Balanced plant", "Dry soil", "Soggy soil", "Hot and bright"]
    for title, features in zip(titles, examples):
        norm = normalize_features([features])[0]
        probs = model.predict_proba(norm)
        print("\n" + "#" * 60)
        print(f"Example: {title}")
        print(generate_report(features, probs))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="plantguard",
        description="PlantGuard: neural plant stress diagnosis with a built-in care assistant.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_train = sub.add_parser("train", help="Train the neural network on synthetic sensor data")
    p_train.add_argument("--samples", type=int, default=2000, help="Number of synthetic samples")
    p_train.add_argument("--epochs", type=int, default=300, help="Training epochs")
    p_train.add_argument("--hidden", type=int, default=12, help="Hidden layer size")
    p_train.add_argument("--lr", type=float, default=0.06, help="Learning rate")
    p_train.add_argument("--seed", type=int, default=42, help="Random seed")
    p_train.add_argument("--weights", default=DEFAULT_WEIGHTS, help="Path to save weights")
    p_train.add_argument("--verbose-every", type=int, default=50, help="Print progress every N epochs")
    p_train.set_defaults(func=cmd_train)

    p_predict = sub.add_parser("predict", help="Predict plant status from sensor readings")
    p_predict.add_argument(
        "values",
        nargs=len(FEATURE_NAMES),
        metavar=("SOIL", "TEMP_C", "LIGHT", "HUMIDITY"),
        help="Readings in order: soil_moisture temperature_c light_level humidity",
    )
    p_predict.add_argument("--weights", default=DEFAULT_WEIGHTS, help="Path to model weights")
    p_predict.set_defaults(func=cmd_predict)

    p_demo = sub.add_parser("demo", help="Run demo predictions on sample scenarios")
    p_demo.add_argument("--weights", default=DEFAULT_WEIGHTS, help="Path to model weights")
    p_demo.set_defaults(func=cmd_demo)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
