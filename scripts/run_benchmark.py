import sys
from pathlib import Path


def main() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from app.evaluation.evaluator import main as run_benchmark

    run_benchmark()


if __name__ == "__main__":
    main()
