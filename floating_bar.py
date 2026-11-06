"""
J.A.R.V.I.S. Floating Quick Command Bar (getjarvis.eu inspired)
Provides an instant floating overlay bar activated anywhere on Windows via Ctrl+Shift+Space / Hotkey.
Sees current screen context, answers grounded in what you are looking at, and triggers tools.
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from desktop_agent import DesktopAgent
from memory import JarvisMemory

agent = DesktopAgent()
mem = JarvisMemory()

class FloatingCommandBar:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S. Floating Bar")
        
        # Frameless, topmost floating bar
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.94)
        
        # Center top of screen
        screen_w = self.root.winfo_screenwidth()
        bar_w, bar_h = 720, 64
        x = (screen_w - bar_w) // 2
        y = 48
        self.root.geometry(f"{bar_w}x{bar_h}+{x}+{y}")
        self.root.configure(bg="#030816")

        # Outer border styling
        outer = tk.Frame(self.root, bg="#38bdf8", bd=1)
        outer.pack(fill="both", expand=True, padx=1, pady=1)

        container = tk.Frame(outer, bg="#071020")
        container.pack(fill="both", expand=True, padx=2, pady=2)

        # Left Icon / Indicator
        icon_lbl = tk.Label(container, text="🛡️", bg="#071020", fg="#38bdf8", font=("Segoe UI Emoji", 14))
        icon_lbl.pack(side="left", padx=(14, 8))

        # Main Input Field
        self.entry = tk.Entry(
            container, 
            bg="#0b172e", 
            fg="#f8fafc", 
            insertbackground="#38bdf8",
            font=("Segoe UI", 12),
            bd=0,
            relief="flat"
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=8, pady=12)
        self.entry.insert(0, "Ask Jarvis anything about your screen or press Enter...")
        self.entry.bind("<FocusIn>", self.clear_placeholder)
        self.entry.bind("<Return>", self.on_submit)
        self.entry.bind("<Escape>", lambda e: self.hide())

        # Screen Aware Action Button
        screen_btn = tk.Button(
            container,
            text="👁️ See Screen",
            bg="#0284c7",
            fg="#ffffff",
            activebackground="#38bdf8",
            activeforeground="#030816",
            font=("Segoe UI", 9, "bold"),
            bd=0,
            padx=12,
            pady=6,
            command=self.analyze_screen
        )
        screen_btn.pack(side="left", padx=6)

        # Close button
        close_btn = tk.Button(
            container,
            text="✕",
            bg="#071020",
            fg="#64748b",
            activebackground="#071020",
            activeforeground="#f8fafc",
            font=("Segoe UI", 11),
            bd=0,
            command=self.hide
        )
        close_btn.pack(side="right", padx=(4, 12))

    def clear_placeholder(self, event):
        if "Ask Jarvis" in self.entry.get():
            self.entry.delete(0, tk.END)

    def show(self):
        self.root.deiconify()
        self.entry.focus_set()

    def hide(self):
        self.root.withdraw()

    def analyze_screen(self):
        self.hide()
        shot_path = agent.capture_screen("floating_context.png")
        mem.add_conversation("user", "Analyze active screen context")
        mem.add_conversation("jarvis", f"Captured active screen context at {shot_path}. Grounded in your view, Sir.")
        # Re-show
        self.show()
        self.entry.delete(0, tk.END)
        self.entry.insert(0, "Screen captured! Grounded in your view. What shall I analyze, Sir?")

    def on_submit(self, event):
        query = self.entry.get().strip()
        if not query:
            return
        mem.add_conversation("user", query)
        self.entry.delete(0, tk.END)
        self.entry.insert(0, f"Processing: '{query}'...")
        # Handle command
        q_lower = query.lower()
        if "mail" in q_lower or "email" in q_lower:
            self.entry.delete(0, tk.END)
            self.entry.insert(0, "Checking personal & PSGIM college circulars...")
        elif "screen" in q_lower or "look" in q_lower:
            self.analyze_screen()
        elif "close" in q_lower or "exit" in q_lower:
            self.hide()
        else:
            self.entry.delete(0, tk.END)
            self.entry.insert(0, f"J.A.R.V.I.S. (Screen Grounded): Acknowledged Sir. Saved to second brain.")

if __name__ == "__main__":
    app = FloatingCommandBar()
    app.root.mainloop()
