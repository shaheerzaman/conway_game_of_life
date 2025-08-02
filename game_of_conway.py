import multiprocessing
import numpy as np
import time
import os

GRID_SIZE = 50
NUM_GENERATIONS = 30
NUM_PROCESSES = os.cpu_count() or 4


def setup_shared_grid(size):
    # shared memory
    shared_array_base = multiprocessing.Array("i", size * size, lock=False)
    grid = np.frombuffer(shared_array_base, dtype=np.int32).reshape((size, size))
    grid[:] = np.random.choice([0, 1], size=(size, size), p=[0.7, 0.3])
    return grid


def worker_task(grid, start_row, end_row, barrier, generations):
    size = len(grid)

    for gen in range(generations):
        local_next_state = np.zeros_like(grid[start_row:end_row])

        for r in range(start_row, end_row):
            for c in range(size):
                live_neighbors = int(
                    (
                        grid[(r - 1) % size, (c - 1) % size]
                        + grid[(r - 1) % size, c]
                        + grid[(r - 1) % size, (c + 1) % size]
                        + grid[r, (c - 1) % size]
                        + grid[r, (c + 1) % size]
                        + grid[(r + 1) % size, (c - 1) % size]
                        + grid[(r + 1) % size, c]
                        + grid[(r + 1) % size, (c + 1) % size]
                    )
                )

                if grid[r, c] == 1 and live_neighbors < 2 or live_neighbors > 3:
                    local_next_state[r - start_row, c] = 0
                elif grid[r, c] == 1 and (live_neighbors == 2 or live_neighbors == 3):
                    local_next_state[r - start_row, c] = 1  # Survives
                elif grid[r, c] == 0 and live_neighbors == 3:
                    local_next_state[r - start_row, c] = 1  # Becomes alive
                else:
                    local_next_state[r - start_row, c] = grid[r, c]

        barrier.wait()
        # criticla section
        grid[start_row:end_row] = local_next_state


def print_grid(grid):
    for row in grid:
        print(" ".join(["■" if cell else "." for cell in row]))

    print("-" * (GRID_SIZE * 2))


if __name__ == "__main__":
    shared_grid = setup_shared_grid(GRID_SIZE)

    barrier = multiprocessing.Barrier(NUM_PROCESSES)
    rows_per_process = GRID_SIZE // NUM_PROCESSES
    processes = []

    print("starting grid")
    print_grid(shared_grid)
    time.sleep(2)

    for i in range(NUM_PROCESSES):
        start_row = i * rows_per_process
        end_row = (i + 1) * rows_per_process if i != NUM_PROCESSES - 1 else GRID_SIZE

        process = multiprocessing.Process(
            target=worker_task,
            args=(shared_grid, start_row, end_row, barrier, NUM_GENERATIONS),
        )
        processes.append(process)
        process.start()

    for p in processes:
        p.join()

    print("Final state")
    print_grid(shared_grid)
