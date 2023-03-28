# Setup Guide: 

#### Python version used: Python 3.7+

#### Non-standard libraries used:
- numpy
- matplotlib
- picamera
<br>- https://picamera.readthedocs.io/en/release-1.13/install.html
<br>mpu6050
<br>- https://github.com/m-rtijn/mpu6050

#### Thymio setup:
- **Guide:** https://github.com/lebalz/thympi
- **Package download:** http://wiki.thymio.org/en:linuxinstall
- Download "aseba_1.5.5_armhf.deb"
- sudo dpkg -i aseba_1.5.5_armhf.deb
- sudo apt-get update && sudo apt-get -f install
- sudo apt-get install python-dbus python-gtk2
- **To initialize:** "asebamedulla ser:name=Thymio-II"
- **To inititalize using python:** _os.system("(asebamedulla ser:name=Thymio-II &) && sleep 0.3")_


