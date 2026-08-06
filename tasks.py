import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from app import app as streamlit_app

def load_data():
    """Load and validate the required datasets"""
    try:
        matches_df = pd.read_csv('matches.csv')
        deliveries_df = pd.read_csv('deliveries.csv')
        return matches_df, deliveries_df
    except FileNotFoundError as e:
        print(f"Error: Required data files not found - {str(e)}")
        return None, None

def analyze_data():
    """Perform basic data analysis"""
    matches_df, deliveries_df = load_data()
    if matches_df is None or deliveries_df is None:
        return
    
    print("Basic Analysis:")
    print(f"Total matches: {len(matches_df)}")
    print(f"Total seasons: {matches_df['season'].nunique()}")
    print(f"Total teams: {matches_df['team1'].nunique()}")

def run_streamlit():
    """Run the Streamlit dashboard"""
    try:
        streamlit_app()
    except Exception as e:
        print(f"Error running Streamlit app: {str(e)}")

def main():
    """Main task runner"""
    tasks = {
        '1': ('Load and validate data', load_data),
        '2': ('Run basic analysis', analyze_data),
        '3': ('Launch Streamlit dashboard', run_streamlit),
    }
    
    while True:
        print("\nAvailable tasks:")
        for key, (desc, _) in tasks.items():
            print(f"{key}. {desc}")
        print("q. Quit")
        
        choice = input("\nSelect a task (or 'q' to quit): ").lower()
        if choice == 'q':
            break
        
        if choice in tasks:
            print(f"\nExecuting: {tasks[choice][0]}")
            tasks[choice][1]()
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main()