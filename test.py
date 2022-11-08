import xml.etree.ElementTree as ET
xml = """<MPD minBufferTime="PT1.500000S" type="static" mediaPresentationDuration="PT0H9M56.46S" profiles="urn:mpeg:dash:profile:isoff-live:2011">
<ProgramInformation moreInformationURL="http://gpac.sourceforge.net">
<Title>
dashed/BigBuckBunny_6s_simple_2014_05_09.mpd generated by GPAC
</Title>
</ProgramInformation>
<Period duration="PT0H9M56.46S">
<AdaptationSet segmentAlignment="true" group="1" maxWidth="480" maxHeight="360" maxFrameRate="24" par="4:3">
<SegmentTemplate timescale="96" media="bunny_$Bandwidth$bps/BigBuckBunny_6s$Number$.m4s" startNumber="1" duration="576" initialization="bunny_$Bandwidth$bps/BigBuckBunny_6s_init.mp4"/>
<Representation id="320x240 46.0kbps" mimeType="video/mp4" codecs="avc1.42c00d" width="320" height="240" frameRate="24" sar="1:1" startWithSAP="1" bandwidth="45514"/>
<Representation id="480x360 177.0kbps" mimeType="video/mp4" codecs="avc1.42c015" width="480" height="360" frameRate="24" sar="1:1" startWithSAP="1" bandwidth="176827"/>
<Representation id="854x480 506.0kbps" mimeType="video/mp4" codecs="avc1.42c01e" width="854" height="480" frameRate="24" sar="1:1" startWithSAP="1" bandwidth="506300"/>
<Representation id="1280x720 1.0Mbps" mimeType="video/mp4" codecs="avc1.42c01f" width="1280" height="720" frameRate="24" sar="1:1" startWithSAP="1" bandwidth="1006743"/>
</AdaptationSet>
</Period>
</MPD>"""

root = ET.fromstring(xml)
for representation in root.find("Period").find("AdaptationSet").findall("Representation"):
    print(representation.get("bandwidth"))