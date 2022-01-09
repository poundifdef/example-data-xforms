import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import plotly.graph_objects as go


def format(x, pos):
    m = 0
    while abs(x) >= 1000:
        m += 1
        x = x / 1000.0
    return "%.2f%s" % (x, ["", "K", "M", "B", "T"][m])


number_formatter = FuncFormatter(format)


def transpose(ds):
    new_index = ds.columns[0]
    rc = ds.set_index(new_index).transpose().reindex()
    return rc


def column_ratio_new(ds, new_col, dividend, divisor):
    return divide(ds, new_col, dividend, divisor)


def subtract_new(ds, new_col, minuend, subtrahend):
    rc = ds
    rc[new_col] = ds[minuend] - ds[subtrahend]
    return rc


def multiply_new(ds, new_col, multiplicand_1, multiplicand_2):
    rc = ds
    rc[new_col] = ds[multiplicand_1] * ds[multiplicand_2]
    return rc


def add_new(ds, new_col, addend_1, addend_2):
    rc = ds
    rc[new_col] = ds[addend_1] + ds[addend_2]
    return rc


def divide_new(ds, new_col, dividend, divisor):
    rc = ds
    rc[new_col] = ds[dividend] / ds[divisor]
    return rc


def total_column_sum_new(ds, new_col):
    rc = ds
    rc[new_col] = ds.sum(axis=1)
    return rc


def aggregation_new(ds, new_col, source, operation):
    if operation != "sum":
        raise Exception(f"Aggregating with {operation} is not supported")
    rc = ds
    rc[new_col] = ds[source].sum()
    return rc


def running_total_new(ds, new_col, source):
    rc = ds
    rc[new_col] = ds[source].cumsum()
    return rc


def ratio_of_total_new(ds, new_col, source):
    rc = ds
    rc[new_col] = ds[source] / ds[source].sum()
    return rc


def datediff_new(ds, new_col, start, end, increment):
    if increment == "day":
        inc = "D"
    elif increment == "week":
        inc = "W"
    elif increment == "month":
        inc = "M"
    elif increment == "year":
        inc = "Y"

    rc = ds
    rc[new_col] = rc[end] - rc[start]
    rc[new_col] = rc[new_col] / np.timedelta64(1, inc)
    rc[new_col] = rc[new_col].apply(np.floor)
    return rc


def substr_new(ds, new_col, source, start=None, end=None):
    rc = ds
    rc[new_col] = ds[source].str[start:end]
    return rc


def custom_new(ds, new_col, function):
    rc = ds
    rc[new_col] = ds.apply(function, axis=1, result_type="reduce")
    return rc


def case_statement_new(
    ds, new_col, source, conditions, default, default_type="LITERAL"
):
    rc = ds

    if default_type == "COLUMN":
        rc[new_col] = rc[default]
    else:
        rc[new_col] = default

    for condition in conditions:
        value = condition["value"]
        value_type = condition["value_type"]
        operand = condition["operand"]
        operator = condition["operator"]

        if value_type == "COLUMN":
            value = rc[value]

        # determine the operand type

        if operator == "LIKE":
            # None of the LIKE operators in the data have percent signs
            operator = "="

        # the data doesn't contain NOT LIKE

        # TODO: determine whether values should be compared using int or str

        if operator in ["=", "!=", ">", ">=", "<", "<="]:
            fn = {
                "=": "eq",
                "!=": "ne",
                ">": "gt",
                ">=": "ge",
                "<": "lt",
                "<=": "le",
            }
            f = getattr(rc[source], fn[operator])
            rc.loc[f(operand), new_col] = value

        elif operator == "IS NOT" and operand == "null":
            rc.loc[pd.notnull(rc[source]), new_col] = value

        elif operator == "IS" and operand == "null":
            rc.loc[pd.isnull(rc[source]), new_col] = value

        elif operator == "IS" and operand == "''":
            rc.loc[rc[source] == "", new_col] = value

        else:
            raise Exception(f"{operator} is not supported")

    return rc


def add(ds, col, addend):
    return add_new(ds, col, col, addend)


