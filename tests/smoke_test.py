"""Minimal install-from-artifact smoke test.

Run against a built wheel/sdist (not via pytest) to confirm the package imports
and exposes its public API, e.g.:

    uv run --isolated --no-project --with dist/*.whl tests/smoke_test.py
"""

from mpbc_vyfa_sf import LaserState, MPBAmplifier

assert MPBAmplifier is not None
assert LaserState.BOOSTER_ON == 52

print("smoke test ok")
