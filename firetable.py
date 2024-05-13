import tkinter as tk
from tkinter import ttk
import pandas as pd

def load_data_frame(csv_path):

    try:
        return pd.read_csv(csv_path)
    except Exception as e:
        print(f"Failed to read CSV file: {e}")
        return pd.DataFrame()  

def create_gui(csv_path):

    root = tk.Tk()
    root.title("Fire Data Viewer")


    df = load_data_frame(csv_path)

    tree = ttk.Treeview(root, columns=list(df.columns), show="headings")
    for col in df.columns:
        tree.heading(col, text=col)
        tree.column(col, width=120, anchor=tk.CENTER)

    for index, row in df.iterrows():
        tree.insert('', index, values=list(row))
    

    vsb = ttk.Scrollbar(root, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(root, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    vsb.pack(side='right', fill='y')
    hsb.pack(side='bottom', fill='x')
    
    tree.pack(side="top", fill="both", expand=True)
    
    root.mainloop()

csv_path = './out/fire_log3'  
create_gui(csv_path)
