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

def column_ratio(ds, new_col, dividend, divisor):
    return divide(ds, new_col, dividend, divisor)

def add(ds, new_col, addend_1, addend_2):
    rc = ds
    rc[new_col] = ds[addend_1] + ds[addend_2]
    return rc

def subtract(ds, new_col, minuend, subtrahend):
    rc = ds
    rc[new_col] = ds[minuend] - ds[subtrahend]
    return rc

def multiply(ds, new_col, multiplicand_1, multiplicand_2):
    rc = ds
    rc[new_col] = ds[multiplicand_1] * ds[multiplicand_2]
    return rc

def total_column_sum(ds, new_col):
    rc = ds
    rc[new_col] = ds.sum(axis=1)
    return rc

def aggregation(ds, new_col, source, operation):
    if operation != 'sum':
        raise Exception(f'Aggregating with {operation} is not supported')
    rc = ds
    rc[new_col] = ds[source].sum()
    return rc

def running_total(ds, new_col, source):
    rc = ds
    rc[new_col] = ds[source].cumsum()
    return rc

def ratio_of_total(ds, new_col, source):
    rc = ds
    rc[new_col] = ds[source] / ds[source].sum()
    return rc

def datediff(ds, new_col, end, beginning, increment):
    if increment == 'day': inc = 'D'
    elif increment == 'week': inc = 'W'
    elif increment == 'month': inc = 'M'
    elif increment == 'year': inc = 'Y'

    rc = ds
    rc[new_col] = rc[end] - rc[beginning]
    rc[new_col] = rc[new_col] / numpy.timedelta64(1, inc)
    rc[new_col] = rc[new_col].apply(numpy.floor)
    return rc

def remove_columns(ds, columns):
    cols_to_drop = [c for c in columns if c in ds]
    rc = ds.drop(columns=cols_to_drop, errors='ignore')
    return rc

def reorder_columns(ds, columns):
    rc = ds[[o for o in columns if o in ds.columns] + [c for c in ds.columns if c not in columns]]
    return rc

def rename_columns(ds, map):
    rc = ds.rename(columns=map)
    return rc

def transpose(ds):
    new_index = ds.columns[0]
    rc = ds.set_index(new_index).transpose().reindex()
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
