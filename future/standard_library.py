"""
Python 3 reorganized the standard library (PEP 3108). This module exposes
several standard library modules to Python 2 under their new Python 3
names.

It is designed to be used as follows::

    from future import standard_library

And then these imports work::

    import builtins
    import configparser
    import copyreg
    import _markupbase
    import queue
    import reprlib
    import socketserver
    import winreg    # on Windows only
    import _thread
    import _dummythread
    import _markupbase
    import test.support

The modules are still available under their old names on Python 2.

This is a cleaner alternative to this idiom (see
http://docs.pythonsprints.com/python3_porting/py-porting.html)::

    try:
        import queue
    except ImportError:
        import Queue as queue


We don't currently support these, but would like to::

    import pickle     # should (optionally) bring in cPickle on Python 2
    import dbm
    import dbm.dumb
    import dbm.gnu
    import xmlrpc.client
    import collections.abc  # on Py33
    import http.cookies
    import http.cookiejar
    import http.server
    import http.client
    import urllib.request
    import urllib.parse
    import urllib.error
    import urllib.robotparser
    import tkinter

These renames are already supported on Python 2.7 without any additional work
from us:
    reload() -> imp.reload()
    reduce() -> functools.reduce()
    StringIO.StringIO -> io.StringIO
    Bytes.BytesIO -> io.BytesIO

This module only supports Python 2.7 and Python 3.1+.

Old things that can perhaps be fixed for people:
  string.uppercase -> string.ascii_uppercase   # works on either Py2.7 or Py3+

Others we should handle:
  itertools.ifilterfalse -> itertools.filterfalse
  intern(s) -> sys.intern(s)
  buffer -> memoryview?
  sys.maxint was renamed to sys.maxsize in Python3
  unittest2 -> unittest
"""

from __future__ import absolute_import, print_function

import sys
import logging
import imp

from . import six

# The modules that are defined under the same names on Py3 but with
# different contents in a significant way (e.g. submodules) are:
#   pickle (fast one)
#   dbm
#   urllib

# These ones are new (i.e. no problem)
#   http
#   html
#   tkinter
#   xmlrpc

# These modules need names from elsewhere being added to them:
#   collections: should provide UserList and UserString
#   subprocess: should provide getoutput and other fns from commands
#               module but these fns are missing: getstatus, mk2arg,
#               mkarg

# Old to new
# etc: see lib2to3/fixes/fix_imports.py
RENAMES = {
           # 'cStringIO': 'io',  # there's a new io module in Python 2.6
                                 # that provides StringIO and BytesIO
           # 'StringIO': 'io',   # ditto
           # 'cPickle': 'pickle',
           '__builtin__': 'builtins',
           'copy_reg': 'copyreg',
           'Queue': 'queue',
           'SocketServer': 'socketserver',
           'ConfigParser': 'configparser',
           'repr': 'reprlib',
           # 'FileDialog': 'tkinter.filedialog',
           # 'tkFileDialog': 'tkinter.filedialog',
           # 'SimpleDialog': 'tkinter.simpledialog',
           # 'tkSimpleDialog': 'tkinter.simpledialog',
           # 'tkColorChooser': 'tkinter.colorchooser',
           # 'tkCommonDialog': 'tkinter.commondialog',
           # 'Dialog': 'tkinter.dialog',
           # 'Tkdnd': 'tkinter.dnd',
           # 'tkFont': 'tkinter.font',
           # 'tkMessageBox': 'tkinter.messagebox',
           # 'ScrolledText': 'tkinter.scrolledtext',
           # 'Tkconstants': 'tkinter.constants',
           # 'Tix': 'tkinter.tix',
           # 'ttk': 'tkinter.ttk',
           # 'Tkinter': 'tkinter',
           'markupbase': '_markupbase',
           '_winreg': 'winreg',
           'thread': '_thread',
           'dummy_thread': '_dummy_thread',
           # 'anydbm': 'dbm',   # causes infinite import loop 
           # 'whichdb': 'dbm',  # causes infinite import loop 
           # anydbm and whichdb are handled by fix_imports2
           # 'dbhash': 'dbm.bsd',
           # 'dumbdbm': 'dbm.dumb',
           # 'dbm': 'dbm.ndbm',
           # 'gdbm': 'dbm.gnu',
           # 'xmlrpclib': 'xmlrpc.client',
           # 'DocXMLRPCServer': 'xmlrpc.server',
           # 'SimpleXMLRPCServer': 'xmlrpc.server',
           # 'httplib': 'http.client',
           # 'htmlentitydefs' : 'html.entities',
           # 'HTMLParser' : 'html.parser',
           # 'Cookie': 'http.cookies',
           # 'cookielib': 'http.cookiejar',
           # 'BaseHTTPServer': 'http.server',
           # 'SimpleHTTPServer': 'http.server',
           # 'CGIHTTPServer': 'http.server',
           'future.backports.test': 'test',  # primarily for renaming test_support to support
           # 'commands': 'subprocess',
           # 'UserString' : 'collections',
           # 'UserList' : 'collections',
           # 'urlparse' : 'urllib.parse',
           # 'robotparser' : 'urllib.robotparser',
           # 'future.backports_31.http': 'http',
           # 'future.backports_33.urllib': 'urllib',
           # 'future.backports_33.html': 'html',
           # 'future.backports_33.xmlrpc': 'xmlrpc',
           # 'future.backports_33.test': 'test',
           # 'abc': 'collections.abc',   # for Py33
           'future.backports.html': 'html',
           'future.backports.http': 'http',
           'future.backports.urllib': 'urllib',
          }


class WarnOnImport(object):
    def __init__(self, *args):
        self.module_names = args
 
    def find_module(self, fullname, path=None):
        if fullname in self.module_names:
            self.path = path
            return self
        return None
 
    def load_module(self, name):
        if name in sys.modules:
            return sys.modules[name]
        module_info = imp.find_module(name, self.path)
        module = imp.load_module(name, *module_info)
        sys.modules[name] = module
 
        logging.warning("Imported deprecated module %s", name)
        return module


class RenameImport(object):
    def __init__(self, old_to_new):
        '''
        Pass in a dictionary-like object mapping from old names to new
        names. E.g. {'ConfigParser': 'configparser', 'cPickle': 'pickle'}
        '''
        self.old_to_new = old_to_new
        both = set(old_to_new.keys()) & set(old_to_new.values())
        # print(both)
        assert len(both) == 0, \
               'Ambiguity in renaming (handler not implemented'
        self.new_to_old = {new: old for (old, new) in old_to_new.items()}
 
    def find_module(self, fullname, path=None):
        # Handles hierarchical importing: package.module.module2
        new_base_names = {s.split('.')[0] for s in self.new_to_old}
        if fullname in set(self.old_to_new) | new_base_names:
            return self
        return None
 
    def load_module(self, name):
        path = None
        if name in sys.modules:
            return sys.modules[name]
        elif name in self.new_to_old:
            # New name. Look up the corresponding old (Py2) name:
            name = self.new_to_old[name]
        module = self._find_and_load_module(name)
        sys.modules[name] = module
        return module
 
    def _find_and_load_module(self, name, path=None):
        """
        Finds and loads it. But if there's a . in the name, handles it
        properly.
        """
        bits = name.split('.')
        while len(bits) > 1:
            # Treat the first bit as a package
            packagename = bits.pop(0)
            package = self._find_and_load_module(packagename, path)
            path = package.__path__
        name = bits[0]
        module_info = imp.find_module(name, path)
        return imp.load_module(name, *module_info)


if not six.PY3:
    sys.meta_path = [RenameImport(RENAMES)]

