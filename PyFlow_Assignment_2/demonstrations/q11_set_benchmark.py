"""
Question 11: Reproducible benchmark comparing list vs set membership testing.
Demonstrates O(n) vs O(1) lookup performance.
"""

import time
import random
from typing import List, Set

def benchmark_list_vs_set(sizes: List[int] = [1000, 5000, 10000, 50000]) -> None:
    """
    Question 11: Benchmark list vs set membership testing.
    
    Expected results:
    - List: O(n) - linear time complexity
    - Set: O(1) - constant time complexity
    """
    print("=" * 80)
    print("Question 11: List vs Set Membership Testing Benchmark")
    print("=" * 80)
    print()
    
    # Set seed for reproducibility
    random.seed(42)
    
    print(f"{'Size':<10} {'List (ms)':<15} {'Set (ms)':<15} {'Speedup':<10}")
    print("-" * 60)
    
    for size in sizes:
        # Create test data
        data_list = list(range(size))
        data_set = set(data_list)
        
        # Random search values (mix of present and absent)
        search_values = [random.randint(0, size + 1000) for _ in range(1000)]
        
        # Benchmark list
        start = time.time()
        for value in search_values:
            _ = value in data_list
        list_time = (time.time() - start) * 1000  # Convert to ms
        
        # Benchmark set
        start = time.time()
        for value in search_values:
            _ = value in data_set
        set_time = (time.time() - start) * 1000  # Convert to ms
        
        speedup = list_time / set_time if set_time > 0 else float('inf')
        
        print(f"{size:<10} {list_time:<15.4f} {set_time:<15.4f} {speedup:<10.2f}x")
    
    print()
    print("Conclusion:")
    print("- Set lookup is O(1) - constant time")
    print("- List lookup is O(n) - linear time")
    print("- Performance gap increases with data size")
    print("- Sets are significantly faster for membership testing")
    print("=" * 80)


if __name__ == "__main__":
    benchmark_list_vs_set()
