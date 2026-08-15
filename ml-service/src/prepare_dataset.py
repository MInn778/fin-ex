"""Normalize phishing/benign source files and split without domain leakage."""

from __future__ import annotations

import argparse
import bz2
import hashlib
import json
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from .domain_rules import registered_domain


def _host(url: str) -> str:
    value = url.strip()
    parsed = urlsplit(value if "://" in value else f"http://{value}")
    return (parsed.hostname or "").lower()


def _read_phishtank(path: Path) -> pd.DataFrame:
    opener = bz2.open if path.suffix == ".bz2" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        frame = pd.read_csv(stream)
    if {"verified", "online"}.issubset(frame.columns):
        frame = frame[
            frame["verified"].astype(str).str.lower().eq("yes")
            & frame["online"].astype(str).str.lower().eq("yes")
        ]
    result = frame[["url"]].copy()
    result["label"], result["source"] = 1, "phishtank"
    return result


def _read_tranco(path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(path) as archive:
        with archive.open(archive.namelist()[0]) as stream:
            frame = pd.read_csv(stream, names=["rank", "domain"])
    result = pd.DataFrame({"url": "https://" + frame["domain"].astype(str).str.lower() + "/"})
    result["label"], result["source"] = 0, "tranco"
    return result


def _clean(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.dropna(subset=["url", "label"]).copy()
    result["url"] = result["url"].astype(str).str.strip()
    result = result[result["url"].str.len().between(4, 4096)].drop_duplicates("url")
    result["registered_domain"] = result["url"].map(lambda value: registered_domain(_host(value)))
    return result[result["registered_domain"].ne("")].reset_index(drop=True)


def _split(frame: pd.DataFrame, seed: int) -> dict[str, pd.DataFrame]:
    first = GroupShuffleSplit(n_splits=1, test_size=0.30, random_state=seed)
    train_index, holdout_index = next(first.split(frame, frame["label"], groups=frame["registered_domain"]))
    train, holdout = frame.iloc[train_index], frame.iloc[holdout_index]
    second = GroupShuffleSplit(n_splits=1, test_size=0.50, random_state=seed)
    validation_index, test_index = next(
        second.split(holdout, holdout["label"], groups=holdout["registered_domain"])
    )
    return {"train": train, "validation": holdout.iloc[validation_index], "test": holdout.iloc[test_index]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phishtank", type=Path, required=True)
    parser.add_argument("--tranco", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/processed"))
    parser.add_argument("--per-class", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    positive, negative = _clean(_read_phishtank(args.phishtank)), _clean(_read_tranco(args.tranco))
    count = min(args.per_class, len(positive), len(negative))
    dataset = pd.concat([
        positive.sample(count, random_state=args.seed),
        negative.sample(count, random_state=args.seed),
    ], ignore_index=True).sample(frac=1, random_state=args.seed).reset_index(drop=True)

    args.output.mkdir(parents=True, exist_ok=True)
    manifest = {"seed": args.seed, "per_class": count, "splits": {}}
    for name, split in _split(dataset, args.seed).items():
        output = args.output / f"{name}.csv"
        split.to_csv(output, index=False, encoding="utf-8")
        digest = hashlib.sha256(output.read_bytes()).hexdigest()
        manifest["splits"][name] = {"rows": len(split), "sha256": digest}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
