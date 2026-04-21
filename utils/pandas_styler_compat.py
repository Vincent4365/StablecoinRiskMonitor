from __future__ import annotations

from typing import Any, Callable


def styler_cell_map(styler: Any, func: Callable[..., Any], *, subset: Any = None) -> Any:
    """Apply a cell-wise style function across a subset.

    Pandas deprecated `Styler.applymap` in favor of `Styler.map` and removed
    `applymap` in pandas 3.0. Streamlit Cloud currently uses pandas 3.x.

    This helper keeps the app compatible with both older and newer pandas.
    """

    styler_map = getattr(styler, "map", None)
    if callable(styler_map):
        # pandas >= 2.1 (and 3.x)
        return styler_map(func, subset=subset)

    styler_applymap = getattr(styler, "applymap", None)
    if callable(styler_applymap):
        # pandas < 3.0
        return styler_applymap(func, subset=subset)

    raise AttributeError("Pandas Styler has neither 'map' nor 'applymap'.")