def multiply(ds, col, multiplicand):
    return multiply_new(ds, col, col, multiplicand)


def divide(ds, col, divisor):
    return divide_new(ds, col, col, divisor)


def round(ds, col, places):
    rc = ds
    rc[col] = ds[col].round(places)
    return rc


def substr(ds, col, start=None, end=None):
    return substr_new(ds, col, col, start, end)


def format(ds, col, arg):
    if arg != 0:
        raise Exception(f"edit_column_format does not work for non-zero args {arg}")
    rc = ds
    rc[col] = ds[col].apply(np.floor)
    return rc


def custom(ds, col, function):
    return custom_new(ds, col, function)


def combine_columns(
    ds, new_col, columns, separator=",", operator="concatenate", hide_columns=False
):
    rc = ds

    if operator == "concatenate":
        for col in columns:
            rc[col] = rc[col].astype(str)
        rc[new_col] = rc[columns].agg(separator.join, axis=1)

    elif operator in ("add", "subtract", "multiply"):
        cols = [ds[col] for col in columns]
        rc[new_col] = cols[0]
        for col in cols[1:]:
            if operator == "add":
                rc[new_col] = rc[new_col].add(col)
            elif operator == "subtract":
                rc[new_col] = rc[new_col].sub(col)
            elif operator == "multiply":
                rc[new_col] = rc[new_col].multiply(col)

    else:
        raise Exception(operator + " is unsupported")

    if hide_columns:
        rc = ds.drop(columns, errors="ignore")

    return rc


# use_three_columns is not implemented
def unpivot(ds, group_alias, values_alias):
    rc = ds.transpose().reset_index()
    rc.rename(columns={"index": group_alias, 0: values_alias}, inplace=True)
    return rc


def zero_fill(ds, column_types):
    rc = ds

    col_1_name = ds.columns[0]
    col_1_type = column_types[col_1_name]

    if col_1_type in ("text", "real"):
        # Do nothing for this zero_fill since the
        # first column is a string or real number
        pass

    elif col_1_type == "date":
        # Do something for this zero_fill since the first column is a date
        col_1 = rc[col_1_name]
        date_range = pd.date_range(col_1.min(), col_1.max(), freq="d")
        diff = date_range.difference(col_1).to_frame()
        diff.rename(columns={0: col_1_name}, inplace=True)
        rc = rc.append(diff, ignore_index=True)
        rc = rc.sort_values(col_1_name)

    else:
        raise Exception("unsupported zero_fill column type " + col_1_type)

    for col_name in ds.columns:
        type = column_types.get(col_name)
        if type in ("integer", "real"):
            rc[col_name].fillna(0, inplace=True)

    return rc


def rename_columns(ds, map):
    rc = ds.rename(columns=map)
    return rc


def remove_columns(ds, columns):
    cols_to_drop = [c for c in columns if c in ds]
    rc = ds.drop(columns=cols_to_drop, errors="ignore")
    return rc


def reorder_columns(ds, columns):
    rc = ds[
        [o for o in columns if o in ds.columns]
        + [c for c in ds.columns if c not in columns]
    ]
    return rc


def group_by(ds, columns):
    ordered = ds.columns

    # get the columns to be grouped
    grouped_cols = [c for c in columns.keys() if c in ordered]

    agg = {}
    rename = {}

    for name, action in columns.items():
        if action == "COUNT_DISTINCT":
            rename[name] = f"COUNT(DISTINCT {name})"
        else:
            rename[name] = f"{action}({name})"

        if action == "MIN":
            method = "min"
        elif action == "MAX":
            method = "max"
        elif action == "MEDIAN":
            method = "median"
        elif action == "AVG":
            method = "mean"
        elif action == "COUNT":
            method = "count"
        elif action == "SUM":
            method = "sum"
        elif action == "COUNT_DISTINCT":
            method = "nunique"
        elif action == "GROUP_CONCAT":
            agg[name] = lambda x: ", ".join(x)
            continue
        agg[name] = method

    rc = ds.groupby(grouped_cols, as_index=False).agg(agg)
    rc = rc[ordered]
    rc.rename(columns=rename, inplace=True)

    return rc


