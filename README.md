
Faux Pas Diagnostics Set Converter
==================================

Converts [Faux Pas] diagnostics set JSON into other formats. This is useful if you want to feed the diagnostics emitted by Faux Pas into some external tool.

Currently supported formats:

- CheckStyle XML

[Faux Pas]: http://fauxpasapp.com


Example
-------

    fauxpas -o json check MyProject.xcodeproj \
        | ./fauxpas_convert.py checkstyle_xml

