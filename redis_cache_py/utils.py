

def get_args_dict(func, args, kwargs):
    args_names = func.__code__.co_varnames[:func.__code__.co_argcount]
    return {
        **dict(zip(args_names, args)),
        **kwargs
    }

def make_key(func, *args, **kwargs):
    args_dict = get_args_dict(func, args, kwargs)
    sorted_args = sorted(args_dict.items(), key=lambda x: x[0])  # Sort by arg name
    args_str = ".".join(f"{k}={v}" for k, v in sorted_args)
    key = f"{func.__module__}.{func.__qualname__}({args_str})"
    return key