def histogram_buckets(ds, col, aggregation, bucket_type, custom_buckets):
    if aggregation != "COUNT":
        raise Exception("We only support COUNT aggregations in histograms")

    if bucket_type != "custom_buckets":
        raise Exception("We only support custom_buckets in histograms")

    bins = pd.IntervalIndex.from_breaks(custom_buckets)
    binned = pd.cut(ds[col], bins=bins)
    binned = binned.cat.rename_categories(lambda r: f"{r.left}-{r.right - 1}")
    rc = binned.groupby(binned).size().to_frame().rename_axis(0).reset_index()
    columns = {}
    columns[col] = "Bucket"
    columns[0] = "Count"
    rc.rename(columns, inplace=True)
    return rc


def filter(ds, filters, match_type="all", mode="include"):
    # filter definition
    """
    {
        "column": "col_name",
        "operator": "<=",
        "operand": "op",
        "operand_type": "COLUMN", # or "LITERAL"
    }
    """
    comparisons = []

    for f in filters:
        column = f["column"]
        operator = f["operator"]
        operand = f.get("operand")
        operand_type = f.get("operand_type", "LITERAL")

        if operand_type == "COLUMN":
            operand = ds[operand]
        else:
            if operator == "IN":
                comparisons.append(ds[column].isin(operand))
                continue

        if operator == "IS NULL":
            comparisons.append(ds[column].isnull())
            continue

        if operator == "IS NOT NULL":
            comparisons.append(ds[column] is not None)
            continue

        fn = {
            "=": "eq",
            "!=": "ne",
            ">": "gt",
            ">=": "ge",
            "<": "lt",
            "<=": "le",
        }
        if operator in fn:
            func = getattr(ds[column], fn[operator])
            comparisons.append(func(operand))
            continue

        raise Exception(f"filter operator {operator}")

    rc = comparisons[0]
    for comparison in comparisons[1:]:
        if match_type == "any":
            rc |= comparison
        else:
            rc &= comparison

    if mode == "exclude":
        rc = ~rc

    return rc


def sort(ds, columns):
    m = {1: 'True', -1: 'False'}
    sort_columns = [c['col_name'] for c in columns]
    sort_directions = [m[c['direction']] for c in columns]
    rc = ds.sort_values(sort_columns, ascending=sort_directions)
    return rc


def pivot(ds, aggregations):
    aggfuncs = {"SUM": "numpy.sum", "AVG": "numpy.average", "MAX": "numpy.max"}

    if len(aggregations) == 1:
        rc = ds.pivot_table(
            index=ds.columns[0],
            columns=ds.columns[1],
            values=ds.columns[2],
            aggfunc=aggfuncs.get(aggregations[0]),
        )
        rc = rc.fillna(0)
        rc.reset_index(level=0, inplace=True)
        rc.columns.name = ""
        return rc

    ordered_cols = list(ds.columns)
    aggfunc = {}

    for i, fn in enumerate(aggregations):
        if len(ordered_cols) <= i + 2:
            break
        col = ordered_cols[i + 2]
        aggfunc[col] = aggfuncs.get(fn)

    rc = ds.pivot_table(index=ordered_cols[0:2], aggfunc=aggfunc)
    rc = rc.unstack()
    rc = rc.reindex(columns=rc.columns.reindex(ordered_cols, level=0)[0])
    rc.columns = [f"{col[1]}:{col[0]}" for col in rc.columns.values]
    rc = rc.fillna(0)
    rc.reset_index(level=0, inplace=True)
    rc.columns.name = ""

    return rc


