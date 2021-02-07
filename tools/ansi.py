
class AnsiEscapeCode:
    def __init__(self, pattern):
        self.pattern = pattern

    def __format__(self, spec):
        return self.pattern.format(spec)


esc = AnsiEscapeCode("\033[{0}")
color = AnsiEscapeCode("\033[{0}m")
