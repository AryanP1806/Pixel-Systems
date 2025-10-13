class Node:
    """A node in a linked list for chaining."""
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.next = None

class HashTable:
    """A hash table of size 10 using division method and chaining."""
    def __init__(self):
        self.size = 10
        self.table = [None] * self.size

    def _hash_function(self, key):
        """Calculates the index for a key."""
        return key % self.size

    def insert(self, key, value):
        """Inserts a key-value pair, updating the value if the key already exists."""
        index = self._hash_function(key)
        head = self.table[index]
        
        # Check if key already exists in the chain
        current = head
        while current:
            if current.key == key:
                current.value = value  # Update existing key
                return
            current = current.next

        # Insert new node at the beginning of the chain
        new_node = Node(key, value)
        new_node.next = head
        self.table[index] = new_node

    def search(self, key):
        """Searches for a key and returns its value, or None if not found."""
        index = self._hash_function(key)
        current = self.table[index]
        
        while current:
            if current.key == key:
                return current.value
            current = current.next
        return None # Key not found

    def delete(self, key):
        """Deletes a key-value pair. Returns True if successful, False otherwise."""
        index = self._hash_function(key)
        head = self.table[index]
        prev = None
        current = head
        
        while current:
            if current.key == key:
                if prev:
                    prev.next = current.next  # Unlink from the middle/end
                else:
                    self.table[index] = current.next  # Unlink from the head
                return True
            prev = current
            current = current.next
        return False # Key not found

    def display(self):
        """Prints the contents of the hash table."""
        print("\n--- Hash Table ---")
        for i, head in enumerate(self.table):
            chain = []
            current = head
            while current:
                chain.append(f"({current.key}:'{current.value}')")
                current = current.next
            
            if chain:
                print(f"Index {i}: " + " -> ".join(chain))
            else:
                print(f"Index {i}: EMPTY")
        print("--------------------\n")

# --- Example Usage ---
if __name__ == "__main__":
    ht = HashTable()

    # 1. Insert items (keys 5, 25, 15 will collide)
    ht.insert(5, "Apple")
    ht.insert(25, "Banana")
    ht.insert(15, "Cherry")
    ht.insert(8, "Date")
    print("After inserting items:")
    ht.display()

    # 2. Search for a key
    print(f"Searching for key 15: Value is '{ht.search(15)}'")
    print(f"Searching for key 99: Value is {ht.search(99)}")

    # 3. Delete a key
    ht.delete(25) # Deletes 'Banana' from the middle of a chain
    print("\nAfter deleting key 25:")
    ht.display()