def _join(join_type, datasets, join_on_first_n_columns):
    rc = datasets[0]

    for i in range(1, len(datasets)):
        left_data = rc
        right_data = datasets[i]

        # Rename join columns on right-hand dataset to match left-hand names
        renamed_columns = {}
        for col_num in range(0, join_on_first_n_columns):
            renamed_columns[right_data.columns[col_num]] = left_data.columns[col_num]
        right_data_renamed = right_data.rename(columns=renamed_columns)

        rc = left_data.merge(
            right_data_renamed,
            how=join_type,
            left_on=list(left_data.columns[:join_on_first_n_columns]),
            right_on=list(right_data_renamed.columns[:join_on_first_n_columns]),
            suffixes=(None, ":1"),
        )

    return rc


def full_outer_join(datasets, join_on_first_n_columns):
    return _join("outer", datasets, join_on_first_n_columns)


def inner_join(datasets, join_on_first_n_columns):
    return _join("inner", datasets, join_on_first_n_columns)


def left_join(datasets, join_on_first_n_columns):
    return _join("left", datasets, join_on_first_n_columns)


def table(ds, column_types: dict = None, column_precision: dict = None):
    """
    Displays a table of data.

    ds: Dataset to display

    column_types: dict of the type of each column, where the key is the column
                  name and the value is the type. Types can be:

                    - percentage
                    - integer
                    - currency

    column_precision: Precision of each column. Key is the column name and
                        the value is the number of decimal places.
    """

    # Formatting is done using d3 format specifiers:
    # https://github.com/d3/d3-format/blob/main/README.md
    # Here is a tool to help test formats:
    # http://bl.ocks.org/zanarmstrong/05c1e95bf7aa16c4768e

    column_types = column_types or {}
    column_precision = column_precision or {}
    formats = []

    for col_name in ds.columns:

        col_type = column_types.get(col_name)
        precision = column_precision.get(col_name)

        if col_type == "percentage":
            precision = precision or 0
            formats.append(f",.{precision}%")
        elif col_type == "integer":
            formats.append(",.0f")
        elif col_type == "currency":
            precision = precision or 2
            formats.append(f"$,.{precision}f")
        elif col_type == "real":
            precision = precision or 2
            formats.append(f",.{precision}f")
        else:
            formats.append(None)

    fig = go.Figure(
        data=[
            go.Table(
                header=dict(values=list(ds.columns), align="left"),
                cells=dict(
                    values=[ds[c] for c in ds.columns], format=formats, align="left"
                ),
            )
        ]
    )

    fig.show()


def line(ds):
    # Ensure the default "index" column is not part of the plo'
    if type(ds.index) == pd.RangeIndex or type(ds.index) == pd.Int64Index:
        index_column = ds.columns[0]
        ds = ds.set_index(index_column)

    # Configure chart display
    fig, ax = plt.subplots()
    ax.yaxis.set_major_formatter(number_formatter)
    ds.plot.line(ax=ax)

    # Rotate x axis labels 45 degrees
    fig.autofmt_xdate()

    # Increase chart size
    fig.set_size_inches(12, 8)

    # Display chart
    plt.show()


def bar(ds, stacked=False):
    """
    Generate a bar chart from dataset. Assumes first column
    is the x axis. Any subsequent columns are new datasets.

    stacked: Display bars stacked on top of each other rather than
             side by side
    """

    barmode = "group"
    if stacked:
        barmode = "stacked"

    fig = px.bar(ds, x=ds.columns[0], y=ds.columns[1:], barmode=barmode)
    fig.show()


def single_value(ds):
    print(ds.iloc[0, 0])


def pie(ds):
    """
    Generate a pie chart from the dataset. Assumes the dataset has 2 columns,
    the first one being the name and second is the value.

    https://plotly.com/python/pie-charts/
    """

    fig = px.pie(ds, values=ds.columns[1], names=ds.columns[0])
    fig.show()


def area(ds):
    """
    Generate a stacked area chart from dataset. Assumes first column
    is the x axis. Any subsequent columns are new datasets.
    """

    fig = px.area(ds, x=ds.columns[0], y=ds.columns[1:])
    fig.show()


def bar_line(ds):
    # TODO: change stacked according to settings
    ds[ds.columns[1:-1]].plot.bar(stacked=True)
    ds[ds.columns[-1]].plot(kind="line", secondary_y=True)
    plt.show()
