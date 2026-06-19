from typing import Literal
import pandas as pd


Signal = Literal['buy', 'sell', 'hold']


def calculate_ma(df: pd.DataFrame, short_period: int = 5, long_period: int = 20) -> pd.DataFrame:
    """
    ����˫����

    Args:
        df: �������̼۵� DataFrame
        short_period: ���ھ������ڣ�Ĭ��5�գ�
        long_period: ���ھ������ڣ�Ĭ��20�գ�

    Returns:
        ������ MA5��MA20 �е� DataFrame
    """
    ...


def generate_signal(df: pd.DataFrame, short_period: int = 5, long_period: int = 20) -> pd.DataFrame:
    """
    ���������źţ�MA5 �ϴ� MA20 ���룬�´�����

    Args:
        df: �������̼۵� DataFrame
        short_period: ���ھ�������
        long_period: ���ھ�������

    Returns:
        ������ signal �е� DataFrame
    """
    ...
