def hello():
    return "hello"

def divide(ds, new_col, dividend, divisor):
    rc = ds
    rc[new_col] = ds[divident] / ds[divisor]
    return rc