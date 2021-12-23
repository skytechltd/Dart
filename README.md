# Dart

DART (Detect and avoid Artificial Reality Testing) is an open community benchmarking system to evaluate visual system detect and avoid algorithms for drones and other aircraft.
Our work as of v1.0 reached TRL 4 (proof of concept). We welcome the community to join us in building on these foundations with the vision to have a standardised system to evaluate DAA systems. An overview video of the project is [available here](https://youtu.be/X2zolGSnKZc). 2021 work was funded by the Dft D-Trig program. Our work is released under [Apache License V 2.0]( https://www.apache.org/licenses/LICENSE-2.0.txt).


## Consultancy

If you would like private consultancy on how to setup and use DART in your organisation then please contact Sky Tech directly [david.redpath@skytech.limited](mailto:david.redpath@skytech.limited)


## Scope

DART v1.0 is designed around the scenario of a single aircraft on collision course in good lighting. The input to the system is a single forward-facing video camera. Our initial study looked at criterion effecting this type of DAA system and typical scenarios such a normal flight (no false alarms), single and multiple collision scenarios.  The combinatorial nature of the problem makes testing solutions exhaustive. We were limited to 8 weeks of development so a fair number of assumptions need to be made to complete on time. We chose to drive simulations via AirSim exclusively and avoid locking in development to one particular setup. Therefore, with minimal changes DART will work on Windows/Linux and with Unreal Engine or Unity.


## Overview

DART is built on Microsoft AirSim using Unreal Engine 4. Python along with the AirSim plugin APIs was used to script different collisions. A Flask server is used to stream virtual cameras from the simulation. The simulator code start/stops each DAA algorithm under test. Each of these are Python scripts which read the virtual camera from the Flask server and input consecutive frames into OpenCV functions to assess the collision threat and issue an avoid manoeuvre.  Results on true, missed and false detection were recorded with the detection distance. An overview video of the system working is [available here]( https://youtu.be/n-x_FPCxEYE).

## Contribute

Please look at [open issues]( https://github.com/skytechltd/Dart/issues) if you are looking for areas to contribute to. Our aim is to setup a working group to steer the future of the project, so please join [the discussion here]( https://github.com/skytechltd/Dart/discussions)

## Workstation Setup

* A workstation with sufficient GPU for 3D graphics is advised to run Unreal Engine 4. We describe setup for a Linux workstation running Ubuntu 20.0 and Unreal Engine 4.25.4, but other versions for Windows and Unity are also choices if you prefer.

* Download DART scripts for this project. All our project files were installed within a common user directory /Dart with the following subdirectories:
```
/UnrealEngine - Install UE4 here
/Airsim – install Airsim here
/Benchmarking – benchmarking scripts
/DAA – our DAA scripts
/Models – 3D models from TurboSquid (download your own), import into UE4
/Simulation – this is the UE4 project file
```

* Install Unreal Engine and AirSim following instruction [here]( https://docs.unrealengine.com/4.27/en-US/SharingAndReleasing/Linux/BeginnerLinuxDeveloper/SettingUpAnUnrealWorkflow/) and [here]( https://microsoft.github.io/AirSim/build_linux/). Ensure the default AirSim project is running without errors.


* Due to asset licensing, it’s necessary to create your own ‘Simulation/Simulation.uproject’ project. For simplicity all we added was a ground plane with a texture, the Airsim plugin and the 3D models for our testing. Please build your own conops digital twin from here.


## Running a Simulation

Start Unreal Engine on Linux, open a terminal, in our case all files were installed under the folder /Dart in the user home directory (NOTE: You need to have first created the Simulation.uproject as described below).

* Start UE4
```
cd Dart
./UnrealEngine/Engine/Binaries/Linux/UE4Editor /home/<insertusername>/Dart/Simulation/Simulation.uproject
```

* Setup Airsim config file under ˜/Documents/Airsim/settings.json, see section below on what this should contain.

* In UE4 click play to run in the viewport

* Start streaming server to export stream from UE4 to the DAA algos, open a new terminal
```
cd Dart/Benchmarking
./airSimStream.py
```
* Run the simulation, open a new terminal, results will be written to the file daares.csv. Edit Documents/AirSim/settings.json and set the specific aircraft on collision such as Cessna, Helicopter, PrivateJet.
```
cd Dart/Benchmarking
./runsim.py
```

* Check results, open a new terminal
```
cd Dart/Benchmarking
./showres.py dares.csv
```

## Airsim settings.json

The settings in this file are sensitive and formatting mistakes can cause AirSim/UE4 to freeze. It’s recommended to change and confirm one setting at a time and keep backups of your working settings. We have tried loading several aircraft on the airfield but experienced inconsistent results. We therefore recommend using one aircraft at a time and setting it here. Two default files are provided for SITL and HITL in the repo under /Setup/Airsim

## Setting Up Your Own Simulation

Due to asset licencing and frequent Unreal Engine updates it’s necessary to create and populate your own project and import your own models. Follow this tutorial on the [Airsim pages here]( https://microsoft.github.io/AirSim/unreal_custenv/). There is also a [video here]( https://www.youtube.com/watch?v=1oY8Qu5maQQ). You will also need to import your own aircraft for testing, this can be done by cloning the blueprint of the default Airsim drone and changing the 3D model. Be careful with naming as the wrong format will crash Unreal Engine. One issue is that the new aircraft will still have a drone kinematic model and look awkward in flight. This is a future area of improvement.


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
## Future Work
An original aim of DART was to include augmented reality to test DAA on a real drone in flight. We found this was going to be months/years of work to customise a plugin and firmware for RaspberryPi/Jetson. The tools exisit for Android/iOS devices and it’s possible to stream from a mobile device into the mission computer but such actions were deemed a novelty in the end over conducting solid research.
We found the two DAA algorithms we specified to be sensitive to global movement and unsuitable for practical application. Working on new robust DAA algorithms is therefore essential.
Rejecting false alarms is quite important and it’s expected DART can be used as a starting point in your own conops digital twin.
Supporting different kinematic models is also an area for future improvement such as aeroplanes, helicopters, rockets.

