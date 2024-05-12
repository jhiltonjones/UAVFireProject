import tkinter as tk
from simfire.sim.simulation import FireSimulation
from simfire.utils.config import Config

config_path = './configs/model_configs.yml'

# Speed: ~52.30024 km/h
speed = 52.3 # Input
agent_timesteps = 5 # Seconds # Input

num_agents = 1 # Input
start_pos = [(340, 340)] # Input
init_fire = (350, 350) # Input

# lat = # Input
# long = # Input
x_dimension = 30000 # Input
y_dimension = 30000 # Input



agents = []

current_mitigation = None

realtime = None
count_min = 0

class custom_sim(FireSimulation):
    def __init__(self, *args, **kwargs):
        super(custom_sim, self).__init__(*args, **kwargs)

    def run_mitigation(self):
        if self._rendering:
            self._render()

    def getFiremap(self):
        return self.fire_map

def run(sim):
    global agents, start_pos
    sim.rendering = True

    for i in range(num_agents):
        agent = (start_pos[i][0], start_pos[i][1], i)
        agents.append(agent)

    sim.update_agent_positions(agents)
    sim.run_mitigation()

def sign(x):
    if x == 0:
        return 0
    elif x < 0:
        return -1
    else:
        return 1
    
def mitigate(agent, sim, step, x, y, current_mitigation):
    mitigations = []
    for i in range(1, step + 1):
        mitigation = (agent[0] + (i * sign(x)), agent[1] + (i * sign(y)), sim.get_actions()[current_mitigation])
        mitigations.append(mitigation)
    
    return mitigations

def check_edge(agent, x, grid):
    if (agent + x >= grid):
        x = grid - agent - 1
    elif (agent + x < 0):
        x = -agent

    return x

def move(sim, step, x, y, hr, min, sec, grid):
    global agents, current_mitigation, realtime, count_min, agent_timesteps
    
    agents_move = []
    mitigations = []

    for agent in agents:
        x_new = check_edge(agent[0], x, grid[1])
        y_new = check_edge(agent[1], y, grid[0])

        if current_mitigation:
            mitigations += mitigate(agent, sim, step, x_new, y_new, current_mitigation)
        agent = (agent[0] + x_new, agent[1] + y_new, agent[2])
        agents_move.append(agent)


    agents = agents_move
    sim.update_agent_positions(agents)

    if current_mitigation:
        sim.update_mitigation(mitigations)
    
    sim.run_mitigation()
    
    if (realtime.get()):
        t = tick(hr, min, sec, agent_timesteps)
        count_min += agent_timesteps
        if (count_min >= 60 or t == 0):
            print(count_min)
            count_min = 0
            spread(sim, t)

def close(sim):
    sim.rendering = False

def save(sim):
    # TODO: Add loading
    sim.save_gif('./out/simfire/out.gif')

def disable(button):
    global count_min, realtime
    count_min = 0
    if button["state"] == "disabled":
        button["state"] = "normal"
    elif button["state"] == "normal":
        button["state"] = "disabled"
    
    print(realtime.get())

def tick(hr, min, sec, amount):
    time_sec = int(hr.get()) * 3600 + int(min.get()) * 60 + int(sec.get()) - amount
    
    if (time_sec < 0):
        time_sec = 0
    
    temp_m, temp_s = divmod(time_sec, 60)
    temp_h, temp_m = divmod(temp_m, 60)

    sec.set(str(temp_s))
    min.set(str(temp_m))
    hr.set(str(temp_h))

    return time_sec


def spread(sim, t):
    # Checking winning
    if (1 not in (sim.run(1)[0])):
        results = tk.messagebox.askyesno(title="Results", message="Strategy has successfully put the fire out! Would you like to save a GIF for reference?")
        if results:
            save(sim)
    elif(t <= 0): # Checking losing
        tk.messagebox.showerror(title="Results", message="Strategy has failed within the given time! Please retry or add more time!")

