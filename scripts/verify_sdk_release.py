from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TS_PACKAGE_DIR = REPO_ROOT / "packages" / "sdk-typescript"
PY_PACKAGE_DIR = REPO_ROOT / "packages" / "sdk-python"


def run(command: list[str], *, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    print(f"$ {' '.join(command)}", flush=True)
    return subprocess.run(command, cwd=cwd, check=True, text=True)


def fail(message: str) -> None:
    raise SystemExit(f"SDK release verification failed: {message}")


def verify_typescript_metadata() -> None:
    package_json = json.loads((TS_PACKAGE_DIR / "package.json").read_text())
    required_fields = {
        "name": "@afrolete/sdk",
        "version": "0.1.0",
        "main": "./dist/index.js",
        "types": "./dist/index.d.ts",
    }
    for key, expected in required_fields.items():
        if package_json.get(key) != expected:
            fail(f"TypeScript package field {key!r} expected {expected!r}, got {package_json.get(key)!r}")
    if "dist" not in package_json.get("files", []):
        fail("TypeScript package must publish dist/")


def verify_python_metadata() -> None:
    pyproject = tomllib.loads((PY_PACKAGE_DIR / "pyproject.toml").read_text())
    project = pyproject["project"]
    if project.get("name") != "afrolete-sdk":
        fail("Python package name must be afrolete-sdk")
    if project.get("version") != "0.1.0":
        fail("Python package version must match the current release train")
    package_data = pyproject.get("tool", {}).get("setuptools", {}).get("package-data", {})
    if "py.typed" not in package_data.get("afrolete_sdk", []):
        fail("Python package must include the PEP 561 py.typed marker")
    if not (PY_PACKAGE_DIR / "src" / "afrolete_sdk" / "py.typed").exists():
        fail("Python py.typed marker is missing")


def clean_python_build_metadata() -> None:
    for path in (PY_PACKAGE_DIR / "src").glob("*.egg-info"):
        shutil.rmtree(path)


def verify_typescript_pack(out_dir: Path | None = None) -> None:
    verify_typescript_metadata()
    run(["pnpm", "--filter", "@afrolete/sdk", "build"])
    if out_dir is None:
        with tempfile.TemporaryDirectory() as temp_dir:
            verify_typescript_pack(Path(temp_dir))
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    for existing in out_dir.glob("*.tgz"):
        existing.unlink()
    run(["npm", "pack", "--pack-destination", str(out_dir)], cwd=TS_PACKAGE_DIR)
    packages = sorted(out_dir.glob("*.tgz"))
    if len(packages) != 1:
        fail("TypeScript npm pack did not produce exactly one tarball")
    with tarfile.open(packages[0]) as archive:
        names = set(archive.getnames())
    for required in {
        "package/package.json",
        "package/README.md",
        "package/dist/index.js",
        "package/dist/index.d.ts",
    }:
        if required not in names:
            fail(f"TypeScript npm tarball is missing {required}")


def verify_python_build(out_dir: Path | None = None) -> None:
    verify_python_metadata()
    clean_python_build_metadata()
    run([sys.executable, "-m", "compileall", str(PY_PACKAGE_DIR / "src" / "afrolete_sdk")])
    if out_dir is None:
        with tempfile.TemporaryDirectory() as temp_dir:
            verify_python_build(Path(temp_dir))
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    for pattern in ("*.whl", "*.tar.gz"):
        for existing in out_dir.glob(pattern):
            existing.unlink()
    try:
        run(["uv", "build", str(PY_PACKAGE_DIR), "--out-dir", str(out_dir)])
    finally:
        clean_python_build_metadata()
    artifacts = sorted(out_dir.iterdir())
    wheel_files = [path for path in artifacts if path.suffix == ".whl"]
    sdist_files = [path for path in artifacts if path.suffixes[-2:] == [".tar", ".gz"]]
    if len(wheel_files) != 1 or len(sdist_files) != 1:
        fail("Python build must produce one wheel and one source distribution")
    with zipfile.ZipFile(wheel_files[0]) as wheel:
        wheel_names = set(wheel.namelist())
    for required in {
        "afrolete_sdk/__init__.py",
        "afrolete_sdk/client.py",
        "afrolete_sdk/types.py",
        "afrolete_sdk/py.typed",
    }:
        if required not in wheel_names:
            fail(f"Python wheel is missing {required}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and verify AfroLete SDK release artifacts.")
    parser.add_argument("--out-dir", default=None, help="Optional directory for durable release artifacts.")
    args = parser.parse_args()
    out_dir = Path(args.out_dir).resolve() if args.out_dir else None
    verify_typescript_pack(out_dir)
    verify_python_build(out_dir)
    print("SDK release verification passed.")


if __name__ == "__main__":
    main()
