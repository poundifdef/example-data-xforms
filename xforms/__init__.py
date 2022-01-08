def hello():
    return "hello"

def divide(ds, new_col, dividend, divisor):
    rc = ds
    rc[new_col] = ds[dividend] / ds[divisor]
    return rc