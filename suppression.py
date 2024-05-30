import tkinter as tk
from simfire.sim.simulation import FireSimulation
from simfire.utils.config import Config
import yaml
import math
from threading import Thread
import time

config_path = './configs/model_configs.yml'

class MyFloat:
    def __init__(self, value):
        self.value = value
    def setValue(self, value):
        self.value = float(value)
    def getValue(self):
        return self.value
    
class MyTuple:
    def __init__(self, value):
        self.value = value
    def setValue(self, value):
        self.value = (int(value.split(',')[0].strip(" (")), int(value.split(',')[1].strip(") ")))
    def getValue(self):
        return self.value

class CustomSim(FireSimulation):
    def __init__(self, *args, **kwargs):
        super(CustomSim, self).__init__(*args, **kwargs)

    def run_mitigation(self): # TODO: Fix elapsed time issue, if needed.
        if self._rendering:
            self._render()

    def getFiremap(self):
        return self.fire_map

# Location, Dimensions
lon = MyFloat(None) # Input
lat = MyFloat(None) # Input
x_dimension = MyFloat(None) # Input
y_dimension = MyFloat(None) # Input

# Speeds
speed = MyFloat(None) # Input
agent_timesteps = MyFloat(None) # Seconds # Input

# Positions
init_fire = MyTuple(None) # (350, 350) # Input
num_agents = MyFloat(None) # Input
agent_start_pos = [] # Input

values = [lon, lat, x_dimension, y_dimension, speed, agent_timesteps, init_fire, num_agents]

run_bool = False
current_mitigation = None
realtime = None

agents = []

count_min = 0

current_agent = None

def ping(args):
    args.run(0)
    time.sleep(2)

def run(sim, widgets, fire_button, none_button, buttons_list): # TODO: Add restart functionality.
    global agents, agent_start_pos, run_bool
    run_bool = True
    toggle_widgets(fire_button, widgets)
    disable(fire_button)
    set_mitigation(None, none_button, buttons_list)
    sim.rendering = True

    for i in range(int(num_agents.getValue())):
        agent = (agent_start_pos[i][0], agent_start_pos[i][1], i)
        agents.append(agent)

    sim.update_agent_positions(agents)
    sim.run_mitigation()

    thread = Thread(target = ping, args = (sim, )) # TODO: Explore improvements so programme does not get slowed a lot
    thread.start()
    thread.join()

def sign(x):
    if x == 0:
        return 0
    elif x < 0:
        return -1
    else:
        return 1
    
def mitigate(agent, sim, x, y, current_mitigation):
    step = max(abs(x), abs(y))
    mitigations = []
    for i in range(1, step + 1):
        mitigation = (agent[0] + (i * sign(x)), agent[1] + (i * sign(y)), sim.get_actions()[current_mitigation])
        mitigations.append(mitigation)
        x = x + (1 * -sign(x))
        y = y + (1 * -sign(y))
    
    return mitigations

def check_edge(agent, x, grid):
    if (agent + x >= grid):
        x = grid - agent - 1
    elif (agent + x < 0):
        x = -agent

    return x

def move(sim, x, y, hr, min, sec, grid):
    global agents, current_mitigation, realtime, count_min, agent_timesteps, current_agent
    
    mitigations = []

    if current_agent is not None:
        agent = agents[current_agent]
        x_new = check_edge(agent[0], x, grid[1])
        y_new = check_edge(agent[1], y, grid[0])

        if current_mitigation:
            mitigations += mitigate(agent, sim, x_new, y_new, current_mitigation)
        agent = (agent[0] + x_new, agent[1] + y_new, agent[2])
        agents[current_agent] = agent

    sim.update_agent_positions(agents)

    if current_mitigation:
        sim.update_mitigation(mitigations)
    
    sim.run_mitigation()
    
    if (realtime.get()):
        t = tick(hr, min, sec, agent_timesteps.getValue())
        count_min += agent_timesteps.getValue()
        if (count_min >= 60 or t == 0):
            print(count_min)
            count_min = 0
            spread(sim, t)

def close(sim, fire_button, widgets, buttons_list, agents_list):
    global run_bool, current_agent
    current_agent = None
    sim.rendering = False
    run_bool = False
    reset_buttons(buttons_list)
    reset_buttons(agents_list)
    toggle_widgets(fire_button, widgets)

