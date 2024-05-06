import tkinter as tk
from simfire.sim.simulation import FireSimulation
from simfire.utils.config import Config

config_path = './configs/model_configs.yml'

# Speed: ~52.30024 km/h # TODO: Auto unit converter
speed = 2 # Pixels = ~30 meters
agent_timesteps = 5 # Seconds

num_agents = 1
start_pos = [(340, 340)]
init_fire = (350, 350)



agents = []

current_mitigation = 'fireline'

realtime = None
count_min = 0

class custom_sim(FireSimulation):
    def __init__(self, *args, **kwargs):
        super(custom_sim, self).__init__(*args, **kwargs)

    def run_mitigation(self):
        if self._rendering:
            self._render()

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
    
def mitigate(agent, sim, x, y, current_mitigation):
    global speed

    mitigations = []
    for i in range(1, speed + 1):
        mitigation = (agent[0] + (i * sign(x)), agent[1] + (i * sign(y)), sim.get_actions()[current_mitigation])
        mitigations.append(mitigation)
    
    return mitigations

def move(sim, x, y):
    global agents, current_mitigation, realtime, count_min, agent_timesteps
    
    agents_move = []
    mitigations = []

    for agent in agents:
        mitigations += mitigate(agent, sim, x, y, current_mitigation)
        agent = (agent[0] + x, agent[1] + y, agent[2])
        agents_move.append(agent)
        print(mitigations)
        print(agent)
        

    agents = agents_move
    sim.update_agent_positions(agents)

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
    sim.save_gif('./out/simfire/out.gif')
    # sim.save_spread_graph('./out/simfire/graph.png')

def disable(button):
    global count_min, realtime

    count_min = 0
    if button["state"] == "disabled":
        button["state"] = "normal"
    elif button["state"] == "normal":
        button["state"] = "disabled"
    
    print(realtime.get())

def spread(sim):
    sim.run(1)

def controls():
    global root, speed, realtime
    root.destroy()
    root = tk.Tk()
    root.title("Controls")

    config = Config(config_path)
    sim = custom_sim(config)

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
    

    # Directions
    buttons = tk.Frame(root)
    buttons.pack(padx=5, pady=5)

    up_button = tk.Button(buttons, text="N", command=lambda: move(sim, 0, -speed))
    up_button.grid(row=0, column=1)

    left_button = tk.Button(buttons, text="W", command=lambda: move(sim, -speed, 0))
    left_button.grid(row=1, column=0)

    right_button = tk.Button(buttons, text="E", command=lambda: move(sim, speed, 0))
    right_button.grid(row=1, column=2)

    down_button = tk.Button(buttons, text="S", command=lambda: move(sim, 0, speed))
    down_button.grid(row=2, column=1)

    nw_button = tk.Button(buttons, text="NW", command=lambda: move(sim, -speed, -speed))
    nw_button.grid(row=0, column=0)

    ne_button = tk.Button(buttons, text="NE", command=lambda: move(sim, speed, -speed))
    ne_button.grid(row=0, column=2)

    sw_button = tk.Button(buttons, text="SW", command=lambda: move(sim, -speed, speed))
    sw_button.grid(row=2, column=0)

    se_button = tk.Button(buttons, text="SE", command=lambda: move(sim, speed, speed))
    se_button.grid(row=2, column=2)

    # TODO: Mitigations Buttons

    # Additional Buttons
    bot_bottons = tk.Frame(root)
    bot_bottons.pack(pady=5)

    close_button = tk.Button(bot_bottons, text="Close", command=lambda: close(sim))
    close_button.grid(row=0, column=0)

    save_button = tk.Button(bot_bottons, text="Save", command=lambda: save(sim))
    save_button.grid(row=0, column=1)


root = tk.Tk()
root.title("Practice Tool")

tk.Label(text="Welcome to Practice Tool! Please set-up the settings below:").pack()

# TODO: Add settings

run_button = tk.Button(root, text="Start", command=lambda: controls())
run_button.pack()

root.mainloop()