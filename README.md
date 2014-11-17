#**CANaconda**
==========
CANaconda is a flexible, open source CAN network monitoring tool under development by the UCSC Autonomous System Lab.

![demo](http://i39.tinypic.com/2gxebg4.jpg)


##System Requirements
PC capable of running Python 3

Lawicel CAN-USB bridge s/n P023

Lawicel CAN-USB drivers available from http://www.can232.com/?page\_id=75

Installation of the pySerial package from http://pyserial.sourceforge.net/pyserial.html

Installation of the matplotlib package from matplotlib.org (optional)

Installation of Qt framework, version 5, available from qt-project.org (optional - for GUI only)

Installation of PyQt5 package from riverbankcomputing.com (optional - for GUI only)


##Running CAN-aconda
Connect USB and CAN cables. The CAN network must have its own power supply. Launch the program from the command line or by double clicking the canpython.py file.

Load filters from an XML file by clicking action-> Load filters

Choose a USB port by clicking action -> Choose Port (On Debian systems this will be /dev/ttyUSB0).

Messages which match a filter will appear in the table on the right hand pane, along with the latest value. Some units can be changed by selecting from the drop-down menu. An additional filter by value (such as a status code) can be added by entering that value in the 'ByValue' cell.

To stream messages in the Message Stream window, find the desired message in the 'Messages Seen' and click on the associated checkbox.

Note that the current version only allows one serial connection per run. If you want to open a different port, close the program and restart.

From the terminal, a command-line version can be run by giving argument '--nogui'

Use the '--csv' argument to make the program output comma-separated-values. In addition to redirecting this to a .csv file, one can pipe to the 'pipePlotter.py' script for graphically viewing data in real-time. However, this script will take some configuration for specific sensors.


*An example commandline launch:*
```
    ./canpython.py --nogui /dev/ttyUSB0 -m xmltest.xml --filter='WSO100{airspeed},WSO200{wind_dir=2,velocity}' --csv --time --zero
```

  This launches the CAN message viewer in command-line mode, with '/dev/ttyUSB0' as the serial port. The messages to be decoded are specified in the 'xmltest.xml' file. The user has chosen to filter the output of the WSO100 device so that only airspeed data is shown. Likewise, for the WSO200 device, output is generated only for 'wind\_dir' and 'velocity'. Finally, the user has asked that the data be shown in 'csv' format with a time stamp, in 'zero-hold' mode.


##Specifying Messages to be Parsed with the Metadata File
Currently CANaconda is being developed to view messages on the NMEA2000 standard. To view these messages, the user will create an XML style 'messages' file. The current format for specifying these messages are similar to that found at keversoft.com. An example:

```xml
<metaData>
	<messageInfo name = "System Time" pgn = "126992" size = "8"> 
		<desc></desc>
		<field 
		name = "SID"
        type = "int"
		offset = "0" 
		length = "8" 
		signed = "no" 
		endian = "little"
		/>
		<field 
		name = "Source" 
        type = "bitfield"
		offset = "8" 
		length = "4" 
		signed = "no" 
		endian = "little"
		/>
		<field 
		name = "Days since epoch" 
        type = "int"
		offset = "16" 
		length = "16" 
		signed = "no" 
		units = "days" 
		endian = "little"
		/>
		<field 
		name = "Seconds since midnight" 
        type = "int"
		offset = "32" 
		length = "32" 
		signed = "no" 
		units = "s" 
        scaling = "0.0001"
		endian = "little"
		/>
	</messageInfo>
</metadata>
```

Alternatively, a 'pgn' can be specified in lieu of the 'id'. Note that specifying both 'id' and 'pgn' for a given filter will result in an error. This is because there is no one-to-one relation between id's and pgn's.

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


```


#Contributors

* [@bapsmith](http://github.com/bapsmith)
* [@xela144](http://github.com/xela144)
* [@susurrus](http://github.com/Susurrus)


#License
All the files in this repository are released under the GPL V3 or greater.
