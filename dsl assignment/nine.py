class Node:
    """
    A class to represent a single node in a Binary Search Tree.
    """
    def __init__(self, key):
        self.key = key      # The value stored in the node
        self.left = None    # Pointer to the left child
        self.right = None   # Pointer to the right child

class BinarySearchTree:
    """
    A class to represent the entire Binary Search Tree and its operations.
    """
    
    def __init__(self):
        """Initializes an empty BST with a null root."""
        self.root = None

    # --- 1. Insertion ---

    def insert(self, key):
        """
        Public method to insert a new key into the BST.
        It calls the private recursive helper function.
        """
        if self.root is None:
            self.root = Node(key)
        else:
            self._insert_recursive(self.root, key)
        print(f"Inserted: {key}")

    def _insert_recursive(self, current_node, key):
        """
        Recursive helper to find the correct spot and insert the new node.
        """
        if key < current_node.key:
            # Go to the left subtree
            if current_node.left is None:
                current_node.left = Node(key)
            else:
                self._insert_recursive(current_node.left, key)
        elif key > current_node.key:
            # Go to the right subtree
            if current_node.right is None:
                current_node.right = Node(key)
            else:
                self._insert_recursive(current_node.right, key)
        else:
            # Key already exists, do nothing (or handle as needed)
            print(f"Key {key} already exists. Ignoring insertion.")

    # --- 2. Search ---

    def search(self, key):
        """
        Public method to search for a key.
        Returns True if the key is found, otherwise False.
        """
        if self._search_recursive(self.root, key):
            print(f"Search: Key {key} was found.")
            return True
        else:
            print(f"Search: Key {key} was NOT found.")
            return False

    def _search_recursive(self, current_node, key):
        """
        Recursive helper to search for a key.
        Returns the node if found, otherwise None.
        """
        # Base cases:
        # 1. Root is null (tree is empty or we've reached a leaf's child)
        # 2. Key is found
        if current_node is None or current_node.key == key:
            return current_node
        
        # Recursive steps:
        if key < current_node.key:
            # Search in the left subtree
            return self._search_recursive(current_node.left, key)
        else:
            # Search in the right subtree
            return self._search_recursive(current_node.right, key)

    # --- 3. Display (In-order Traversal) ---

    def display_in_order(self):
        """
        Public method to display the tree's keys in ascending order
        (In-order Traversal).
        """
        print("--- In-order Display (Sorted) ---")
        nodes = []
        self._in_order_recursive(self.root, nodes)
        print(" -> ".join(map(str, nodes)))

    def _in_order_recursive(self, current_node, nodes_list):
        """
        Recursive helper for in-order traversal (Left -> Root -> Right).
        """
        if current_node is not None:
            self._in_order_recursive(current_node.left, nodes_list)
            nodes_list.append(current_node.key)
            self._in_order_recursive(current_node.right, nodes_list)

    # --- 4. Deletion ---

    def delete(self, key):
        """
        Public method to delete a key from the BST.
        It calls the private recursive helper.
        """
        self.root = self._delete_recursive(self.root, key)
        print(f"Attempted to delete: {key}")

    def _find_min_node(self, node):
        """
        Helper function to find the node with the minimum key
        in a given subtree (the leftmost node).
        """
        current = node
        while current.left is not None:
            current = current.left
        return current

    def _delete_recursive(self, current_node, key):
        """
        Recursive helper to find the node and delete it.
        """
        # Base case: If the tree is empty
        if current_node is None:
            return current_node
        
        # --- 1. Find the node to delete ---
        if key < current_node.key:
            current_node.left = self._delete_recursive(current_node.left, key)
        elif key > current_node.key:
            current_node.right = self._delete_recursive(current_node.right, key)
        else:
            # --- 2. Node found! Handle the 3 deletion cases ---
            
            # Case 1: Node with only one child or no child
            if current_node.left is None:
                temp_node = current_node.right
                current_node = None  # Free the memory (in Python, just dereference)
                return temp_node
            elif current_node.right is None:
                temp_node = current_node.left
                current_node = None
                return temp_node
                
            # Case 2: Node with two children
            # Get the in-order successor (smallest in the right subtree)
            temp_node = self._find_min_node(current_node.right)
            
            # Copy the successor's key to this node
            current_node.key = temp_node.key
            
            # Delete the in-order successor from the right subtree
            current_node.right = self._delete_recursive(current_node.right, temp_node.key)
            
        return current_node
        
    # --- Bonus: Pretty Visual Display ---
    
    def display_visual(self):
        """Public method for a simple visual display of the tree structure."""
        print("--- Visual Tree Structure ---")
        if self.root is None:
            print("(Empty Tree)")
        else:
            self._display_visual_recursive(self.root, 0)
    
    def _display_visual_recursive(self, current_node, level):
        """Recursive helper for visual display (Pre-order: Root -> Left -> Right)."""
        if current_node is not None:
            indent = "  " * level
            print(f"{indent}|- {current_node.key}")
            self._display_visual_recursive(current_node.left, level + 1)
            self._display_visual_recursive(current_node.right, level + 1)


# --- Main execution (Driver Code) ---
if __name__ == "__main__":
    
    bst = BinarySearchTree()
    
    # --- 1. Insertion ---
    print("--- 1. INSERTING NODES ---")
    keys_to_insert = [50, 30, 70, 20, 40, 60, 80]
    for key in keys_to_insert:
        bst.insert(key)

    # --- 2. Display ---
    print("\n--- 2. DISPLAYING TREE ---")
    bst.display_in_order()
    bst.display_visual()

    # --- 3. Search ---
    print("\n--- 3. SEARCHING NODES ---")
    bst.search(40)  # Should be found
    bst.search(90)  # Should not be found

    # --- 4. Deletion ---
    print("\n--- 4. DELETING NODES ---")
    
    # Case 1: Delete a leaf node (e.g., 20)
    print("\n--- Deleting Leaf Node (20) ---")
    bst.delete(20)
    bst.display_visual()

    # Case 2: Delete a node with one child (e.g., 70, which has 60 and 80)
    # Let's delete 30 (which now has one child: 40)
    print("\n--- Deleting Node with One Child (30) ---")
    bst.delete(30)
    bst.display_visual()

    # Case 3: Delete a node with two children (e.g., 50, the root)
    print("\n--- Deleting Node with Two Children (50) ---")
    bst.delete(50)
    bst.display_visual()
    
    # Final in-order display to show it's still sorted
    print("\n--- Final In-order Display ---")
    bst.display_in_order()