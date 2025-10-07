from .models import Student

class StudentHashTable:
    def __init__(self):
        self.table = {}

    def _hash(self, student_id):
        return hash(student_id) % 100  # simple hash function

    def insert(self, student):
        key = self._hash(student.student_id)
        self.table[key] = student

    def search(self, student_id):
        key = self._hash(student_id)
        return self.table.get(key, None)

    def delete(self, student_id):
        key = self._hash(student_id)
        if key in self.table:
            del self.table[key]

    def get_all_sorted(self):
        return sorted(self.table.values(), key=lambda s: s.name)

# Singleton hash table
student_hash = StudentHashTable()
