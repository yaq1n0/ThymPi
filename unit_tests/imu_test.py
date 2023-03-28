
# testing MPU6050 IMU using mpu6050 module
# source code: https://github.com/m-rtijn/mpu6050

from mpu6050 import mpu6050

import numpy as np

import matplotlib.pyplot as plt

sensor = mpu6050(0x68)

xyz = []

for i in range(100):
    acc_data = sensor.get_gyro_data()
    # returns acc_data in dict form ("x", "y", "z")
    
    xyz.append((acc_data["x"], acc_data["y"], acc_data["z"]))

label = []
x = []
y = []
z = []

for i in range(100):
    label.append(i)
    x.append(xyz[0])
    y.append(xyz[1])
    z.append(xyz[2])
    
#plt.plot(label, x)
#plt.show()

print(z)
                
        
    
    
