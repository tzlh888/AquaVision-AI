"""Regenerate Phase 1 EDA from the real sample manifest; no network access."""

import argparse
import json
from pathlib import Path

from aquavision.data.eda import inspect_sample


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("data/metadata/sample_manifest.json"))
    parser.add_argument("--output", type=Path, default=Path("research_outputs"))
    args = parser.parse_args()
    print(json.dumps(inspect_sample(args.manifest, Path.cwd(), args.output), indent=2))


if __name__ == "__main__":
    main()
