import matplotlib.pyplot as plt
import os
import sys

def init_font_cache():
    print("Initializing matplotlib font cache...")
    plt.figure()
    plt.close()
    print("Font cache initialization complete.")

if __name__ == "__main__":
    init_font_cache()