def calculate(data, **params):
    import pandas as pd
    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    result = pd.Series([0]*len(data), index=data.index)
    return result
