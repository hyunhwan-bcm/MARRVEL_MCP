import pickle
from pathlib import Path
import sys


def modify_pkl(path):
    p = Path(path).expanduser()
    with open(p, "rb") as f:
        data = pickle.load(f)

    print(f"Original classification: {data.get('classification')}")
    data["classification"] = "no - simulated failure"

    with open(p, "wb") as f:
        pickle.dump(data, f)
    print(f"Modified classification: {data.get('classification')}")


if __name__ == "__main__":
    modify_pkl(sys.argv[1])
