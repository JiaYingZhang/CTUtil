__all__ = ['maxlength', 'minlength']

def maxlength(length: int):
    return lambda x: (x, '') if len(x) <= length else ('', f'{x} length more than {length}')


def minlength(length: int):
    return lambda x: (x, '') if len(x) >= length else ('', f'{x} length less than {length}')