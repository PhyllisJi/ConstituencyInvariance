class TransError:
    error_count = 0

    def __init__(self, last_trans, next_trans, error_words):
        self.last_trans = last_trans
        self.next_trans = next_trans
        self.error_words = error_words
        TransError.error_count += 1

    def show_error(self):
        print(self.last_trans.source, self.last_trans.trans)
        print(self.next_trans.source, self.next_trans.trans)

    def save_error(self):
        last = "{};{}".format(self.last_trans.source, self.last_trans.trans)
        next = "{};{}".format(self.next_trans.source, self.next_trans.trans)
        return last, next, self.error_words
