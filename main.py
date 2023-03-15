import matplotlib.pyplot as plt
import matplotlib.animation as animation
from cool import Drawpicture, Trajectory 


homework = Drawpicture(length_EW = 2e4, zoom = 0.5)
homework.calculate_M()
homework.calculate_H()
homework.refresh_overlap()
homework.calculate_B()
homework.calculate_num_pics()
homework.calculate_exposure()

homework.create_blank_image()
homework.draw_picture()

fig, ax = plt.subplots()
x, y = homework.get_xy()
line, = ax.plot(x, y)

def animate(i):
    if len(ax.lines) == 2:
        ax.lines.pop(1)
    ax.plot(x[i], y[i], 'o', color='red')
    return line, ax

ani = animation.FuncAnimation(
    fig, animate, frames=len(x), interval=1, blit=False, save_count=5)
ani.save("trajectory.gif")
plt.show()

