import sys
from collections import deque

class CityGraph:
    """
    This class represents the map of city locations as a graph.
    It stores two representations:
    1. Adjacency Matrix (for DFS)
    2. Adjacency List (for BFS)
    """
    
    def __init__(self, locations):
        """
        Initializes the graph with a list of location names.
        
        Args:
            locations (list): A list of strings, where each string is a location name.
        """
        self.locations = locations
        self.num_locations = len(locations)
        
        # --- Mappings ---
        # Create a mapping from location name (e.g., 'A') to matrix index (e.g., 0)
        self.location_to_index = {location: i for i, location in enumerate(locations)}
        # Create a reverse mapping from index to location name
        self.index_to_location = {i: location for i, location in enumerate(locations)}
        
        # --- 1. Adjacency Matrix (for DFS) ---
        # Initialize an N x N matrix with all zeros
        self.adj_matrix = [[0] * self.num_locations for _ in range(self.num_locations)]
        
        # --- 2. Adjacency List (for BFS) ---
        # Initialize an empty adjacency list (dictionary)
        self.adj_list = {location: [] for location in locations}

    def add_route(self, location1, location2):
        """
        Adds an undirected route (an edge) between two locations.
        It updates both the adjacency matrix and the adjacency list.
        
        Args:
            location1 (str): The name of the first location.
            location2 (str): The name of the second location.
        """
        if location1 not in self.location_to_index or location2 not in self.location_to_index:
            print(f"Error: One or both locations '{location1}', '{location2}' are not in the graph.")
            return
            
        # Get indices for the matrix
        idx1 = self.location_to_index[location1]
        idx2 = self.location_to_index[location2]
        
        # Update Adjacency Matrix (undirected)
        self.adj_matrix[idx1][idx2] = 1
        self.adj_matrix[idx2][idx1] = 1
        
        # Update Adjacency List (undirected)
        if location2 not in self.adj_list[location1]:
            self.adj_list[location1].append(location2)
        if location1 not in self.adj_list[location2]:
            self.adj_list[location2].append(location1)
            
    def print_adj_matrix(self):
        """Helper function to print the adjacency matrix."""
        print("--- Adjacency Matrix ---")
        # Print header
        print("  ", " ".join(self.locations))
        for i, row in enumerate(self.adj_matrix):
            print(self.locations[i], "", " ".join(map(str, row)))
            
    def print_adj_list(self):
        """Helper function to print the adjacency list."""
        print("\n--- Adjacency List ---")
        for location, neighbors in self.adj_list.items():
            print(f"{location}: {', '.join(neighbors)}")

    # --- (i) DFS with Adjacency Matrix ---
    
    def dfs(self, start_location):
        """
        Public method to start the Depth-First Search.
        
        Args:
            start_location (str): The name of the starting location.
            
        Returns:
            list: The sequence of visited locations.
        """
        if start_location not in self.location_to_index:
            return f"Error: Starting location '{start_location}' not found."
            
        # 1. Create a 'visited' array for indices, initialized to False
        visited_indices = [False] * self.num_locations
        
        # 2. Create a list to store the traversal path
        traversal_path = []
        
        # 3. Get the starting index
        start_index = self.location_to_index[start_location]
        
        # 4. Call the recursive helper function
        self._dfs_recursive(start_index, visited_indices, traversal_path)
        
        return traversal_path

    def _dfs_recursive(self, current_index, visited_indices, traversal_path):
        """
        Recursive helper function for DFS using the adjacency matrix.
        
        Args:
            current_index (int): The index of the current location.
            visited_indices (list): The boolean array tracking visited indices.
            traversal_path (list): The list to append visited locations to.
        """
        # 1. Mark the current node as visited
        visited_indices[current_index] = True
        
        # 2. Add the *location name* to the traversal path
        location_name = self.index_to_location[current_index]
        traversal_path.append(location_name)
        
        # 3. Recur for all adjacent, unvisited neighbors
        # We check the row of the current_index in the matrix
        for neighbor_index in range(self.num_locations):
            # Check if an edge exists (matrix[current][neighbor] == 1)
            if self.adj_matrix[current_index][neighbor_index] == 1:
                # Check if this neighbor has not been visited
                if not visited_indices[neighbor_index]:
                    self._dfs_recursive(neighbor_index, visited_indices, traversal_path)

    # --- (ii) BFS with Adjacency List ---

    def bfs(self, start_location):
        """
        Public method to start the Breadth-First Search.
        
        Args:
            start_location (str): The name of the starting location.
            
        Returns:
            list: The sequence of visited locations.
        """
        if start_location not in self.location_to_index:
            return f"Error: Starting location '{start_location}' not found."
            
        # 1. Create a 'visited' set for location names
        visited_locations = set()
        
        # 2. Create a queue for BFS
        # Use collections.deque for an efficient queue
        queue = deque()
        
        # 3. Create a list to store the traversal path
        traversal_path = []
        
        # 4. Enqueue the start location and mark it as visited
        queue.append(start_location)
        visited_locations.add(start_location)
        
        # 5. Loop until the queue is empty
        while queue:
            # Dequeue a location
            current_location = queue.popleft()
            traversal_path.append(current_location)
            
            # Get all neighbors of the current location from the Adjacency List
            for neighbor in self.adj_list[current_location]:
                # If the neighbor has not been visited
                if neighbor not in visited_locations:
                    # Mark it as visited
                    visited_locations.add(neighbor)
                    # Enqueue it
                    queue.append(neighbor)
                    
        return traversal_path


# --- Main execution ---
if __name__ == "__main__":
    
    # 1. Define the popular locations in your area
    # (Using letters as placeholders per your example)
    locations = ['A', 'B', 'C', 'D', 'E', 'F']
    
    # 2. Create the graph
    city_map = CityGraph(locations)
    
    # 3. Add the routes (edges)
    # Let's create a sample map:
    # A is connected to B and C
    # B is connected to A, D, and E
    # C is connected to A and F
    # D is connected to B
    # E is connected to B and F
    # F is connected to C and E
    
    city_map.add_route('A', 'B')
    city_map.add_route('A', 'C')
    city_map.add_route('B', 'D')
    city_map.add_route('B', 'E')
    city_map.add_route('C', 'F')
    city_map.add_route('E', 'F')
    
    # 4. Print the graph representations
    city_map.print_adj_matrix()
    city_map.print_adj_list()
    
    print("\n" + "="*40)
    
    # 5. Define the starting location
    start_node = 'A'
    print(f"Starting traversal from location: {start_node}")
    
    # 6. Run DFS (using Adjacency Matrix)
    dfs_sequence = city_map.dfs(start_node)
    print(f"\n(i) DFS Traversal Sequence:")
    print(" -> ".join(dfs_sequence))
    
    # 7. Run BFS (using Adjacency List)
    bfs_sequence = city_map.bfs(start_node)
    print(f"\n(ii) BFS Traversal Sequence:")
    print(" -> ".join(bfs_sequence))