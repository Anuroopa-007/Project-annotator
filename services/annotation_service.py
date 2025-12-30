class AnnotationService:
    def __init__(self):
        self.annotations = []
        self.undo_stack = []
        self.redo_stack = []

    def add(self, label, rect):
        self.undo_stack.append(self.annotations.copy())
        self.annotations.append((label.strip().lower(), rect))
        self.redo_stack.clear()

    def remove(self, rect):
        self.undo_stack.append(self.annotations.copy())
        self.annotations = [(l, r) for l, r in self.annotations if r != rect]
        self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack:
            return
        self.redo_stack.append(self.annotations.copy())
        self.annotations = self.undo_stack.pop()

    def redo(self):
        if not self.redo_stack:
            return
        self.undo_stack.append(self.annotations.copy())
        self.annotations = self.redo_stack.pop()

    def clear(self):
        self.undo_stack.append(self.annotations.copy())
        self.annotations.clear()
        self.redo_stack.clear()
