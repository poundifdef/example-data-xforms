import numpy as np
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
    if operation != 'sum':
        raise Exception(f'Aggregating with {operation} is not supported')
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
    if increment == 'day': inc = 'D'
    elif increment == 'week': inc = 'W'
    elif increment == 'month': inc = 'M'
    elif increment == 'year': inc = 'Y'

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
    rc[new_col] = ds.apply(function, axis=1, result_type='reduce')
    return rc

def case_statement_new(ds, new_col):
    pass

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
        raise Exception(f'edit_column_format does not work for non-zero args {arg}')
    rc = ds
    rc[col] = ds[col].apply(np.floor)
    return rc

def custom(ds, col, function):
    return custom_new(ds, col, function)

def combine_columns(ds, new_col, columns, separator=',', operator='concatenate', hide_columns=False):
    rc = ds

    if operator == 'concatenate':
        for col in columns:
            rc[col] = rc[col].astype(str)
        rc[new_col] = rc[columns].agg(separator.join, axis=1)
    
    elif operator in ('add', 'subtract', 'multiply'):
        cols = [ds[col] for col in columns]
        rc[new_col] = cols[0]
        for col in cols[1:]:
            if operator == 'add':
                rc[new_col] = rc[new_col].add(col)
            elif operator == 'subtract':
                rc[new_col] = rc[new_col].sub(col)
            elif operator == 'multiply':
                rc[new_col] = rc[new_col].multiply(col)

    else:
        raise Exception(operator + ' is unsupported')

    if hide_columns:
        rc = ds.drop(columns, errors='ignore')

    return rc

# use_three_columns is not implemented
def unpivot(ds, group_alias, values_alias):
    rc = ds.transpose().reset_index()
    rc.rename(columns={'index': group_alias, 0: values_alias}, inplace=True)
    return rc

def zero_fill():
    pass

def rename_columns(ds, map):
    rc = ds.rename(columns=map)
    return rc

def remove_columns(ds, columns):
    cols_to_drop = [c for c in columns if c in ds]
    rc = ds.drop(columns=cols_to_drop, errors='ignore')
    return rc

def reorder_columns(ds, columns):
    rc = ds[[o for o in columns if o in ds.columns] + [c for c in ds.columns if c not in columns]]
    return rc

def group_by():
    pass

def histogram_buckets():
    pass

def filter():
    pass

def sort():
    pass

def pivot():
    pass

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
            suffixes=(None, ':1')
        )

    return rc

def full_outer_join(datasets, join_on_first_n_columns):
    return _join('outer', datasets, join_on_first_n_columns)

def inner_join(datasets, join_on_first_n_columns):
    return _join('inner', datasets, join_on_first_n_columns)

def left_join(datasets, join_on_first_n_columns):
    return _join('left', datasets, join_on_first_n_columns)

def table():
    pass

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

def bar(ds):
    # Ensure the default "index" column is not part of the plot
    if type(ds.index) == pd.RangeIndex or type(ds.index) == pd.Int64Index:
        index_column = ds.columns[0]
        ds = ds.set_index(index_column)
    
    # Configure chart display
    fig, ax = plt.subplots()
    ax.yaxis.set_major_formatter(number_formatter)
    ds.plot.bar(ax=ax)

    # Rotate x axis labels 45 degrees
    fig.autofmt_xdate()

    # Increase chart size
    fig.set_size_inches(12, 8)

    # Display chart
    plt.show()

def single_value(ds):
    print(ds.iloc[0, 0])

def pie(ds):
    y_column = ds.columns[1]
    ds.plot.pie(y=y_column)
    plt.show()

def area(ds):
    ds.plot.area()
    plt.show()

def bar_line(ds):
    # TODO: change stacked according to settings
    ds[ds.columns[1:-1]].plot.bar(stacked=True)
    ds[ds.columns[-1]].plot(kind="line", secondary_y=True)
    plt.show()
