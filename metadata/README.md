##Specifying Messages to be Parsed with the Metadata File
Currently CANaconda is being developed to view messages on the NMEA2000 standard. To view these messages, the user will create an XML style 'metadata' file. 

The current format for specifying these messages is similar to that found at keversoft.com. 

The structure of this file is as follows. Optional tags are shown between square brackets, i.e. [attribute = "*attribute*"]. First we discuss the top-level tag, which is the metadata tag itself. All metadata xml must be embedded within this tag.

The next level is the *messageInfo* tag. Within the *messageInfo* tag are the following attributes: *name, pgn, id, size,* and *protocol*
 * *name* - The name of the CAN message, as it will appear in the program at run-time. 
 * *size* - The size of the message payload, in **bytes**
 * Identifier *or* parameter group number.
   * *id* - The identifier field of the CAN message, in hexadecimal form.
   * *pgn* - The parameter group number of the message, as specified by the NMEA 2000 protocol. Note that for this application, a message will have either an ID or a PGN, but not both.
 * *protocol* [optional] - Here the user can specify a higher level protocol. Currently, valid argument is only *nmea200*.

```xml
<metadata>
    <messageInfo name = "name" pgn = "pgn" size = "size">

    </messageInfo>
</metadata>
```

 An example:



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
