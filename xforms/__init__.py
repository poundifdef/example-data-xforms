import numpy
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

def format(x, pos):
    m = 0
    while abs(x) >= 1000:
        m += 1
        x = x/1000.0
    return "%.2f%s" % (x, ["", "K", "M", "B", "T"][m])

number_formatter = FuncFormatter(format)

def hello():
    return "hello"

def divide(ds, new_col, dividend, divisor):
    rc = ds
    rc[new_col] = ds[dividend] / ds[divisor]
    return rc

def remove_columns(ds, columns):
    cols_to_drop = [c for c in columns if c in ds]
    rc = ds.drop(columns=cols_to_drop, errors='ignore')
    return rc

def reorder_columns(ds, columns):
    rc = ds[[o for o in columns if o in ds.columns] + [c for c in ds.columns if c not in columns]]
    return rc

def line(ds):
    # Ensure the default "index" column is not part of the plot\n'
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
