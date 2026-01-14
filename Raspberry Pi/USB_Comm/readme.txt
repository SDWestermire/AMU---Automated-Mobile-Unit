Note:  

boot.py will be ran on the Raspberry Pi Pico upon boot-up.    One of the primary functions is to enable CDC communications necessary for USB UART bi-directional transmissions

pico2rpi.py:  As the name implies, this code resides on the Raspberry Pi and will communicate AMU status for all sensors, components and mission status.
rpi2pico.py:  As the name implies, communicates to the Pico, via UART USB cable, with all updates and ACK.
