import tkinter as tk
from simfire.sim.simulation import FireSimulation
from simfire.utils.config import Config

config_path = './configs/model_configs.yml'
speed = 1
num_agents = 1
start_pos = [(340, 340)]
init_fire = (350, 350)

agents = []

current_mitigation = 'fireline'

class custom_sim(FireSimulation):
    def __init__(self, *args, **kwargs):
        super(custom_sim, self).__init__(*args, **kwargs)

    def run_mitigation(self, time):
        self.fire_sprites = self.fire_manager.sprites

        if self._rendering:
            self._render()
        
        if self.config.simulation.save_data:
            self._save_data()

def run(sim):
    global agents, start_pos
    sim.rendering = True

    for i in range(num_agents):
        agent = (start_pos[i][0], start_pos[i][1], i)
        agents.append(agent)

    sim.update_agent_positions(agents)

    sim.run_mitigation(1)

def move(sim, x, y):
    global agents, current_mitigation
    agents_move = []
    mitigations = []

    for agent in agents:
        agent = (agent[0] + x, agent[1] + y, agent[2])
        agents_move.append(agent)

        mitigation = (agent[0], agent[1], sim.get_actions()[current_mitigation])
        mitigations.append(mitigation)

    agents = agents_move
    sim.update_agent_positions(agents)

    sim.update_mitigation(mitigations)
    
    sim.run_mitigation(1)

def close(sim):
    sim.rendering = False

def save(sim):
    sim.save_gif('./out/simfire/out.gif')
    # sim.save_spread_graph('./out/simfire/graph.png')

def controls():
    global root, speed
    root.destroy()
    root = tk.Tk()
    root.title("Controls")

    config = Config(config_path)
    sim = custom_sim(config)

    # Running
    run_button = tk.Button(root, text="Run", command=lambda: run(sim))
    run_button.pack(pady=5)

    fire_button = tk.Button(root, text="Spread", command=lambda: sim.run(1))
    fire_button.pack(pady=5)

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

run_button = tk.Button(root, text="Start", command=lambda: controls())
run_button.pack()

root.mainloop()