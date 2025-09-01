import pandas as pd
from .ta_utils import EMA

def calculate(data, N1=12, N2=26, N3=9):
    high = data['HIGH']
    low = data['LOW']
    aws = EMA((high + low) / 2, N1) - EMA((high + low) / 2, N2)
    aws_signal = EMA(aws, N3)
    return aws, aws_signal
