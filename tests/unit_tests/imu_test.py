# basic MPU6050 IMU test using mpu6050 python module
# based on: https://github.com/m-rtijn/mpu6050

from mpu6050 import mpu6050

import time
import numpy as np
import matplotlib.pyplot as plt

sensor = mpu6050(0x68)

t, x, y, z = [], [], [], []

print("starting test")
start_time = time.time()
end_time = time.time() + 5

while time.time() <= end_time:
    acc_data = sensor.get_accel_data()
    # returns acc_data in dict form ("x", "y", "z")

    t.append(time.time())
    x.append(acc_data["x"])
    y.append(acc_data["y"])
    z.append(acc_data["z"])

print("ended test")

print("starting plot")
plt.plot(t, x)
plt.plot(t, y)
plt.plot(t, z)

plt.show()

print("finishing plot")
