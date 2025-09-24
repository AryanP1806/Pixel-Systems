class HashTable:
    def __init__(self, size):
        self.size = size
        self.table = [[] for _ in range(size)]  # Separate chaining for collisions

    def hash_function(self, key):
        return key % self.size

    def insert(self, key, value):
        index = self.hash_function(key)
        # Update value if key already exists
        for pair in self.table[index]:
            if pair[0] == key:
                pair[1] = value
                print("Key updated successfully!")
                return
        # Otherwise, add new key-value pair
        self.table[index].append([key, value])
        print("Key inserted successfully!")

    def search(self, key):
        index = self.hash_function(key)
        for pair in self.table[index]:
            if pair[0] == key:
                print(f"Key found! Value: {pair[1]}")
                return
        print("Key not found in hash table.")

    def display(self):
        print("\nHash Table Contents:")
        for i, bucket in enumerate(self.table):
            print(f"Index {i}: {bucket}")


# Menu-driven program
def main():
    size = int(input("Enter size of hash table: "))
    ht = HashTable(size)

    while True:
        print("\nMenu:")
        print("1. Insert")
        print("2. Search")
        print("3. Display")
        print("4. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            key = int(input("Enter key (integer): "))
            value = input("Enter value: ")
            ht.insert(key, value)

        elif choice == '2':
            key = int(input("Enter key to search: "))
            ht.search(key)

        elif choice == '3':
            ht.display()

        elif choice == '4':
            print("Exiting program. Goodbye!")
            break

        else:
            print("Invalid choice! Please try again.")


if __name__ == "__main__":
    main()
