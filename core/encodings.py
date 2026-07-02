"""Which column kinds each chart slot accepts (Tableau/Metabase pattern).

The UI offers only valid columns per slot, so invalid states (a text
column on a heatmap) can't be selected instead of being error-handled.
"""

ENCODINGS = {
    "temporal.line": {"x_column": ("temporal", "numeric"), "y_columns": ("numeric",)},
    "categorical.bar": {"x_column": ("categorical", "temporal"), "y_columns": ("numeric",)},
    "statistical.scatter": {"x_column": ("numeric",), "y_column": ("numeric",)},
    "statistical.histogram": {"value_column": ("numeric",)},
    "statistical.boxplot": {"value_columns": ("numeric",)},
    "statistical.heatmap": {"value_columns": ("numeric",)},
}
GROUP_BY_TAGS = ("categorical",)  # histogram's optional group column


def valid_columns(source, plot_id: str, param: str) -> list:
    allowed = ENCODINGS.get(plot_id, {}).get(param)
    if not allowed:
        return source.columns
    return [c for c in source.columns if source.tags.get(c) in allowed]


def applicable(source, plot_id: str) -> bool:
    """A chart applies when every required slot has at least one column."""
    return all(valid_columns(source, plot_id, p)
               for p in ENCODINGS.get(plot_id, {}))
