"""Load the pinned Python rule engine reused by the official reader."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


REPOSITORY = Path(__file__).resolve().parents[3]
LEGACY_READER = REPOSITORY / "experimental" / "modular-candidate-1" / "readers" / "python"


def load(name, filename):
    """Load one legacy Python module under a private, stable module name."""
    if name in sys.modules:
        return sys.modules[name]
    spec = spec_from_file_location(name, LEGACY_READER / filename)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load reused Python module {filename}")
    module = module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
