
# live plotting of MPU6050 data
# source code for mpu6050 library: https://github.com/m-rtijn/mpu6050
# code for live plotting: https://learn.sparkfun.com/tutorials/graph-sensor-data-with-python-and-matplotlib/update-a-graph-in-real-time

from mpu6050 import mpu6050

import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation


def animateX(i, t, x):
    acc_data = sensor.get_accel_data(g=False)
    t.append(time.process_time_ns())
    x.append(acc_data["x"])

    t = t[-500:]
    x = x[-500:]

    ax.clear()
    ax.plot(t, x)

    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.30)
    plt.title('MPU6050 x-axis readings live')


def animateY(i, t, y):
    acc_data = sensor.get_accel_data(g=False)
    t.append(time.process_time_ns())
    y.append(acc_data["y"])

    t = t[-500:]
    y = y[-500:]

    ax.clear()
    ax.plot(t, x)

    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.30)
    plt.title('MPU6050 y-axis readings live')


def animateZ(i, t, z):
    acc_data = sensor.get_accel_data(g=False)
    t.append(time.process_time_ns())
    z.append(acc_data["z"])

    t = t[-500:]
    z = z[-500:]

    ax.clear()
    ax.plot(t, x)

    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.30)
    plt.title('MPU6050 z-axis readings live')


if __name__ == '__main__':
    # setting up sensor instance
    sensor = mpu6050(0x68)

    # setting up value store
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    t, x, y, z = [], [], [], []

    ani = animation.FuncAnimation(fig, animateX, fargs=(t, x), interval=100)
    # ani = animation.FuncAnimation(fig, animateY, fargs=(t,y), interval=100)
    # ani = animation.FuncAnimation(fig, animateZ, fargs=(t,z), interval=100)

    plt.show()
