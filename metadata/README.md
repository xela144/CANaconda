##Specifying Messages to be Parsed with the Metadata File
For CANaconda to understand the data within the CAN messages, a metadata file must be provided in the form of an XML file. While CANaconda is completely usable without one of these files, it will be a lot harder to use, so generating these metadata files is recommended. All messages that can be encountered should be added to the metadata file, as filtering the output to emit only certain messages is supported by both the CLI and GUI.

The root level element in the metadata XML file is the **metadata** tag itself. It has no attributes.

Each CAN message is described by the **messageInfo** tag, which has the following attributes:
 * **name** - A human-readable name of the CAN message, which will be shown to the user. 
 * **size** - The size of the message payload, in *bytes*. Valid values: [0, 8].
 * Identifier *or* parameter group number (must be one of either):
   * **id** - The identifier field of the CAN message, in hexadecimal form so should be prepended with "0x".
   * **pgn** - The parameter group number of the message as a decimal value, as set by the NMEA2000 protocol. Note that for this application, a message will have either an ID or a PGN, but not both.
 * **endian** - The endianness of the CAN data, either "*little*" or "*big*".
 * **protocol** [optional] - Here the user can specify a higher level protocol. Currently, the only valid argument is "*nmea2000*". Setting this value currently only affects the **endian** setting, so if this is set, **endian** does not need to be set as well.

Here it is instructive to see a working example for the metadata file so far:

```xml
<metadata>
    <messageInfo name = "name" id [or pgn] = "id [or pgn]" size = "size" [protocol = "protocol"]>

    </messageInfo>
</metadata>
```

Within these **messageInfo** elements is exactly 1 descrption element named **desc**. This tag should contain a description of the message, possibly describing its purpose, expected transmission rate, etc. This text is viewable as a tooltip within the GUI.

The payload of a message is described by 1 or more **field** elements that describe the individual values contained within the , we address the payload itself. A CAN message can have several pieces of information encoded within its payload. The attributes for this tag are as follows:
 * **name** - The name of the field.
 * **type** [optional] - The data type of the field. Default value is 'int'. Allowable data types are as follows:
  * *int* - A fixed-point integer value.
  * *bitfield* - A value where each bit represents a boolean value.
  * *boolean* - A single boolean value.
  * *enum* - Similar to an int, but values signify modes or states versus a numerical value.
 * **offset** - The number of *bits* that precede the field within the body of the CAN message. Valid values: [0, 63]
 * **length** - The number of *bits* used for the data of the current field. Valid values: [1, 64]
 * **signed** [optional] - Allowable arguments here are either "*yes*" or "*no*". Defaults to "*no*".
 * **scaling** [optional] - The fixed-point scaling for the data, analogous to precision. Defaults to 1. Format should be in standard decimal format (0.0001), not exponential format. Only applicable to the *int* type.
 * **units** [optional] - The units this field is in. Any string can be specified, but there is application support for certain units. If those units are specified, the user can easily convert between units in the GUI:
  * Speed: *MPS* or *m/s* for meters per second, *MPH* for miles per hour, and *KNOT* for knots
  * Angle: *RAD* for radians, *DEG* for degrees
  * Temperature: *K* for Kelvin, *CEL* for Celsius, *FAR* for Fahrenheit

Now our working example of the metadata file is:

```xml
<metadata>
    <messageInfo name = "name" id [or pgn] = "id [or pgn]" size = "size" [protocol = "protocol"]>
        <desc>description goes here</desc>
        <field
        name = "name"
        type = "type"
        offset = "offset"
        length = "length"
        [signed = "signed"]
        [scaling = "scaling"]
        [units = "units"]
        />
        <field 
        ...
        />
    </messageInfo>
    ...
</metadata>
```

Additionally, a user can specify other metadata files from within any metadata file. This allows collections of messages to be partitioned by application or CAN bus. For example, this repository already contains the following metadata file "AllMessages.xml", which when loaded actually just loads the other files found within the **include** tag recursively . Circular dependencies between metadata files are not supported at this time.


```xml
<metadata>
    <include file="application_one.xml" />
    <include file="application_two.xml" />
    <include file="protocol_x.xml" />
</metadata>
```


If syntactical errors were encountered when parsing a metadata file, the user will receive notification when the file is loaded at run-time.
