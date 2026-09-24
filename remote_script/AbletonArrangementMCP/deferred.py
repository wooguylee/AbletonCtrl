"""Internal continuations; advance once per Live update_display, never on a worker."""


class Deferred:
    def __init__(self, iterator):
        self.iterator = iterator

    def advance(self):
        try:
            next(self.iterator)
            return self
        except StopIteration as done:
            return done.value

    def close(self):
        self.iterator.close()
