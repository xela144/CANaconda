##Specifying Messages to be Parsed with the Metadata File
Currently CANaconda is being developed to view messages on the NMEA2000 standard. To view these messages, the user will create an XML style 'messages' file. The current format for specifying these messages are similar to that found at keversoft.com. An example:

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
