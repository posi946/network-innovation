import json
import math
import random
from typing import List, Sequence, Tuple


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _matvec(mat: Sequence[Sequence[float]], vec: Sequence[float]) -> List[float]:
    return [_dot(row, vec) for row in mat]


def _add(a: Sequence[float], b: Sequence[float]) -> List[float]:
    return [x + y for x, y in zip(a, b)]


def _relu(x: List[float]) -> List[float]:
    return [v if v > 0 else 0.0 for v in x]


def _relu_grad(x: List[float]) -> List[float]:
    return [1.0 if v > 0 else 0.0 for v in x]


def _softmax(logits: List[float]) -> List[float]:
    m = max(logits)
    exps = [math.exp(v - m) for v in logits]
    s = sum(exps)
    return [e / s for e in exps]


def _cross_entropy(probs: List[float], target_index: int) -> float:
    p = min(max(probs[target_index], 1e-12), 1.0)
    return -math.log(p)


class NeuralNetwork:
    """A small feedforward neural network implemented from scratch.

    Architecture: input -> hidden (ReLU) -> output (softmax)
    """

    def __init__(self, input_size: int, hidden_size: int, output_size: int, seed: int = 42):
        rng = random.Random(seed)
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size

        # He-like init for ReLU hidden layer
        h_scale = math.sqrt(2.0 / max(1, input_size))
        o_scale = math.sqrt(1.0 / max(1, hidden_size))
        self.W1 = [[rng.gauss(0, h_scale) for _ in range(input_size)] for _ in range(hidden_size)]
        self.b1 = [0.0 for _ in range(hidden_size)]
        self.W2 = [[rng.gauss(0, o_scale) for _ in range(hidden_size)] for _ in range(output_size)]
        self.b2 = [0.0 for _ in range(output_size)]

    def forward(self, x: Sequence[float]) -> Tuple[List[float], List[float], List[float], List[float]]:
        z1 = _add(_matvec(self.W1, x), self.b1)
        a1 = _relu(z1)
        z2 = _add(_matvec(self.W2, a1), self.b2)
        probs = _softmax(z2)
        return z1, a1, z2, probs

    def predict_proba(self, x: Sequence[float]) -> List[float]:
        _, _, _, probs = self.forward(x)
        return probs

    def predict(self, x: Sequence[float]) -> int:
        probs = self.predict_proba(x)
        return max(range(len(probs)), key=lambda i: probs[i])

    def train(
        self,
        X: List[List[float]],
        y: List[int],
        epochs: int = 300,
        learning_rate: float = 0.05,
        verbose_every: int = 50,
    ) -> List[float]:
        history = []
        n = len(X)
        for epoch in range(1, epochs + 1):
            total_loss = 0.0
            correct = 0
            for x, target in zip(X, y):
                z1, a1, _, probs = self.forward(x)
                loss = _cross_entropy(probs, target)
                total_loss += loss
                pred = max(range(len(probs)), key=lambda i: probs[i])
                if pred == target:
                    correct += 1

                # Output layer gradient: dL/dz2 = probs - one_hot(target)
                dz2 = list(probs)
                dz2[target] -= 1.0

                # Gradients for W2, b2
                dW2 = [[dz2[i] * a1[j] for j in range(self.hidden_size)] for i in range(self.output_size)]
                db2 = list(dz2)

                # Backprop into hidden layer
                da1 = [0.0 for _ in range(self.hidden_size)]
                for j in range(self.hidden_size):
                    s = 0.0
                    for i in range(self.output_size):
                        s += self.W2[i][j] * dz2[i]
                    da1[j] = s
                rz1 = _relu_grad(z1)
                dz1 = [da1[j] * rz1[j] for j in range(self.hidden_size)]

                # Gradients for W1, b1
                dW1 = [[dz1[j] * x[k] for k in range(self.input_size)] for j in range(self.hidden_size)]
                db1 = list(dz1)

                # SGD update
                for i in range(self.output_size):
                    for j in range(self.hidden_size):
                        self.W2[i][j] -= learning_rate * dW2[i][j]
                    self.b2[i] -= learning_rate * db2[i]
                for j in range(self.hidden_size):
                    for k in range(self.input_size):
                        self.W1[j][k] -= learning_rate * dW1[j][k]
                    self.b1[j] -= learning_rate * db1[j]

            avg_loss = total_loss / max(1, n)
            acc = correct / max(1, n)
            history.append(avg_loss)
            if verbose_every and (epoch % verbose_every == 0 or epoch == 1):
                print(f"Epoch {epoch:4d}/{epochs} - loss: {avg_loss:.4f} - acc: {acc:.3f}")
        return history

    def evaluate(self, X: List[List[float]], y: List[int]) -> float:
        correct = 0
        for x, target in zip(X, y):
            if self.predict(x) == target:
                correct += 1
        return correct / max(1, len(X))

    def save(self, path: str) -> None:
        payload = {
            "input_size": self.input_size,
            "hidden_size": self.hidden_size,
            "output_size": self.output_size,
            "W1": self.W1,
            "b1": self.b1,
            "W2": self.W2,
            "b2": self.b2,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f)

    @classmethod
    def load(cls, path: str) -> "NeuralNetwork":
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        net = cls(payload["input_size"], payload["hidden_size"], payload["output_size"])
        net.W1 = payload["W1"]
        net.b1 = payload["b1"]
        net.W2 = payload["W2"]
        net.b2 = payload["b2"]
        return net
