from collections import deque

# Function to find minimum dice throws required to reach last cell
def min_dice_throws(board, n):
    """
    board: list of size n (board configuration)
           if board[i] != -1, it means there is a ladder or snake to board[i]
    n: total number of cells on the board
    """

    visited = [False] * n
    queue = deque()

    # Start from first cell (0)
    # Queue stores tuples (cell_index, distance_from_start)
    queue.append((0, 0))
    visited[0] = True

    while queue:
        cell, dist = queue.popleft()

        # If we've reached the last cell, return the result
        if cell == n - 1:
            return dist

        # Roll the dice for 1 to 6
        for dice in range(1, 7):
            next_cell = cell + dice
            if next_cell < n and not visited[next_cell]:
                visited[next_cell] = True

                # If there's a snake or ladder, move accordingly
                if board[next_cell] != -1:
                    queue.append((board[next_cell], dist + 1))
                else:
                    queue.append((next_cell, dist + 1))

    # If end not reachable (should not happen normally)
    return -1


# Example setup
if __name__ == "__main__":
    n = 30
    board = [-1] * n

    # Ladders (start -> end)
    board[2] = 21
    board[4] = 7
    board[10] = 25
    board[19] = 28

    # Snakes (start -> end)
    board[26] = 0
    board[20] = 8
    board[16] = 3
    board[18] = 6

    print("Minimum number of dice throws required is:", min_dice_throws(board, n))
