# Dart

DART (Detect and avoid Artificial Reality Testing) is an open community benchmarking system to evaluate detect and avoid algorithms using a camera system for drones and other aircraft.
Our work as to v1.0 reached TRL 4 (proof of concept). We welcome the community to join us in building on these foundations with the vision to have a standardised system to evaluate DAA systems. An overview video of the project is [available here](https://youtu.be/X2zolGSnKZc). Our work in 2021 was funded by the Dft D-Trig program and is released under [Apache License v2.0]( https://www.apache.org/licenses/LICENSE-2.0.txt).


## Scope

DART v1.0 is designed around the scenario of deecting a single aircraft on a collision course in good lighting. The input to the system is a single forward-facing video camera. Our initial study looked at criterion effecting this type of DAA system and typical scenarios such a normal flight (no false alarms), single and multiple collision scenarios.  The combinatorial nature of the problem makes testing solutions exhaustive. We were limited to 8 weeks of development so a fair number of assumptions need to be made to complete on time. We chose to drive simulations via AirSim exclusively and avoid locking in development to one particular setup. Therefore, with minimal changes DART will work on Windows/Linux and with Unreal Engine or Unity.


## Overview

DART is built on Microsoft AirSim using Unreal Engine 4. Python along with the AirSim plugin APIs was used to script different collisions. A Flask server is used to stream virtual cameras from the simulation. The simulator code start/stops each DAA algorithm under test. Each of these are Python scripts which read the virtual camera from the Flask server and input consecutive frames into OpenCV functions to assess the collision threat and issue an avoid manoeuvre.  Results on true, missed and false detection were recorded with the detection distance.

## Contribute

Please look at [open issues]( https://github.com/skytechltd/Dart/issues) if you are looking for areas to contribute to. Our aim is to setup a working group to steer the future of the project, so please join [the discussion here]( https://github.com/skytechltd/Dart/discussions)


## Workstation Setup

*A workstation with sufficient GPU for 3D graphics is advised to run Unreal Engine 4. We describe setup for a Linux workstation running Ubuntu 20.0 and Unreal Engine 4, but Windows and Unity are also choices if you prefer.

* Download DART scripts for this project. All our project files were installed within a common user directory /Dart with the following subdirectories:

UnrealEngine - Install UE4 here
Airsim – install Airsim here
DAA – our DAA scripts
Models – Downloaded 3D models from TurboSquid (download your own)
Setup - AirSim
Benchmarking – benchmarking scripts
Simulation – this is the UE4 project file

*Install Unreal Engine and AirSim following instruction [here]( https://docs.unrealengine.com/4.27/en-US/SharingAndReleasing/Linux/BeginnerLinuxDeveloper/SettingUpAnUnrealWorkflow/) and [here]( https://microsoft.github.io/AirSim/build_linux/). Ensure the default AirSim


* Due to asset licensing, it’s necessary to create your own ‘Simulation/Simulation.uproject’ project. For simplicity all we added was a ground plane with a texture, the Airsim plugin and the 3D models.


## Running a Simulation

Start Unreal Engine on Linux, open a terminal, in our case all files were installed under the folder /Dart in the home directory

* Start UE4
‘’’
cd Dart
./UnrealEngine/Engine/Binaries/Linux/UE4Editor /home/<insertusername>/Dart/Simulation/Simulation.uproject
‘’’

* Setup Airsim config file under ˜/Documents/Airsim/settings.json, see section below on what this should contain.

* In UE4 click start

* Start streaming server, open a new terminal
‘’’
cd Dart/Benchmarking
./airSimStream.py
‘’’
* Run the simulation, open a new terminal, results will be written to the file daares.csv. Edit Documents/AirSim/settings.json and set the specific aircraft on collision such as Cessna, Helicopter, PrivateJet.

cd Dart/Benchmarking
./runsim.py


* Check results, open a new terminal

cd Dart/Benchmarking
./showres.py dares.csv


## Airsim settings.json

The settings in this file are sensitive and formatting mistakes can cause AirSim/UE4 to freeze. It’s recommended to change and confirm one setting at a time and keep backups of your working settings. We have tried loading several aircraft on the airfield but experienced inconsistent results. We therefore recommend using one aircraft at a time and setting it here.

??? SITL/HITL

## Setting Up Your Own Simulation

?? How to add models



## HITL Raspberry Pi

If you wish to run DAA algorithms on real hardware you can. We used a Raspberry Pi but any Linux based PC should be fine (Jetson,NUC,etc). We also used the camera module on Pi to use it as an actual DAA system but have not yet tested on a physical drone in flight. Future work will add augmented reality collision to this project but we found doing so isn’t trivial without months of development work. Android/iOS make this easy but support is only available for off the shelf mobile devices. Supporting the Pi on Unreal Engine would be a long journey and a stripped down 3D sim would be more suitable. Our setup is motivated to allow the mission controller (Pi) to issue avoid manoeuvres to the flight controller (PX4-Offboard mode) via Mavlink.

* Install Pi Ubuntu image to sdcard and boot, do all the install steps…
* Update $sudo apt-get update, $sudo apt-get upgrade
* Install packages $sudo apt install vim ifconfig openssh-server
* Enable the uart on pins 8,10, via $vim /boot/firmware/config.txt - add the line ‘enable_uart=1’
* Install packages $sudo apt install python3-pip
* Install mavsdk via $pip3 install mvsdk
* For the video camera. connect up hardware correctly (check schematic for the Pi4 that you re using the CSI port not the DSI port) . Edit config  $vim /boot/firmware/config.txt - add the line ‘start_x=1’ $sudo apt-get instll v4l-tools, check camera is found with $v4l2-ctl --list-devices $sudo apt install ffmpeg. Now run $ffplay /dev/video0 and you should see the camera output.
* Install git $sudo apt-get install, $git clone https://github.com/skytechltd/Dart
* Install python packages $pip install opencv-python matplotlib scipy
* On the simulation workstation check firewall ports are open to access the video stream.
![image](https://user-images.githubusercontent.com/13902794/147113991-2b1332a4-7b16-43f5-a292-8eacb84ca144.png)

