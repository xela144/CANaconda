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
Connect USB and CAN cables. The CAN network must have its own power supply for the CAN-USB. Launch the program from the command line or by double clicking the canpython.py file.

Load filters from an XML file by clicking action-> Load filters

Choose a USB port by clicking action -> Choose Port (On Debian systems this will be /dev/ttyUSB0).

Messages which match a filter will appear in the table on the right hand pane, along with the latest value. Some units can be changed by selecting from the drop-down menu. An additional filter by value (such as a status code) can be added by entering that value in the 'ByValue' cell.

To display a value in the Message Stream pane, click on the checkbox associated with it.

Only one serial connection per program launch, i.e. you only get to choose a comport once. If for whatever reason you want to open a different port, close the program and start all over.

From the terminal, a command-line version can be run by giving argument '--nogui'

If the '--csv' argument is specified, the output can be piped to the 'pipePlotter.py' script for graphically viewing data in real-time. Currently, supported for Maretron WSO100 windspeed data only. If you don't have this device and you want to view your data in a plot, it's best to save the output to a file and view in your favorite number-crunching program, such as Matlab, or the matplotlib package in Python.

Example commandline launch:
```
    ./canpython.py --nogui /dev/ttyUSB0 -m xmltest.xml --filter='WSO100{airspeed},WSO200{wind_dir=2,velocity}' --csv --time --zero
```

  This launches the CAN message viewer in command-line mode, with '/dev/ttyUSB0' as the serial port. The messages to be decoded are specified in the 'xmltest.xml' file. The user has chosen to filter the output of the WSO100 device so that only airspeed data is shown. Likewise, for the WSO200 device, output is generated only for 'wind\_dir' and 'velocity'. Finally, the user has asked that the data be shown in 'csv' format with a time stamp, in 'zero-hold' mode.


##Specifying Messages to be Parsed with the Metadata File
Currently CANaconda is being developed to view messages on the NMEA2000 standard. To view these messages, the user will create an XML style 'messages' file. The current format for specifying these messages are similar to that found at keversoft.com.

```xml
<metaData>
  <messageInfo name = "WSO100" pgn = "130306"> 
    <desc></desc>
    <field 
    name = "airspeed" 
    offset = "8" 
    length = "16" 
    signed = "no" 
    units = "m/s" 
    scaling = ".01" 
    endian = "little"
    />
    <field 
    name = "wind_dir" 
    offset = "24" 
    length = "16" 
    signed = "no" 
    units = "rad" 
    scaling = ".0001" 
    endian = "little"
    />
  </messageInfo>
  <messageInfo name = "FilterAirTemp" id = "15FD0784">
    <desc></desc>
    <field
    name = "Humidity"
    offset = "24"
    length = "16"
    signed = "yes"
    units = "%"
    scaling = ".004"
    endian = "little"
    />
  </messageInfo>
</metaData>
```

Alternatively, a 'pgn' can be specified in lieu of the 'id'. Note that specifying both 'id' and 'pgn' for a given filter will result in an error. This is because there is no one-to-one relation between id's and pgn's.


The example XML-style metadata file specifies wind speed and direction messages from one device, and ambient humidity messages from another device.

With both these devices connected to the CAN bus, and with this metadata file loaded, the message stream looks like this:

    None 09FD0284 8 EA8000EA76FAFFFFCFF6            // no longer correct:
    Header: 09FD0284, BOD: 8 WSO100 airspeed:  1.28 // needs updating

Future development of this project will focus allowing the user to specify a list of known PGNs found at keversoft.com.

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
[From http://qt-project.org/wiki/Qt5_dependencies]

To get Qt 5 working here you’ll first need build-essentials, which will give you the compilers you’ll need(g++). Following that Qt 5 will need some graphics library stuff. Type the following code in the terminal to get the required dependencies respectively:

>sudo apt-get install build-essential

By default, Qt also expects XCB and OpenGL drivers to be installed. Usually, many modern distros already do have those packages included by default. If you don’t have other OpenGL drivers (supplied by graphics vendor, for example), you can use the mesa package:

>sudo apt-get install libx11-xcb-dev libglu1-mesa-dev


From Qt downloads page, download qt-linux-opensource-5.2.0-x86-offline.run. Then type:

> chmod u+x qt-linux-opensource-5.2.0-x86-offline.run
> ./qt-linux-opensource-5.2.0-x86-offline.run 


To install PyQt5:
 * If 'qmake' is not in your python path, add it to your .bashrc (or appropriate) file:
 
```
  export PYTHONPATH=$PYTHONPATH:/usr/lib/python3.2/site-packages  // <-- change when necessary
```
 * Likewise for the gcc compiler included in the Qt download:

```
  export PATH=$PATH:/opt/Qt5.2.0/5.2.0/gcc/bin/qmake  // <-- change when necessary
```


PyQt depends on Sip, which is found at www.riverbankcomputing.com. Download and follow installation directions there.

Now in the PyQt-gpl-5.0 folder you can run the command

> python3 configure.py

If the configure script fails, rerun with the --verbose option. If an error is generated that says python.h is not found, install python3.X-dev (where 'X' is the minor version you of Python 3 which you are using). 



#Contributors

* [@bapsmith](http://github.com/bapsmith)
* [@xela144](http://github.com/xela144)
* [@susurrus](http://github.com/Susurrus)


#License
All the files in this repository are released under the GPL V3 or greater.
