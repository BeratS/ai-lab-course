from calculator import add, subtract, multiply, divide

assert add(2, 3) == 5
assert add(-1, 1) == 0
assert add(0.5, 0.25) == 0.75

assert subtract(5, 3) == 2
assert subtract(3, 5) == -2

assert multiply(4, 3) == 12
assert multiply(-2, 3) == -6
assert multiply(0, 99) == 0

assert divide(6, 3) == 2
assert divide(7, 2) == 3.5
assert divide(-6, 3) == -2

for zero in (0, 0.0):
    try:
        divide(1, zero)
    except ValueError:
        pass
    else:
        raise AssertionError("divide by zero did not raise ValueError")

print('ALL TESTS PASSED')
