import matplotlib.pyplot as plt
import matplotlib.animation as animation
from cool import Drawpicture, Trajectory, Regulation, Point

def animate(i):
    #画动点图函数
    if len(ax.lines) == 2:
        ax.lines.pop(1)
    ax.plot(x[i], y[i], 'o', color='red')
    return line, ax

#画矩形区域航迹规划
""" homework = Drawpicture(zoom = 0.5)
homework.calculate_M()
homework.calculate_H()
homework.refresh_overlap()
homework.calculate_B()
homework.calculate_num_pics_rect()
homework.calculate_exposure()
homework.create_blank_image()
homework.draw_picture()
fig, ax = plt.subplots()
x, y = homework.get_xy()
line, = ax.plot(x, y)
ax.set_aspect(aspect=1)

ani = animation.FuncAnimation(
    fig, animate, frames=len(x), interval=1, blit=False, save_count=5)
#ani.save("trajectory.gif")
plt.show()
 """


#输入多边形坐标
A = Point(1000, 2000)
B = Point(2000, 10000)
C = Point(4000, 20000)
D = Point(12000, 9000)
E = Point(8000, 3000)
List = [A, B, C, D, E]
#进行多边形平移旋转简化
regulation = Regulation(List)
regulation.get_angle()
regulation.turn_Polygen()
#计算各项参数
homework = Drawpicture()
homework.calculate_M()
homework.calculate_H()
homework.refresh_overlap()
homework.calculate_B()
x, y =homework.calculate_num_pics_polygen(regulation.edge_points)
homework.calculate_exposure()
#绘图（不提供带有覆盖范围的opencv绘图）
fig, ax = plt.subplots()
line, = ax.plot(x, y)
ax.set_aspect(aspect=1)

ani = animation.FuncAnimation(
    fig, animate, frames=len(x), interval=1, blit=False, save_count=5)
#ani.save("trajectory.gif")
plt.show()

