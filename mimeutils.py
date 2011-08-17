"""MIME type utilities.

Per Kraulis
 2007-10-03
 2008-09-23  changes
 2008-11-19  added 'guess_type'
 2008-12-29  added .rst and text/x-rst for ReStructuredText
 2009-01-27  added .gdb and application/x-gdbm
 2009-03-26  added .db3, application/x-sqlite3, .sql, text/x-sql
 2009-04-22  added application/docbook+xml
 2010-06-14  made DEFINED_MIMETYPES into proper inverse of DEFINED_EXTENSIONS
 2010-07-02  added guess_content_type
 2010-10-14  added .atom
 2011-07-14  added .bin for application/octet-stream
 2011-08-16  added .csv for text/csv, since this is lacking for some systems?
"""

import mimetypes
import os.path
import subprocess


# Cases where the default is not useful or does not exist
DEFINED_EXTENSIONS = {'text/plain':               '.txt',  # Else '.ksh'
                      'text/csv':                 '.csv',  # Missing sometimes?
                      'application/octet-stream': '.bin',  # Else '.obj'
                      'application/xml':          '.xml',  # Else '.wsdl'
                      'application/xslt+xml':     '.xsl',
                      'application/docbook+xml':  '.xml',
                      'application/atom+xml':     '.atom',
                      'application/json':         '.json',
                      'image/vnd.microsoft.icon': '.ico',
                      'image/jpeg':               '.jpg',  # Else '.jpe'
                      'application/x-fasta':      '.fasta',
                      'text/x-rst':               '.rst',
                      'text/x-sql':               '.sql',
                      'text/x-log':               '.log',
                      'application/x-gdbm':       '.gdb',
                      'application/x-sqlite3':    '.db3',
                      'application/x-hdf5':       '.h5',
                      'text/x-templyte-html':     '.thtml'}

# The inverse of the above
DEFINED_MIMETYPES = dict([(value, key)
                          for key, value in DEFINED_EXTENSIONS.items()])

TEXT_MIMETYPES = set(['text/plain',
                      'text/html',
                      'text/xml',
                      'text/csv',
                      'text/tab-separated-values',
                      'text/css',
                      'text/x-rst',
                      'text/x-sql',
                      'text/x-log',
                      'text/x-python',
                      'text/x-templyte-html',
                      'image/svg+xml',
                      'application/xml',
                      'application/xhtml+xml',
                      'application/xslt+xml',
                      'application/docbook+xml',
                      'application/rdf+xml',
                      'application/javascript',
                      'application/x-javascript',
                      'application/x-fasta'])

HTML_MIMETYPES = set(['text/html',
                      'application/xhtml+xml'])

XML_MIMETYPES = set(['text/xml',
                     'application/xml',
                     'application/xhtml+xml',
                     'application/xslt+xml',
                     'application/docbook+xml',
                     'application/atom+xml',
                     'application/rdf+xml',
                     'image/svg+xml'])

IMAGE_MIMETYPES = set(['image/jpeg',
                       'image/gif',
                       'image/png',
                       'image/tiff',
                       'image/vnd.microsoft.icon'])

MIMETYPE_TITLES = {'text/plain': 'Text',
                   'text/csv': 'Comma-separated values',
                   'text/tab-separated-values': 'Tab-separated values',
                   'text/xml': 'XML; eXtensible Markup Language',
                   'text/css': 'CSS; Cascading Style Sheet',
                   'image/svg+xml': 'SVG; Scalable Vector Graphics',
                   'image/png': 'PNG; Portable Network Graphics',
                   'image/gif': 'GIF; Graphics Interchange Format',
                   'image/jpeg': 'JPEG',
                   'image/tiff': 'TIFF; Tagged Image File Format',
                   'image/x-portable-pixmap': 'PPM; Portable Pixmap format',
                   'image/x-targa': 'TGA; Targa graphics file format',
                   'image/x-xbitmap': 'XBM; X BitMap format',
                   'image/x-xpixmap': 'XPM; X PixMap format',
                   'image/x-ms-bmp': 'BMP; MicroSoft Bitmap format',
                   'text/html': 'HTML; HyperText Markup Language',
                   'application/xhtml+xml': 'XHTML; HTML as XML',
                   'application/xslt+xml': 'XSLT; Extensible Stylesheet Language for Transformations',
                   'application/docbook+xml': 'DocBook XML',
                   'application/atom+xml': 'Atom Syndication Format',
                   'application/rdf+xml': 'RDF; Resource Description Format',
                   'application/pdf': 'PDF; Portable Document Format',
                   'application/postscript': 'PostScript',
                   'text/x-sql': 'SQL; Structure Query Language',
                   'text/x-rst': 'ReStructuredText',
                   'application/x-gdbm': 'gdbm key-value database; GNU DBM',
                   'application/x-sqlite3': 'SQLite3 database',
                   'application/x-hdf5': 'Hierarchical Data Format 5 (HDF5)',
                   'text/x-templyte-html': 'Templyte HTML template'}

def guess_type(filename, strict=True):
    """Guess MIME type from the suffix (including dot) of the filename or URL.
    Returns a tuple (type, encoding)."""
    try:
        return (DEFINED_MIMETYPES[os.path.splitext(filename)[1]], None)
    except KeyError:
        return mimetypes.guess_type(filename, strict)

def guess_content_type(filepath):
    """Guess MIME type from the file content using the 'file' utility.
    Return None if no guess could be made, or if an error in calling 'file'.
    NOTE: Returns only the type, no encoding."""
    process = subprocess.Popen(['/usr/bin/file',
                                '-b', # Brief; do not include file name
                                '--mime-type',
                                filepath],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    output, error = process.communicate('')
    code = process.wait()
    if code != 0:
        return None
    else:
        return output.strip()

def guess_extension(mimetype, fallback='.bin'):
    """Guess file extension (including dot) for a given MIME type,
    except for a few hard-wired ones which are known.
    If nothing fits, then return the given fallback."""
    try:
        return DEFINED_EXTENSIONS[mimetype]
    except KeyError:
        return mimetypes.guess_extension(mimetype or '') or fallback


if __name__ == '__main__':
    for mt in ['application/xml',
               'text/plain',
               'text/xml',
               'text/html',
               'blah/blu',
               'image/svg+xml',
               'application/x-fasta']:
        print mt, guess_extension(mt).lstrip('.')
    print
    for filename in ['P01112.fasta',
                     'chunk.h5',
                     'image.jpg',
                     'image.jpeg',
                     'image.jpe',
                     'stuff.bin']:
        print filename, guess_type(filename)
    print
    for filepath in ['/home/pjk/ok', '/home/pjk/ok-none']:
        print filepath, guess_content_type(filepath)