def save(sim):
    # TODO: Add loading
    sim.save_gif('./out/simfire/out.gif')

def disable(button):
    global count_min, realtime, run_bool
    if (run_bool):
        count_min = 0
        if (realtime.get()):
            button["state"] = "disabled"
        else:
            button["state"] = "normal"

def tick(hr, min, sec, amount):
    time_sec = int(hr.get()) * 3600 + int(min.get()) * 60 + int(sec.get()) - int(amount)
    
    if (time_sec < 0):
        time_sec = 0
    
    temp_m, temp_s = divmod(time_sec, 60)
    temp_h, temp_m = divmod(temp_m, 60)

    sec.set(str(temp_s))
    min.set(str(temp_m))
    hr.set(str(temp_h))

    return time_sec

def spread(sim, t):
    global run_bool

    # Checking winning
    if (1 not in (sim.run(1)[0])):
        results = tk.messagebox.askyesno(title="Results", message="Strategy has successfully put the fire out! Would you like to save a GIF for reference?")
        if results:
            save(sim)
    elif(t <= 0): # Checking losing
        tk.messagebox.showerror(title="Results", message="Strategy has failed within the given time! Please retry or add more time!")

def spread_button(sim, hr, min, sec):
    if (run_bool == True):
        t = tick(hr, min, sec, 60)
        spread(sim, t)

def reset_buttons(buttons):
    for button in buttons:
        button["state"] = "normal"

def set_mitigation(mitigation, button, buttons):
    global current_mitigation
    reset_buttons(buttons)
    button["state"] = "disabled"
    current_mitigation = mitigation

def unit_converter(grid, speed, agent_timesteps):
    global x_dimension, y_dimension
    m_s = speed.getValue() * 1000 / (60 * 60)
    return round((m_s / (x_dimension.getValue() / grid[1])) * agent_timesteps.getValue()), round((m_s / (y_dimension.getValue() / grid[0])) * agent_timesteps.getValue())

def toggle_widgets(fire_button, widgets):
    fire_button["state"] = "disabled"
    for widget in widgets:
        if widget["state"] == "disabled":
            widget["state"] = "normal"
        else:
            widget["state"] = "disabled"

def setValues(entries, agent_start_pos_entry):
    global values
    set_agents_pos(agent_start_pos_entry.get())
    for v in range(len(values)):
        values[v].setValue(entries[v].get())

def set_agents_pos(input):
    global agent_start_pos

    for i in input.split("),"):
        agent_start_pos.append((int(i.split(',')[0].strip(" [](")), int(i.split(',')[1].strip(") []"))))

def modify_config(config_path): # TODO: Add better error-handling
    global lon, lat, x_dimension, y_dimension, init_fire
    
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)

    config['operational']['longitude'] = lon.getValue()
    config['operational']['latitude'] = lat.getValue()
    config['operational']['width'] = int(x_dimension.getValue())
    config['operational']['height'] = int(y_dimension.getValue())
    
    config['fire']['fire_initial_position']['static']['position'] = init_fire.getValue()

    with open(config_path, 'w') as file:
        yaml.safe_dump(config, file)

def even(i):
    if (i % 2 == 0):
        return 1
    else:
        return 0

def setAgent(i, buttons):
    global current_agent
    reset_buttons(buttons)
    buttons[i]["state"] = "disabled"
    current_agent = i

