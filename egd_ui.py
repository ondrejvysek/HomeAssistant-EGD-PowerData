import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import filedialog
from tkcalendar import DateEntry
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import json
import os
from egd_api import EGDAPI  # Ensure egd_api.py is in the same directory

chart_canvas = None  # To store the current chart canvas
CONFIG_FILE = "config.json"  # File to store client ID, secret, and EAN

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    return {}

def save_config(client_id, client_secret, meter_id):
    with open(CONFIG_FILE, "w") as file:
        json.dump({"client_id": client_id, "client_secret": client_secret, "meter_id": meter_id}, file)

def fetch_and_display():
    global chart_canvas

    client_id = client_id_entry.get()
    client_secret = client_secret_entry.get()
    meter_id = meter_id_entry.get()
    interval = date_range_combobox.get()
    profile_selection = profile_combobox.get()
    aggregation = aggregation_combobox.get()
    start_date = start_date_entry.get_date() if hasattr(start_date_entry, 'get_date') else start_date_entry.get()
    end_date = end_date_entry.get_date() if hasattr(end_date_entry, 'get_date') else end_date_entry.get()

    if not client_id or not client_secret or not meter_id:
        messagebox.showerror("Error", "Please fill in all required fields!")
        return

    save_config(client_id, client_secret, meter_id)

    profilec = "ICC1" if "C Profiles" in profile_selection else "ICQ2"
    profilep = "ISC1" if "C Profiles" in profile_selection else "ISQ2"

    try:
        api = EGDAPI(client_id, client_secret, meter_id, debug=True)
        token = api.get_token()

        if not token:
            messagebox.showerror("Error", "Failed to retrieve token. Check credentials.")
            return

        data = None
        datac = None
        datap = None
        if interval == "Own Interval":
            if not start_date or not end_date:
                messagebox.showerror("Error", "Please specify start and end dates for Own Interval.")
                return
            datac = api.get_data("interval", profilec, start_date.strftime('%d.%m.%Y'), end_date.strftime('%d.%m.%Y'))
            datap = api.get_data("interval", profilep, start_date.strftime('%d.%m.%Y'), end_date.strftime('%d.%m.%Y'))
        elif interval == "Year to Date":
            if not start_date:
                messagebox.showerror("Error", "Please specify a start date for Year to Date.")
                return
            datac = api.get_data("ytd", profilec, start_date.strftime('%d.%m.%Y'))
            datap = api.get_data("ytd", profilec, start_date.strftime('%d.%m.%Y'))
        else:
            datac = api.get_data(interval.lower().replace(" ", ""), profilec)
            datap = api.get_data(interval.lower().replace(" ", ""), profilep)

        if not datac or not datap:
            messagebox.showerror("Error", "No data retrieved.")
            return

        aggregated_datac = api.sum_data(datac, aggregation.lower())
        aggregated_datap = api.sum_data(datap, aggregation.lower())
        inverted_data = api.invert_data(aggregated_datac)

        if chart_canvas:
            chart_canvas.get_tk_widget().destroy()  # Remove previous chart

        display_chart(aggregated_datap, inverted_data)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def display_chart(consumption_data, production_data):
    global chart_canvas

    figure = plt.Figure(figsize=(6, 4), dpi=100)
    ax = figure.add_subplot(111)

    dates = list(consumption_data.keys())
    consumption = list(consumption_data.values())
    production = list(production_data.values())

    ax.plot(dates, consumption, label="Consumption", marker="o")
    ax.plot(dates, production, label="Production", marker="x")

    # Add labels to the data points
    for i, txt in enumerate(consumption):
        ax.annotate(f'{txt}', (dates[i], consumption[i]), textcoords="offset points", xytext=(0,10), ha='center')
    for i, txt in enumerate(production):
        ax.annotate(f'{txt}', (dates[i], production[i]), textcoords="offset points", xytext=(0,10), ha='center')


    ax.set_title("Energy Consumption and Production")
    ax.set_xlabel("Date")
    ax.set_ylabel("Energy (kWh)")
    ax.legend()
    ax.grid(True)

    chart_canvas = FigureCanvasTkAgg(figure, chart_frame)
    chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    chart_canvas.draw()

app = tk.Tk()
app.title("EGD API Data Viewer")
app.geometry("900x500")

config = load_config()

# Input fields
input_frame = tk.Frame(app)
input_frame.pack(pady=10)

# First line: Client ID, Client Secret, EAN
tk.Label(input_frame, text="Client ID:").grid(row=0, column=0, padx=5, pady=5)
client_id_entry = tk.Entry(input_frame, width=25)
client_id_entry.grid(row=0, column=1, padx=5, pady=5)
client_id_entry.insert(0, config.get("client_id", ""))

tk.Label(input_frame, text="Client Secret:").grid(row=0, column=2, padx=5, pady=5)
client_secret_entry = tk.Entry(input_frame, width=25)
client_secret_entry.grid(row=0, column=3, padx=5, pady=5)
client_secret_entry.insert(0, config.get("client_secret", ""))

tk.Label(input_frame, text="Meter ID (EAN):").grid(row=0, column=4, padx=5, pady=5)
meter_id_entry = tk.Entry(input_frame, width=25)
meter_id_entry.grid(row=0, column=5, padx=5, pady=5)
meter_id_entry.insert(0, config.get("meter_id", ""))

# Second line: Date Range, Start Date, End Date
tk.Label(input_frame, text="Date Range:").grid(row=1, column=0, padx=5, pady=5)
date_range_combobox = ttk.Combobox(input_frame, values=["Yesterday", "This Week", "Last Week", "This Month", "Last Month", "Year to Date", "Own Interval"], width=22)
date_range_combobox.grid(row=1, column=1, padx=5, pady=5)
date_range_combobox.set("Yesterday")

tk.Label(input_frame, text="Start Date:").grid(row=1, column=2, padx=5, pady=5)
start_date_entry = DateEntry(input_frame, width=22, date_pattern='dd.mm.yyyy')
start_date_entry.grid(row=1, column=3, padx=5, pady=5)

tk.Label(input_frame, text="End Date:").grid(row=1, column=4, padx=5, pady=5)
end_date_entry = DateEntry(input_frame, width=22, date_pattern='dd.mm.yyyy')
end_date_entry.grid(row=1, column=5, padx=5, pady=5)

# Third line: Profile, Aggregation, Button
tk.Label(input_frame, text="Profile:").grid(row=2, column=0, padx=5, pady=5)
profile_combobox = ttk.Combobox(input_frame, values=["C Profiles (ICC1/ISC1)", "Q Profiles (ICQ2/ISQ2)"], width=22)
profile_combobox.grid(row=2, column=1, padx=5, pady=5)
profile_combobox.set("C Profiles (ICC1/ISC1)")

tk.Label(input_frame, text="Aggregation:").grid(row=2, column=2, padx=5, pady=5)
aggregation_combobox = ttk.Combobox(input_frame, values=["Daily", "Weekly", "Monthly", "All"], width=22)
aggregation_combobox.grid(row=2, column=3, padx=5, pady=5)
aggregation_combobox.set("Daily")

fetch_button = tk.Button(input_frame, text="Get Data", command=fetch_and_display)
fetch_button.grid(row=2, column=4, columnspan=2, padx=5, pady=5)

# Chart frame
chart_frame = tk.Frame(app)
chart_frame.pack(fill=tk.BOTH, expand=True)

app.mainloop()
