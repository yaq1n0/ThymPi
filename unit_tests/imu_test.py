
# testing MPU6050 IMU using mpu6050 module
# source code: https://github.com/m-rtijn/mpu6050

from mpu6050 import mpu6050

import time
import numpy as np
import matplotlib.pyplot as plt

sensor = mpu6050(0x68)

t, x, y, z = [], [], [], []

start_time = time.process_time_ns()
end_time = time.process_time_ns() + (5 * 1000000000) # 5 seconds

while time.process_time_ns() <= end_time:
    acc_data = sensor.get_gyro_data()
    # returns acc_data in dict form ("x", "y", "z")

    t.append(time.process_time_ns())
    x.append(acc_data["x"])
    y.append(acc_data["y"])
    z.append(acc_data["z"])

plt.plot(t, x)
plt.plot(t, y)
plt.plot(t, z)

plt.show()

                
        
    
    
