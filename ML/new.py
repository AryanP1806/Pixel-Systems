def repeat(n):
    def decorator(func):
        def wrapper(*args,**kwargs):
            for i in range(n):
                func(*args,**kwargs)
        return wrapper
    return decorator
@repeat(5)
def say():
    print("Hi")
say()
list1 = [1, 2, 3, 4, 5, 6]