def controls(entries, agent_start_pos_entry):
    global config_path, root, speed, realtime, agent_timesteps, hr, min, sec
    hr_value = hr.get()
    min_value = min.get()
    sec_value = sec.get()
    setValues(entries, agent_start_pos_entry)
    modify_config(config_path)
    root.destroy()

    root = tk.Tk()
    root.title("Controls")

    widgets = []

    config = Config(config_path)
    sim = CustomSim(config)
    grid = sim.getFiremap().shape
    step_x, step_y = unit_converter(grid, speed, agent_timesteps)

    # Timer
    timer_frame = tk.Frame(root)
    timer_frame.pack(pady=5)

    hr = tk.StringVar()
    hr.set(hr_value)
    hr_entry = tk.Entry(timer_frame, textvariable=hr, width=2)
    hr_entry.grid(row=0, column=0)

    min = tk.StringVar()
    min.set(min_value)
    min_entry = tk.Entry(timer_frame, textvariable=min, width=2)
    min_entry.grid(row=0, column=1)

    sec = tk.StringVar()
    sec.set(sec_value)
    sec_entry = tk.Entry(timer_frame, textvariable=sec, width=2)
    sec_entry.grid(row=0, column=2)

    # Running
    fire_button = None
    none_button = None
    buttons_list = []

    run_button = tk.Button(root, text="Run", command=lambda: run(sim, widgets, fire_button, none_button, buttons_list))
    run_button.pack(pady=5)
    widgets.append(run_button)

    run_button["state"] = "disabled"

    real_time_frame = tk.Frame(root)
    real_time_frame.pack(padx=5, pady=5)
    realtime = tk.BooleanVar()
    fire_button = tk.Button(real_time_frame, text="Spread", command=lambda: spread_button(sim, hr, min, sec))
    real_time_check = tk.Checkbutton(real_time_frame, text="Real-time", onvalue=True, offvalue=False, variable=realtime, command=lambda: disable(fire_button))# tk.Checkbutton()

    real_time_check.grid(row=0, column=0)
    fire_button.grid(row=0, column=1)
    
    mid_frame = tk.Frame(root)
    mid_frame.pack(padx=5, pady=5)

    # Directions
    buttons = tk.Frame(mid_frame)
    buttons.pack(padx=5, pady=5)

    up_button = tk.Button(buttons, text="N", command=lambda: move(sim, 0, -step_y, hr, min, sec, grid))
    up_button.grid(row=0, column=1)

    left_button = tk.Button(buttons, text="W", command=lambda: move(sim, -step_x, 0, hr, min, sec, grid))
    left_button.grid(row=1, column=0)

    right_button = tk.Button(buttons, text="E", command=lambda: move(sim, step_x, 0, hr, min, sec, grid))
    right_button.grid(row=1, column=2)

    down_button = tk.Button(buttons, text="S", command=lambda: move(sim, 0, step_y, hr, min, sec, grid))
    down_button.grid(row=2, column=1)

    nw_button = tk.Button(buttons, text="NW", command=lambda: move(sim, -step_x, -step_y, hr, min, sec, grid))
    nw_button.grid(row=0, column=0)

    ne_button = tk.Button(buttons, text="NE", command=lambda: move(sim, step_x, -step_y, hr, min, sec, grid))
    ne_button.grid(row=0, column=2)

    sw_button = tk.Button(buttons, text="SW", command=lambda: move(sim, -step_x, step_y, hr, min, sec, grid))
    sw_button.grid(row=2, column=0)

    se_button = tk.Button(buttons, text="SE", command=lambda: move(sim, step_x, step_y, hr, min, sec, grid))
    se_button.grid(row=2, column=2)

    widgets += buttons.winfo_children()

    # Mitigations Buttons
    mitigation_buttons = tk.Frame(mid_frame)
    mitigation_buttons.pack(padx=5, pady=5)

    none_button = tk.Button(mitigation_buttons, text="None", command=lambda: set_mitigation(None, none_button, buttons_list))
    none_button.grid(row=0, column=0)

    fl_button = tk.Button(mitigation_buttons, text="Fireline", command=lambda: set_mitigation('fireline', fl_button, buttons_list))
    fl_button.grid(row=1, column=0)

    wl_button = tk.Button(mitigation_buttons, text="Wetline", command=lambda: set_mitigation('wetline', wl_button, buttons_list))
    wl_button.grid(row=2, column=0)

    sl_button = tk.Button(mitigation_buttons, text="Scratchline", command=lambda: set_mitigation('scratchline', sl_button, buttons_list))
    sl_button.grid(row=3, column=0)

    buttons_list = mitigation_buttons.winfo_children()
    widgets += mitigation_buttons.winfo_children()

    agent_buttons = []
    # Additional Buttons
    bot_bottons = tk.Frame(root)
    bot_bottons.pack(pady=5)

    close_button = tk.Button(bot_bottons, text="Close", command=lambda: close(sim, fire_button, widgets, buttons_list, agent_buttons))
    close_button.grid(row=0, column=0)

    save_button = tk.Button(bot_bottons, text="Save", command=lambda: save(sim))
    save_button.grid(row=0, column=1)

    widgets += bot_bottons.winfo_children()

    # Agents
    agents_frame = tk.Frame(root)
    agents_frame.pack(pady=5)

    for i in range(int(num_agents.getValue())):
        agent_button = tk.Button(agents_frame, text=f"Agent {i + 1}", command=lambda x = i: setAgent(x, agent_buttons))
        agent_button.grid(row=math.ceil((i + 1)/2) - 1, column=even(i + 1))
    
    agent_buttons += agents_frame.winfo_children()
    widgets += agents_frame.winfo_children()

    toggle_widgets(fire_button, widgets)
    root.mainloop()