def spread_button(sim, hr, min, sec):
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

def unit_converter(grid, speed): # TODO: Add support to non-square scenarios
    global x_dimension
    m_m = speed * 1000 / (60 * 60)
    return m_m / (x_dimension / grid[0])

def controls():
    global root, speed, realtime, agent_timesteps, hr, min, sec
    hr_value = hr.get()
    min_value = min.get()
    sec_value = sec.get()
    root.destroy()
    root = tk.Tk()
    root.title("Controls")

    config = Config(config_path)
    sim = custom_sim(config)
    grid = sim.getFiremap().shape
    step = round(unit_converter(grid, speed) * agent_timesteps)

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
    run_button = tk.Button(root, text="Run", command=lambda: run(sim))
    run_button.pack(pady=5)

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

    up_button = tk.Button(buttons, text="N", command=lambda: move(sim, step, 0, -step, hr, min, sec, grid))
    up_button.grid(row=0, column=1)

    left_button = tk.Button(buttons, text="W", command=lambda: move(sim, step, -step, 0, hr, min, sec, grid))
    left_button.grid(row=1, column=0)

    right_button = tk.Button(buttons, text="E", command=lambda: move(sim, step, step, 0, hr, min, sec, grid))
    right_button.grid(row=1, column=2)

    down_button = tk.Button(buttons, text="S", command=lambda: move(sim, step, 0, step, hr, min, sec, grid))
    down_button.grid(row=2, column=1)

    nw_button = tk.Button(buttons, text="NW", command=lambda: move(sim, step, -step, -step, hr, min, sec, grid))
    nw_button.grid(row=0, column=0)

    ne_button = tk.Button(buttons, text="NE", command=lambda: move(sim, step, step, -step, hr, min, sec, grid))
    ne_button.grid(row=0, column=2)

    sw_button = tk.Button(buttons, text="SW", command=lambda: move(sim, step, -step, step, hr, min, sec, grid))
    sw_button.grid(row=2, column=0)

    se_button = tk.Button(buttons, text="SE", command=lambda: move(sim, step, step, step, hr, min, sec, grid))
    se_button.grid(row=2, column=2)

    # Mitigations Buttons
    mitigation_buttons = tk.Frame(mid_frame)
    mitigation_buttons.pack(padx=5, pady=5)

    buttons_list = []

    none_button = tk.Button(mitigation_buttons, text="None", command=lambda: set_mitigation(None, none_button, buttons_list))
    none_button.grid(row=0, column=0)

    none_button["state"] = "disabled"

    fl_button = tk.Button(mitigation_buttons, text="Fireline", command=lambda: set_mitigation('fireline', fl_button, buttons_list))
    fl_button.grid(row=1, column=0)

    wl_button = tk.Button(mitigation_buttons, text="Wetline", command=lambda: set_mitigation('wetline', wl_button, buttons_list))
    wl_button.grid(row=2, column=0)

    sl_button = tk.Button(mitigation_buttons, text="Scratchline", command=lambda: set_mitigation('scratchline', sl_button, buttons_list))
    sl_button.grid(row=3, column=0)

    buttons_list = [none_button, fl_button, wl_button, sl_button]

    # Additional Buttons
    bot_bottons = tk.Frame(root)
    bot_bottons.pack(pady=5)

    close_button = tk.Button(bot_bottons, text="Close", command=lambda: close(sim))
    close_button.grid(row=0, column=0)

    save_button = tk.Button(bot_bottons, text="Save", command=lambda: save(sim))
    save_button.grid(row=0, column=1)


root = tk.Tk()
root.title("Practice Tool")

tk.Label(root, text="Welcome to Practice Tool! Please set-up the settings below:").pack()

# TODO: Add settings:

# Timer
timer = tk.Label(root, text="Timer")
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

# Dimensions

run_button = tk.Button(root, text="Start", command=lambda: controls())
run_button.pack()

root.mainloop()