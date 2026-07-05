"""Adapters — the impure edges around the pure core.

Each subpackage bridges the deterministic domain to the outside world:
``persist`` (SQLite), later ``render`` (Textual/Rich) and ``rlenv`` (Gymnasium).
Adapters may depend on the domain; the domain never depends on them.
"""
