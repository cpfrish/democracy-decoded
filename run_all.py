#!/usr/bin/env python3
"""
Run All Steps - Complete workflow from data fetching to visualization
"""

import subprocess
import sys
import os


def run_step(step_num, script_name, description):
    """Run a single step and handle errors"""
    print()
    print("=" * 70)
    print(f"Running Step {step_num}: {description}")
    print("=" * 70)
    print()
    
    result = subprocess.run([sys.executable, script_name])
    
    if result.returncode != 0:
        print()
        print(f"ERROR: Step {step_num} failed!")
        print(f"Try running manually: python {script_name}")
        sys.exit(1)
    
    return True


def main():
    """Run all steps in sequence"""
    
    # Check for API key
    if not os.environ.get("CONGRESS_API_KEY"):
        print("=" * 70)
        print("ERROR: CONGRESS_API_KEY environment variable not set")
        print("=" * 70)
        print()
        print("Please set your Congress.gov API key:")
        print("  export CONGRESS_API_KEY='your_key_here'")
        print()
        print("Get an API key at: https://api.congress.gov/sign-up/")
        sys.exit(1)
    
    print()
    print("=" * 70)
    print("Congressional Data Pipeline")
    print("=" * 70)
    print()
    print("This will fetch all data and create visualizations.")
    print("Total time: ~4-5 minutes")
    print()
    input("Press Enter to continue...")
    
    # Run all steps
    run_step(1, "1_fetch_member_data.py", "Fetch member data")
    run_step(2, "2_fetch_location_data.py", "Fetch location data")
    run_step(3, "3_create_visualizations.py", "Create visualizations")
    
    print()
    print("=" * 70)
    print("✓ ALL STEPS COMPLETE!")
    print("=" * 70)
    print()
    print("Your visualizations are ready in the visualizations/ directory:")
    print("  - member_activity_scatter_interactive.html")
    print("  - congress_map_dual_chamber.html")
    print()
    print("Open these HTML files in your web browser to explore!")
    print()


if __name__ == "__main__":
    main()
