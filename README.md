#**CANaconda**
==========
CANaconda is a flexible, open source CAN network monitoring tool under development by the UCSC Autonomous System Lab.

![demo](http://i39.tinypic.com/2gxebg4.jpg)


##System Requirements
PC with Python version 3.3 or higher

Lawicel CAN-USB bridge 

Installation of the pySerial package from http://pyserial.sourceforge.net/pyserial.html

Installation of the matplotlib package from matplotlib.org (optional)

Installation of Qt framework, version 5, available from qt-project.org (optional - for GUI only)

Installation of PyQt5 package from riverbankcomputing.com (optional - for GUI only)


##Running CANaconda
Connect USB and CAN cables. The CAN network must have its own power supply. Launch the program from the command line or by double clicking the canpython.py file.

Load filters from an XML file by clicking action-> Load filters. See README found in [metadata](http://www.github.com/xela144/CANaconda/tree/master/metadata) directory for specifiying these filters.


Choose a USB port by clicking action -> Choose Port (On Debian systems this will be /dev/ttyUSB0).

Messages which match a filter will appear in the table on the right hand pane, along with the latest value. Some units can be changed by selecting from the drop-down menu. An additional filter by value (such as a status code) can be added by entering that value in the 'ByValue' cell.

To stream messages in the Message Stream window, find the desired message in the 'Messages Seen' and click on the associated checkbox.

Note that the current version only allows one serial connection per run. If you want to open a different port, close the program and restart.

From the terminal, a command-line version can be run by giving argument '--nogui', along with the serial port.

Use the '--csv' argument to make the program output comma-separated-values. In addition to redirecting this to a .csv file, one can pipe to the 'pipePlotter.py' script for graphically viewing data in real-time. However, this script will take some configuration for specific sensors.


*An example commandline launch:*
```
    ./canpython.py --nogui /dev/ttyUSB0 -m xmltest.xml --filter='WSO100{airspeed},WSO200{wind_dir=2,velocity}' --csv --time --zero
```

This launches the CAN message viewer in command-line mode, with '/dev/ttyUSB0' as the serial port. The messages to be decoded are specified in the 'xmltest.xml' file. The user has chosen to filter the output of the WSO100 device so that only airspeed data is shown. Likewise, for the WSO200 device, output is generated only for 'wind\_dir' and 'velocity'. Finally, the user has asked that the data be shown in 'csv' format with a time stamp, in 'zero-hold' mode.

##Plotting Data
This is still in an experimental stage. Future work includes embedding this plot into a Qt widget to display to the user. Should a user wish to view data in real time, then the CANaconda application should be launched with the command line interface, with the --csv flag. The output at the terminal must be piped to the 'pipeplotter.py' script in this directory. This may take some configuration with the matplotlib backend. An example CLI launch of this script is shown here, with water speed data from the DST200 device.

> python3 CANaconda.py --nogui /dev/ttyUSB0 --messages metadata/Nmea2000.xml --filter='Speed{Speed Water Referenced}' --csv --time | python3 pipePlotter.py 

##Specifying Messages to be Parsed with the Metadata File
In addition to standard and extended CAN (2.0A and 2.0B), CANaconda is being developed to view messages on the NMEA2000 standard. Future plans will include the CANopen standard. 

See README found in [metadata](http://www.github.com/xela144/CANaconda/tree/master/metadata) directory for specifiying these filters.

#Installation for Linux

_Note that these instructions are for Debian-based distributions. Some packages may be different if you are using another distribution._

To install the pyserial package:
 * download from pypi.python.org/pypi/pyserial and follow instructions there or:
 * if pip is installed on your system, use command

> sudo pip3 install pyserial
     

Serial data will be available at /dev/ttyUSB0. However, access to /dev/ttyUSB0 is by default limited to root. In order to give access to canpython.py, add user (self) to dialout group:

> sudo adduser \<user name\> dialout

To make changes active, log out, closing session completely, and log back in.

To install Qt:
Although we can't use apt-get to install Qt5, there are good instructions found at https://qt-project.org/wiki/Install_Qt_5_on_Ubuntu. To do an online install of Qt5.3.1, follow these steps.

Download the latest version of Qt at http://qt-project.org/downloads

Make the file executable and then run it:

>chmod +x qt-opensource-linux-x64-1.6.0-4-online.run 
>./qt-opensource-linux-x64-1.6.0-4-online.run 

This is for installing g++:

>sudo apt-get install build-essential

Install the OpenGL libraries:

>sudo apt-get install mesa-common-dev libglu1-mesa-dev

The latter package is for more recent Ubuntu versions. See link above for details.

PyQt depends on Sip, which is found at www.riverbankcomputing.com. Download and unzip, then run

>python3 configure.py
>make
>make install

If you get an error that "python.h" is not found, it's because python3-dev is not installed.

To install PyQt5, run the configure.py script:

>python3 configure.py 

If the program can't find the right version of qmake, use option -q along with the path.

>python3 configure.py -q  ~/path/to/qmake
 
Then build and install. (Bro tip: use the -j option for multicore processors)

>make
>sudo make install

Export the PyQt directory to the PYTHONPATH variable
>export PYTHONPATH=$PYTHONPATH:/usr/lib/python3.4/site-packages/

Make sure this is the correct path.

Finally, open up a python3 interactive session, and run
>import PyQt5

to make sure that installation was successful.

# Installation for Mac

Using brew, the installation for PyQt5 is done in a single command:

>brew install pyqt5

To get Pyserial, use pip3:

>pip3 install pyserial

These instructions assume that brew was used to install Python 3.

```


#Contributors

* [@bapsmith](http://github.com/bapsmith)
* [@xela144](http://github.com/xela144)
* [@susurrus](http://github.com/Susurrus)


#License
All the files in this repository are released under the GPL V3 or greater.
