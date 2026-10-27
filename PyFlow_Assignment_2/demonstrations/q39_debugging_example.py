"""
Question 39: Documented pdb debugging example.
Demonstrates use of Python debugger for troubleshooting.
"""

import pdb
import pandas as pd

def buggy_fare_calculator(df: pd.DataFrame) -> pd.DataFrame:
    """
    Question 39: Example function with intentional bug for debugging demonstration.
    
    Bug: Incorrectly calculates total fare
    
    To debug, run:
        python -m pdb demonstrations/q39_debugging_example.py
    
    Or insert breakpoint:
        pdb.set_trace()
    
    Common pdb commands:
    - n (next): Execute next line
    - s (step): Step into function
    - c (continue): Continue execution
    - p variable: Print variable value
    - pp variable: Pretty-print variable
    - l (list): Show current code
    - w (where): Show call stack
    - b lineno: Set breakpoint at line
    - cl (clear): Clear breakpoints
    - q (quit): Exit debugger
    """
    
    # Set breakpoint here
    # pdb.set_trace()  # Uncomment to debug
    
    # Bug: Should add tip_amount, not multiply
    df['total_calculated'] = df['fare_amount'] * df['tip_amount']  # BUG!
    
    # Correct version:
    # df['total_calculated'] = df['fare_amount'] + df['tip_amount']
    
    return df


def debugging_tutorial():
    """
    Interactive debugging tutorial for Question 39.
    """
    print("=" * 80)
    print("Question 39: pdb Debugging Tutorial")
    print("=" * 80)
    print()
    
    # Create sample data
    df = pd.DataFrame({
        'trip_id': [1, 2, 3],
        'fare_amount': [10.0, 15.0, 20.0],
        'tip_amount': [2.0, 3.0, 4.0]
    })
    
    print("Original Data:")
    print(df)
    print()
    
    print("Running buggy_fare_calculator...")
    print("(Expected: total = fare + tip)")
    print()
    
    # Uncomment to actually debug:
    # pdb.set_trace()
    
    result = buggy_fare_calculator(df)
    
    print("Result:")
    print(result)
    print()
    
    print("Bug Found!")
    print("- Line: df['total_calculated'] = df['fare_amount'] * df['tip_amount']")
    print("- Issue: Using multiplication instead of addition")
    print("- Fix: Change * to +")
    print()
    
    print("Debugging Steps Using pdb:")
    print("1. Insert breakpoint: pdb.set_trace()")
    print("2. Run script: python script.py")
    print("3. Use 'n' to step through code")
    print("4. Use 'p df' to inspect dataframe")
    print("5. Use 'l' to see code context")
    print("6. Use 'c' to continue or 'q' to quit")
    print()
    
    print("Alternative: Run with debugger from command line:")
    print("  python -m pdb script.py")
    print()
    
    print("=" * 80)


if __name__ == "__main__":
    debugging_tutorial()
