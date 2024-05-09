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

def move(sim, step, x, y):
    global agents, current_mitigation, realtime, count_min, agent_timesteps
    
    agents_move = []
    mitigations = []

    for agent in agents:
        if current_mitigation:
            mitigations += mitigate(agent, sim, step, x, y, current_mitigation)
        agent = (agent[0] + x, agent[1] + y, agent[2])
        agents_move.append(agent)
        

    agents = agents_move
    sim.update_agent_positions(agents)

    if current_mitigation:
        sim.update_mitigation(mitigations)
    
    sim.run_mitigation()
    
    if (realtime.get()):
        count_min += agent_timesteps
        if (count_min >= 60):
            print(count_min)
            count_min = 0
            sim.run(1)

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

def spread(sim):
    if (1 not in (sim.run(1)[0])):
        results = tk.messagebox.askyesno(title="Results", message="Strategy has successfully put the fire out! Would you like to save a GIF for reference?")
        if results:
            save(sim)

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
    global root, speed, realtime, agent_timesteps
    root.destroy()
    root = tk.Tk()
    root.title("Controls")

    config = Config(config_path)
    sim = custom_sim(config)
    step = round(unit_converter(sim.getFiremap().shape, speed) * agent_timesteps)
    print(step)

    # Running
    run_button = tk.Button(root, text="Run", command=lambda: run(sim))
    run_button.pack(pady=5)

    real_time_frame = tk.Frame(root)
    real_time_frame.pack(padx=5, pady=5)

    realtime = tk.BooleanVar()
    fire_button = tk.Button(real_time_frame, text="Spread", command=lambda: spread(sim))
    real_time_check = tk.Checkbutton(real_time_frame, text="Real-time", onvalue=True, offvalue=False, variable=realtime, command=lambda: disable(fire_button))# tk.Checkbutton()

    real_time_check.grid(row=0, column=0)
    fire_button.grid(row=0, column=1)
    
    mid_frame = tk.Frame(root)
    mid_frame.pack(padx=5, pady=5)

    # Directions
    buttons = tk.Frame(mid_frame)
    buttons.pack(padx=5, pady=5)

    up_button = tk.Button(buttons, text="N", command=lambda: move(sim, step, 0, -step))
    up_button.grid(row=0, column=1)

    left_button = tk.Button(buttons, text="W", command=lambda: move(sim, step, -step, 0))
    left_button.grid(row=1, column=0)

    right_button = tk.Button(buttons, text="E", command=lambda: move(sim, step, step, 0))
    right_button.grid(row=1, column=2)

    down_button = tk.Button(buttons, text="S", command=lambda: move(sim, step, 0, step))
    down_button.grid(row=2, column=1)

    nw_button = tk.Button(buttons, text="NW", command=lambda: move(sim, step, -step, -step))
    nw_button.grid(row=0, column=0)

    ne_button = tk.Button(buttons, text="NE", command=lambda: move(sim, step, step, -step))
    ne_button.grid(row=0, column=2)

    sw_button = tk.Button(buttons, text="SW", command=lambda: move(sim, step, -step, step))
    sw_button.grid(row=2, column=0)

    se_button = tk.Button(buttons, text="SE", command=lambda: move(sim, step, step, step))
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
# Dimensions

run_button = tk.Button(root, text="Start", command=lambda: controls())
run_button.pack()

root.mainloop()