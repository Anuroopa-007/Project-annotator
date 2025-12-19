class AnnotationService:
    def __init__(self):
        self.annotations = []
        self.classes = set()

    def add(self, label, rect):
        self.annotations.append((label, rect))
        self.classes.add(label)

    def clear(self):
        self.annotations.clear()
