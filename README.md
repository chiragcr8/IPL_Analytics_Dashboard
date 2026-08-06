# IPL Data Analytics Project

## Project Structure

```
d:\IPL_Data_Analytics_Project\
├── app.py                 # Main Streamlit dashboard application
├── tasks.py              # Task runner for various operations
├── requirements.txt      # Python dependencies
├── notebooks/           # Jupyter notebooks for analysis
│   └── IPL_Data_Analysis.ipynb
└── data/                # Data directory (create if not exists)
    ├── matches.csv      # Match-level data
    └── deliveries.csv   # Ball-by-ball data
```

## Quick Start

1. Place your data files:
   - Put `matches.csv` and `deliveries.csv` in the project root directory

2. Run tasks:
   ```
   python tasks.py
   ```

3. Launch dashboard:
   ```
   streamlit run app.py
   ```

## Key Files

- `app.py`: Contains the main interactive dashboard
- `tasks.py`: Provides utilities for data loading and analysis
- `notebooks/IPL_Data_Analysis.ipynb`: Contains exploratory data analysis
