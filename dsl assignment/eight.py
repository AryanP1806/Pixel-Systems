# A special constant to mark deleted slots in the hash table.
# This is necessary for linear probing to work correctly after deletions.
DELETED_NODE = "<deleted>"

class HashTable:
    """
    A class to represent a hash table using the division method and linear probing.
    """

    def __init__(self, size):
        """
        Initializes the hash table with a fixed size.
        Args:
            size (int): The number of slots in the hash table.
        """
        self.size = size
        # Initialize the table with None, representing empty slots.
        self.table = [None] * size

    def _hash_function(self, key):
        """
        Calculates the hash index for a given key using the division method.
        Args:
            key (int): The key to be hashed.
        Returns:
            int: The calculated index in the hash table.
        """
        return key % self.size

    def insert(self, key):
        """
        Inserts a key into the hash table.
        It uses linear probing to find the next available slot if a collision occurs.
        """
        initial_index = self._hash_function(key)

        # Probe for the next available slot
        for i in range(self.size):
            probe_index = (initial_index + i) % self.size

            # If the slot is empty or was previously deleted, insert the new key
            if self.table[probe_index] is None or self.table[probe_index] == DELETED_NODE:
                self.table[probe_index] = key
                print(f"✅ Key '{key}' inserted at index {probe_index}.")
                return

            # If the key already exists, notify the user and stop
            if self.table[probe_index] == key:
                print(f"⚠️ Key '{key}' already exists at index {probe_index}. No duplicates allowed.")
                return

        # If the loop completes, the table is full
        print("❌ Hash table is full. Cannot insert key.")

    def search(self, key):
        """
        Searches for a key in the hash table.
        Returns the index if found, otherwise returns -1.
        """
        initial_index = self._hash_function(key)

        # Probe for the key
        for i in range(self.size):
            probe_index = (initial_index + i) % self.size

            # If we find an empty slot, the key cannot be in the table
            if self.table[probe_index] is None:
                print(f"❓ Key '{key}' not found.")
                return -1

            # If we find the key, return its index
            if self.table[probe_index] == key:
                print(f"🔍 Key '{key}' found at index {probe_index}.")
                return probe_index

        # If the loop completes, the key was not found
        print(f"❓ Key '{key}' not found.")
        return -1

    def delete(self, key):
        """
        Deletes a key from the hash table.
        It replaces the key with a special marker to maintain the probe chain.
        """
        initial_index = self._hash_function(key)

        # Probe to find the key to be deleted
        for i in range(self.size):
            probe_index = (initial_index + i) % self.size

            # If we hit an empty slot, the key isn't in the table
            if self.table[probe_index] is None:
                print(f"❓ Key '{key}' not found. Cannot delete.")
                return

            # If we find the key, replace it with the deleted marker
            if self.table[probe_index] == key:
                self.table[probe_index] = DELETED_NODE
                print(f"🗑️ Key '{key}' deleted from index {probe_index}.")
                return

        # If the loop completes, the key was not found
        print(f"❓ Key '{key}' not found. Cannot delete.")

    def display(self):
        """
        Displays the current state of the hash table.
        """
        print("\n--- Hash Table Status ---")
        for i, item in enumerate(self.table):
            value = "EMPTY" if item is None else item
            print(f"Index {i}: {value}")
        print("-------------------------\n")


def main():
    """
    Main function to provide a user interface for hash table operations.
    """
    try:
        size = int(input("Enter the size of the hash table: "))
        if size <= 0:
            print("Size must be a positive integer.")
            return
        ht = HashTable(size)
    except ValueError:
        print("Invalid input. Please enter an integer for the size.")
        return

    while True:
        print("\n--- Hash Table Menu ---")
        print("1. Insert a key")
        print("2. Search for a key")
        print("3. Delete a key")
        print("4. Display the table")
        print("5. Exit")

        choice = input("Enter your choice (1-5): ")

        if choice == '1':
            try:
                key = int(input("Enter the integer key to insert: "))
                ht.insert(key)
            except ValueError:
                print("Invalid key. Please enter an integer.")
        elif choice == '2':
            try:
                key = int(input("Enter the integer key to search for: "))
                ht.search(key)
            except ValueError:
                print("Invalid key. Please enter an integer.")
        elif choice == '3':
            try:
                key = int(input("Enter the integer key to delete: "))
                ht.delete(key)
            except ValueError:
                print("Invalid key. Please enter an integer.")
        elif choice == '4':
            ht.display()
        elif choice == '5':
            print("Exiting program. Goodbye! 👋")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")

# Run the main program
if __name__ == "__main__":
    main()