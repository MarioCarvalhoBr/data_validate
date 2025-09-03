#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
import time
from typing import Callable, Any, Optional
from functools import wraps


def estimate_time(func: Optional[Callable]) -> Callable:
    """
    Decorator to measure execution time of any function.

    Args:
        func: The function to be timed. Can be None or any callable.

    Returns:
        Wrapped function with timing functionality.

    Raises:
        TypeError: If func is not callable or is None.
    """
    if func is None:
        raise TypeError(
            "Cannot decorate None object. Please provide a callable function."
        )

    if not callable(func):
        raise TypeError(f"Object of type '{type(func).__name__}' is not callable.")

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time
            print(f"Function '{func.__name__}' executed in {elapsed_time:.4f} seconds")
            return result
        except Exception as e:
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time
            print(f"Function '{func.__name__}' failed after {elapsed_time:.4f} seconds")
            raise e

    return wrapper


def fibonacci(n: int) -> int:
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)


def main():
    n = 30  # Example input
    print(f"Calculating fibonacci({n}) without timing:")
    print(f"Result: {fibonacci(n)}")

    timed_fibonacci = estimate_time(fibonacci)
    print(f"\nCalculating fibonacci({n}) with timing:")
    print(f"Result: {timed_fibonacci(n)}")

    # timed_read_data = estimate_time(self._read_data)
    # timed_read_data()


if __name__ == "__main__":
    main()
