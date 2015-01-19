##Specifying Messages to be Parsed with the Metadata File
Currently CANaconda is being developed to view messages on the NMEA2000 standard. To view these messages, the user will create an XML style 'metadata' file. 

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
 * **type** - The data type of the field. Allowable data types are as follows:
  * *int*
  * *bitfield*
  * *boolean*
  * *enum*
 * **offset** - The number of *bits* that precede the field within the body of the CAN message.
 * **signed** - Allowable arguments here are either "*yes*" or "*no*"
 * **scaling** - The scaling used for the data. Analogous to precision.
 * **units** - Some data will have units associated. Any units can be specified, and mostly these are decorative. However, if the data is in the form of one of the following, it is advisable to use the given format, since units conversion will be available:
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

```xml
<metaData>
	<messageInfo name = "message_name" pgn = "xxx" size = "8"> 
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
