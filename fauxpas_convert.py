#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import os
import xml.dom.minidom
from collections import defaultdict
from xml.sax.saxutils import escape as xml_escape, quoteattr
try:
    from docopt import docopt
    from xmlbuilder import XMLBuilder
except Exception, e:
    print e
    print 'Required modules: docopt, xmlbuilder'
    sys.exit(1)


class DiagnosticsSet:

    def __init__(self, input_json_file):
        import json
        import codecs
        diags_set_json = codecs.getreader('utf-8')(input_json_file).read()
        self.obj = json.loads(diags_set_json)
        self.diagnostics = [Diagnostic(x)
                            for x in self.obj.get('diagnostics', [])]

    @property
    def pbxproj_path(self):
        return os.path.join(self.obj.get('projectPath'), 'project.pbxproj')

    def grouped_diagnostics(self, by_property='file'):
        ret = defaultdict(list)
        for diag in self.diagnostics:
            value = getattr(diag, by_property)
            ret[value].append(diag)
        return ret


class Diagnostic:

    def __init__(self, dictobj):
        self.obj = dictobj
        self.html = DictWrapper(self.obj.get('html'), defaultvalue='')
        self.extent = DiagnosticExtent(self.obj.get('extent'))

    def __getattr__(self, attrname):
        default = 0 if attrname in ('severity', 'confidence') else ''
        return self.obj.get(attrname) or default


class DiagnosticExtent:

    def __init__(self, dictobj):
        self.start = DictWrapper(dictobj.get('start'), defaultvalue=0)
        self.end = DictWrapper(dictobj.get('end'), defaultvalue=0)


class DictWrapper:

    def __init__(self, dictobj, defaultvalue):
        self.obj = dictobj
        self.defaultvalue = defaultvalue

    def __getattr__(self, attrname):
        return self.obj.get(attrname, self.defaultvalue)


FORMATTER_FUNCTIONS = {}


def formatter_function(func):
    def func_wrapper(diags_set):
        return func(diags_set)
    FORMATTER_FUNCTIONS[func.__name__] = func
    return func_wrapper


@formatter_function
def checkstyle_xml(diags_set):

    def converted_severity(fauxpas_severity):
        # checkstyle severities: ignore, info, warning, error
        if (9 <= fauxpas_severity):
            return 'error'
        elif (5 <= fauxpas_severity):
            return 'warning'
        return 'info'

    x = XMLBuilder('checkstyle')
    diags_by_file = diags_set.grouped_diagnostics(by_property='file')
    for filepath, diags in diags_by_file.items():
        with x.file(name=filepath or diags_set.pbxproj_path):
            for diag in diags:
                message = diag.info
                if 0 < len(message):
                    message += ' '
                message += '(%s - %s)' % (diag.ruleName, diag.ruleDescription)
                x.error(severity=converted_severity(diag.severity),
                        source=diag.ruleShortName,
                        message=message,
                        line=str(diag.extent.start.line),
                        column=str(diag.extent.start.utf16Column)
                        )
    return str(x)


def main():
    """Usage: convert.py <format>

    Faux Pas diagnostics JSON should be provided through standard input.
    """
    args = docopt(main.__doc__)

    format_name = args.get('<format>')
    formatter_function = FORMATTER_FUNCTIONS.get(format_name)
    if formatter_function is None:
        sys.stderr.write('<format> must be one of: %s\n'
                         % ', '.join(FORMATTER_FUNCTIONS.keys()))
        sys.exit(1)

    print formatter_function(DiagnosticsSet(sys.stdin))


if __name__ == '__main__':
    main()
