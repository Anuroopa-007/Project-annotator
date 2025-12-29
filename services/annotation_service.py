class AnnotationService:
    def __init__(self):
        self.annotations = []

    def add(self, label, rect):
        label = label.strip().lower()  # normalize
        self.annotations.append((label, rect))

    def clear(self):
        self.annotations.clear()
