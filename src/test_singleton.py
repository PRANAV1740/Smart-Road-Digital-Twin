def test_metaclass():
    from PySide6.QtCore import QObject
    class Singleton(type(QObject)):
        def __init__(cls, name, bases, dct):
            super().__init__(name, bases, dct)
            cls.instance = None
        def __call__(cls, *args, **kwargs):
            if cls.instance is None:
                cls.instance = super().__call__(*args, **kwargs)
            return cls.instance

    class ThemeManager(QObject, metaclass=Singleton):
        def __init__(self):
            super().__init__()

    t1 = ThemeManager()
    t2 = ThemeManager()
    print("Same instance:", t1 is t2)

if __name__ == "__main__":
    test_metaclass()
