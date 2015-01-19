##Specifying Messages to be Parsed with the Metadata File
Currently CANaconda is being developed to view messages on the NMEA2000 standard. Custom CAN messages that follow the CAN 2.0A or 2.0B standard are also viewable with this tool. To view these messages, the user will create an XML style 'metadata' file. 

The current format for specifying these messages is similar to that found at keversoft.com. 

The structure of this file is as follows. Optional tags are shown between square brackets, i.e. [attribute = "*attribute*"]. First we discuss the top-level tag, which is the metadata tag itself. All metadata xml must be embedded within this tag.

The next level is the **messageInfo** tag. Within the **messageInfo** tag are the following attributes: **name, pgn, id, size,** and **protocol**
 * **name** - The name of the CAN message, as it will appear in the program at run-time. 
 * **size** - The size of the message payload, in *bytes*
 * Identifier *or* parameter group number (must be one of either of the following):
   * **id** - The identifier field of the CAN message, in hexadecimal form.
   * **pgn** - The parameter group number of the message, as specified by the NMEA 2000 protocol. Note that for this application, a message will have either an ID or a PGN, but not both.
 * **endian** - The endianness of the CAN data.
 * **protocol** [optional] - Here the user can specify a higher level protocol. Currently, valid argument is only *nmea200*. This attribute will effect the way the program interprets the endianness of the CAN messages.

Here it is instructive to include a working example for the metadata file so far:

```xml
<metadata>
    <messageInfo name = "name" id [or pgn] = "id [or pgn]" size = "size" [protocol = "protocol"]>

    </messageInfo>
</metadata>
```

At the next level of the xml heirarchy, we have two tags: **desc** and **field**. The **desc** tag simply allows the user to enter a brief description the information contained with a particular CAN message. This description shows up as a tooltip within the GUI.

Next, we address the payload itself. A CAN message can have several pieces of information encoded within its payload. Therefore, we introduce a new tag called **field**. The attributes for this tag are as follows:

 * **name** - The name of the field.
 * **type** [optional] - The data type of the field. Default value is 'int' Allowable data types are as follows:
  * *int*
  * *bitfield*
  * *boolean*
  * *enum*
 * **offset** - The number of *bits* that precede the field within the body of the CAN message.
 * **length** - The number of *bits* used to express the data of the current field.
 * **signed** [optional] - Allowable arguments here are either "*yes*" or "*no*". Defaults to unsigned.
 * **scaling** [optional] - The scaling used for the data. Analogous to precision. Defaults to scale factor of 1.
 * **units** [optional] - Some data will have units associated. Any units can be specified, and mostly these are decorative. However, if the data is in the form of one of the following, it is advisable to use the given format, since units conversion will be available:
  * *MPS* or *m/s* for meters per second
  * *MPH* for miles per hour
  * *KNOT* for knots
  * *RAD* for radians
  * *DEG* for degrees
  * *K* for Kelvins
  * *CEL* for Celsius
  * *FAR* for Fahrenheit


Now our working example of the metadata file is:

```xml
<metadata>
    <messageInfo name = "name" id [or pgn] = "id [or pgn]" size = "size" [protocol = "protocol"]>
    <desc>description goes here</desc>
    <field
    name = "name"
    type = "type"
    offset = "offset"
    signed = "signed"
    scaling = "scaling"
    units = "units"
    />
    <field 
    ...
    />
    </messageInfo>
</metadata>
```

With this brief tutorial, one should be able to construct a custom metadata file. If syntactical errors were included in a metadata file, the user will receive notification when the file is loaded at run-time.
