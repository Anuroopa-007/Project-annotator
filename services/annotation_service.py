class AnnotationService:
    def __init__(self):
        self.annotations = []
        self.class_map = {}

    def add(self, label, rect):
        if label not in self.class_map:
            self.class_map[label] = len(self.class_map)
        self.annotations.append((label, rect))

    def clear(self):
        self.annotations.clear()
