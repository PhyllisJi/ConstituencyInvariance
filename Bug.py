class Bug:

    def __init__(self, last_step, next_step, error_words, step):
        self.last_step = last_step
        self.next_step = next_step
        self.error_words = error_words
        self.step = step

    def __hash__(self):
        return hash(self.last_step)

    def __eq__(self, other):
        source_sent = self.last_step.split(";")[0]
        other_sent = other.last_step.split(";")[0]
        if source_sent == other_sent:
            return True
        else:
            return False