root = tk.Tk()
root.title("Practice Tool")

tk.Label(root, text="Welcome to Practice Tool! Please set-up the settings below:").pack()

# Settings:
entries = []

# Timer
timer = tk.Label(root, text="Timer (hr:min:sec)")
timer.pack(pady=5)

timer_frame = tk.Frame(root)
timer_frame.pack()

hr = tk.StringVar()
hr.set("00")
hr_entry = tk.Entry(timer_frame, textvariable=hr, width=2)
hr_entry.grid(row=0, column=0)

min = tk.StringVar()
min.set("00")
min_entry = tk.Entry(timer_frame, textvariable=min, width=2)
min_entry.grid(row=0, column=1)

sec = tk.StringVar()
sec.set("00")
sec_entry = tk.Entry(timer_frame, textvariable=sec, width=2)
sec_entry.grid(row=0, column=2)

# Location, Dimensions
lon_entry = tk.StringVar()
lon_entry.set("-120.05")
tk.Label(root, text="Longitude").pack(pady=(10, 0))
tk.Entry(root, width=20, textvariable=lon_entry).pack(pady=5)
entries.append(lon_entry)

lat_entry = tk.StringVar()
lat_entry.set("38.13")
tk.Label(root, text="Latitude").pack(pady=(10, 0))
tk.Entry(root, width=20, textvariable=lat_entry).pack(pady=5)
entries.append(lat_entry)

width = tk.StringVar()
width.set("30000")
tk.Label(root, text="Width").pack(pady=(10, 0))
tk.Entry(root, width=20, textvariable=width).pack(pady=5)
entries.append(width)

height = tk.StringVar()
height.set("30000")
tk.Label(root, text="Height").pack(pady=(10, 0))
tk.Entry(root, width=20, textvariable=height).pack(pady=5)
entries.append(height)

# Speeds
speed_entry = tk.StringVar()
speed_entry.set("52.3")
tk.Label(root, text="Speed (km/h)").pack(pady=(10, 0))
tk.Entry(root, width=20, textvariable=speed_entry).pack(pady=5)
entries.append(speed_entry)

agent_timesteps_entry = tk.StringVar()
agent_timesteps_entry.set("5")
tk.Label(root, text="Length of Agent's Timestep (seconds)").pack(pady=(10, 0))
tk.Entry(root, width=20, textvariable=agent_timesteps_entry).pack(pady=5)
entries.append(agent_timesteps_entry)

# Positions
init_fire_entry = tk.StringVar()
init_fire_entry.set("(350, 350)")
tk.Label(root, text="Initial Fire Position (x, y)").pack(pady=(10, 0))
tk.Entry(root, width=20, textvariable=init_fire_entry).pack(pady=5)
entries.append(init_fire_entry)

num_agents_entry = tk.StringVar()
num_agents_entry.set("1")
tk.Label(root, text="Number of Agents").pack(pady=(10, 0))
tk.Entry(root, width=20, textvariable=num_agents_entry).pack(pady=5)
entries.append(num_agents_entry)

agent_start_pos_entry = tk.StringVar()
agent_start_pos_entry.set("[(340, 340)]")
tk.Label(root, text="Agents' Initial Positions [(x, y), ...]").pack(pady=(10, 0))
tk.Entry(root, width=20, textvariable=agent_start_pos_entry).pack(pady=5)

run_button = tk.Button(root, text="Start", command=lambda: controls(entries, agent_start_pos_entry))
run_button.pack()

# TODO: Add "Other" settings for configurations
tk.Label(root, text=f"To adjust further enviromental configurations, please refer to the config file at {config_path}").pack(padx=10)

root.mainloop()