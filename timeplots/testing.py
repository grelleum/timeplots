# Move me to a Jupyter notebook

import random


def random_numbers(max_values=60):
    current = random.randrange(20, 40)
    for _ in range(max_values):
        modifier = random.randrange(1, 3)
        modifier = modifier if random.randint(0, 1) else 0 - modifier
        current += modifier
        yield current


times = [datetime(2019, 12, 1, 0, t) for t in range(60)]


plotter = timeplots.Plotter(width=900)
plotter.new_plot("Stuff happening", "stuff/period")

for index in range(8):
    data = list(random_numbers())
    plotter.add_line(f"D{index}P", times, data)

plotter.render()
