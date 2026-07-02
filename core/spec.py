"""Chart spec as one JSON dict: save a figure definition, reload it later.

The spec captures what the user built (chart, columns, styling) - the
PyGWalker/Graphic Walker pattern - and is the foundation for Phase 5's
export-as-Python.
"""

import json

# widget-state keys that belong in a spec
_CFG_KEYS = ("cfg_width", "cfg_height", "cfg_dpi", "cfg_font",
             "cfg_grid", "cfg_legend", "style_preset")


def build_spec(session, plot_id: str, params: dict) -> str:
    cfg = session["plot_config"]
    return json.dumps({
        "version": 1,
        "plot_id": plot_id,
        "params": params,
        "config": cfg.to_dict(),
        "widgets": {k: session[k] for k in _CFG_KEYS if k in session},
    }, indent=2, default=str)


def apply_spec(session, spec: dict) -> None:
    """Write a parsed spec into session state (call before widgets render)."""
    if spec.get("version") != 1:
        raise ValueError("unsupported spec version")
    plot_id = spec["plot_id"]
    for k, v in spec.get("widgets", {}).items():
        session[k] = v
    for k, v in spec.get("config", {}).items():
        if hasattr(session["plot_config"], k):
            setattr(session["plot_config"], k,
                    tuple(v) if k == "figsize" else v)
    session["sel_category"], session["sel_plot"] = plot_id.split(".")
    for param, value in spec.get("params", {}).items():
        key = (f"ms_{plot_id}_{param}" if isinstance(value, list)
               else f"sb_{plot_id}_{param}")
        session[key] = value
    session["_applied_preset"] = session.get("style_preset", "Default")
