#### PATTERN | DB ##################################################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################

import os
import sys
import inspect
import re
import base64
import json

import csv as csvlib

from codecs import BOM_UTF8
from itertools import islice
from datetime import datetime, timedelta
from calendar import monthrange
from time import mktime, strftime
from math import sqrt

from functools import cmp_to_key

from io import open, StringIO, BytesIO

BOM_UTF8 = BOM_UTF8.decode("utf-8")

from html.entities import name2codepoint

from email.utils import parsedate_tz, mktime_tz

try:
    MODULE = os.path.dirname(os.path.realpath(__file__))
except:
    MODULE = ""

from pattern.helpers import encode_string, decode_string

decode_utf8 = decode_string
encode_utf8 = encode_string

ALL = "*"

_sum = sum # pattern.db.sum() is also a column aggregate function.

#### DATE FUNCTIONS ################################################################################

NOW, YEAR = "now", datetime.now().year

# Date formats can be found in the Python documentation:
# http://docs.python.org/library/time.html#time.strftime
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
date_formats = [
    DEFAULT_DATE_FORMAT,           # 2010-09-21 09:27:01  => SQLite + MySQL
    "%Y-%m-%dT%H:%M:%SZ",          # 2010-09-20T09:27:01Z => Bing
    "%a, %d %b %Y %H:%M:%S +0000", # Fri, 21 Sep 2010 09:27:01 +000 => Twitter
    "%a %b %d %H:%M:%S +0000 %Y",  # Fri Sep 21 09:21:01 +0000 2010 => Twitter
    "%Y-%m-%dT%H:%M:%S+0000",      # 2010-09-20T09:27:01+0000 => Facebook
    "%Y-%m-%d %H:%M",              # 2010-09-21 09:27
    "%Y-%m-%d",                    # 2010-09-21
    "%d/%m/%Y",                    # 21/09/2010
    "%d %B %Y",                    # 21 September 2010
    "%d %b %Y",                    # 21 Sep 2010
    "%B %d %Y",                    # September 21 2010
    "%B %d, %Y",                   # September 21, 2010
]


def _yyyywwd2yyyymmdd(year, week, weekday):
    """ Returns (year, month, day) for given (year, week, weekday).
    """
    d = datetime(year, month=1, day=4) # 1st week contains January 4th.
    d = d - timedelta(d.isoweekday() - 1) + timedelta(days=weekday - 1, weeks=week - 1)
    return (d.year, d.month, d.day)


def _strftime1900(d, format):
    """ Returns the given date formatted as a string.
    """
    if d.year < 1900: # Python's strftime() doesn't handle year < 1900.
        return strftime(format, (1900,) + d.timetuple()[1:]).replace("1900", str(d.year), 1)
    return datetime.strftime(d, format)


class DateError(Exception):
    pass


class Date(datetime):
    """ A convenience wrapper for datetime.datetime with a default string format.
    """
    format = DEFAULT_DATE_FORMAT
    # Date.year
    # Date.month
    # Date.day
    # Date.minute
    # Date.second

    @property
    def minutes(self):
        return self.minute

    @property
    def seconds(self):
        return self.second

    @property
    def microseconds(self):
        return self.microsecond

    @property
    def week(self):
        return self.isocalendar()[1]

    @property
    def weekday(self):
        return self.isocalendar()[2]

    @property
    def timestamp(self):

        # In Python 3, years before 1900 are accepted whilee mktime() raises ValueError in Python 2. Let's stick to this.
        if self.timetuple().tm_year < 1900:
            raise ValueError("year out of range")

        return int(mktime(self.timetuple())) # Seconds elapsed since 1/1/1970.

    def strftime(self, format):
        return _strftime1900(self, format)

    def copy(self):
        return date(self.timestamp)

    def __str__(self):
        return self.strftime(self.format)

    def __repr__(self):
        return "Date(%s)" % repr(self.__str__())

    def __iadd__(self, t):
        return self.__add__(t)

    def __isub__(self, t):
        return self.__sub__(t)

    def __add__(self, t):
        d = self
        if getattr(t, "years", 0) \
        or getattr(t, "months", 0):
            # January 31 + 1 month = February 28.
            y = (d.month + t.months - 1) // 12 + d.year + t.years
            m = (d.month + t.months + 0) % 12 or 12
            r = monthrange(y, m)
            d = date(y, m, min(d.day, r[1]), d.hour, d.minute, d.second, d.microsecond)
        d = datetime.__add__(d, t)
        return date(d.year, d.month, d.day, d.hour, d.minute, d.second, d.microsecond, self.format)

    def __sub__(self, t):
        if isinstance(t, (Date, datetime)):
            # Subtracting two dates returns a Time.
            t = datetime.__sub__(self, t)
            return Time(+t.days, +t.seconds,
                microseconds = +t.microseconds)
        if isinstance(t, (Time, timedelta)):
            return self + Time(-t.days, -t.seconds,
                microseconds = -t.microseconds,
                      months = -getattr(t, "months", 0),
                       years = -getattr(t, "years", 0))


def date(*args, **kwargs):
    """ Returns a Date from the given parameters:
        - date(format=Date.format) => now
        - date(int)
        - date(string)
        - date(string, format=Date.format)
        - date(string, inputformat, format=Date.format)
        - date(year, month, day, format=Date.format)
        - date(year, month, day, hours, minutes, seconds, format=Date.format)
        If a string is given without an explicit input format, all known formats will be tried.
    """
    d = None
    f = None
    if len(args) == 0 \
    and kwargs.get("year") is not None \
    and kwargs.get("month") \
    and kwargs.get("day"):
        # Year, month, day.
        d = Date(**kwargs)
    elif kwargs.get("week"):
        # Year, week, weekday.
        f = kwargs.pop("format", None)
        d = Date(*_yyyywwd2yyyymmdd(
            kwargs.pop("year", args and args[0] or Date.now().year),
            kwargs.pop("week"),
            kwargs.pop("weekday", kwargs.pop("day", 1))), **kwargs)
    elif len(args) == 0 or args[0] == NOW:
        # No parameters or one parameter NOW.
        d = Date.now()
    elif len(args) == 1 \
     and isinstance(args[0], (Date, datetime)):
        # One parameter, a Date or datetime object.
        d = Date.fromtimestamp(int(mktime(args[0].timetuple())))
        d += time(microseconds=args[0].microsecond)
    elif len(args) == 1 \
     and (isinstance(args[0], int) \
      or isinstance(args[0], (str, bytes)) and args[0].isdigit()):
        # One parameter, an int or string timestamp.
        if isinstance(args[0], bytes):
            args = (args[0].decode("utf-8"),)
        d = Date.fromtimestamp(int(args[0]))
    elif len(args) == 1 \
     and isinstance(args[0], (str, bytes)):
        # One parameter, a date string for which we guess the input format (RFC2822 or known formats).
        if isinstance(args[0], bytes):
            args = (args[0].decode("utf-8"),)
        try:
            d = Date.fromtimestamp(mktime_tz(parsedate_tz(args[0])))
        except:
            for format in ("format" in kwargs and [kwargs["format"]] or []) + date_formats:
                try:
                    d = Date.strptime(args[0], format)
                    break
                except:
                    pass
        if d is None:
            raise DateError("unknown date format for %s" % repr(args[0]))
    elif len(args) == 2 \
     and isinstance(args[0], (str, bytes)):
        # Two parameters, a date string and an explicit input format.
        if isinstance(args[0], bytes):
            args = (args[0].decode("utf-8"), args[1].decode("utf-8"))
        d = Date.strptime(args[0], args[1])
    elif len(args) >= 3:
        # 3-6 parameters: year, month, day, hours, minutes, seconds.
        f = kwargs.pop("format", None)
        d = Date(*args[:7], **kwargs)
    else:
        raise DateError("unknown date format")
    d.format = kwargs.get("format") or len(args) > 7 and args[7] or f or Date.format
    return d


class Time(timedelta):

    def __new__(cls, *args, **kwargs):
        """ A convenience wrapper for datetime.timedelta that handles months and years.
        """
        # Time.years
        # Time.months
        # Time.days
        # Time.seconds
        # Time.microseconds
        y = kwargs.pop("years", 0)
        m = kwargs.pop("months", 0)
        t = timedelta.__new__(cls, *args, **kwargs)
        setattr(t, "years", y)
        setattr(t, "months", m)
        return t


def time(days=0, seconds=0, minutes=0, hours=0, **kwargs):
    """ Returns a Time that can be added to a Date object.
        Other parameters: microseconds, milliseconds, weeks, months, years.
    """
    return Time(days=days, seconds=seconds, minutes=minutes, hours=hours, **kwargs)


def string(value, default=""):
    """ Returns the value cast to unicode, or default if it is None/empty.
    """
    # Useful for HTML interfaces.
    if value is None or value == "": # Don't do value != None because this includes 0.
        return default
    return decode_utf8(value)


class EncryptionError(Exception):
    pass


class DecryptionError(Exception):
    pass


def encrypt_string(s, key=""):
    """ Returns the given string as an encrypted bytestring.
    """
    key += " "
    a = []
    for i in range(len(s)):
        try:
            a.append(chr(ord(s[i]) + ord(key[i % len(key)]) % 256).encode("latin-1"))
        except:
            raise EncryptionError()
    s = b"".join(a)
    s = base64.urlsafe_b64encode(s)
    return s


def decrypt_string(s, key=""):
    """ Returns the given string as a decrypted Unicode string.
    """
    key += " "
    s = base64.urlsafe_b64decode(s)
    s = s.decode("latin-1")
    a = []
    for i in range(len(s)):
        try:
            a.append(chr(ord(s[i]) - ord(key[i % len(key)]) % 256))
        except:
            raise DecryptionError()
    s = "".join(a)
    s = decode_utf8(s)
    return s


#### LIST FUNCTIONS ################################################################################


def order(list, cmp=None, key=None, reverse=False):
    """ Returns a list of indices in the order as when the given list is sorted.
        For example: ["c","a","b"] => [1, 2, 0]
        This means that in the sorted list, "a" (index 1) comes first and "c" (index 0) last.
    """
    if cmp and key:
        f = lambda i, j: cmp(key(list[i]), key(list[j]))
    elif cmp:
        f = lambda i, j: cmp(list[i], list[j])
    elif key:
        f = lambda i, j: int(key(list[i]) >= key(list[j])) * 2 - 1
    else:
        f = lambda i, j: int(list[i] >= list[j]) * 2 - 1
    return sorted(range(len(list)), key=cmp_to_key(f), reverse=reverse)

_order = order


def avg(list):
    """ Returns the arithmetic mean of the given list of values.
        For example: mean([1,2,3,4]) = 10/4 = 2.5.
    """
    return float(_sum(list)) / (len(list) or 1)


def variance(list):
    """ Returns the variance of the given list of values.
        The variance is the average of squared deviations from the mean.
    """
    a = avg(list)
    return _sum([(x - a)**2 for x in list]) / (len(list) - 1 or 1)


def stdev(list):
    """ Returns the standard deviation of the given list of values.
        Low standard deviation => values are close to the mean.
        High standard deviation => values are spread out over a large range.
    """
    return sqrt(variance(list))

#### FIELD #########################################################################################


class _String(str):
    # The STRING constant can be called with a length when passed to field(),
    # for example field("language", type=STRING(2), default="en", index=True).
    def __new__(self):
        return str.__new__(self, "string")

    def __call__(self, length=100):
        return "varchar(%s)" % (length > 255 and 255 or (length < 1 and 1 or length))

# Field type.
# Note: SQLite string fields do not impose a string limit.
# Unicode strings have more characters than actually displayed (e.g. "&#9829;").
# Boolean fields are stored as tinyint(1), int 0 or 1.
STRING, INTEGER, FLOAT, TEXT, BLOB, BOOLEAN, DATE = \
    _String(), "integer", "float", "text", "blob", "boolean", "date"

STR, INT, BOOL = STRING, INTEGER, BOOLEAN


#--- QUERY -----------------------------------------------------------------------------------------



# Sorting:
ASCENDING = "asc"
DESCENDING = "desc"

# Grouping:
FIRST, LAST, COUNT, MAX, MIN, SUM, AVG, STDEV, CONCATENATE = \
    "first", "last", "count", "max", "min", "sum", "avg", "stdev", "group_concat"


#### DATASHEET #####################################################################################

#--- CSV -------------------------------------------------------------------------------------------

# Raise the default field size limit:
if sys.platform == 'win32':
    csvlib.field_size_limit(min(sys.maxsize, 2147483647))
else:
    csvlib.field_size_limit(sys.maxsize)


def csv_header_encode(field, type=STRING):
    # csv_header_encode("age", INTEGER) => "age (INTEGER)".
    t = re.sub(r"^varchar\(.*?\)", "string", (type or ""))
    t = t and " (%s)" % t or ""
    s = "%s%s" % (field or "", t.upper())
    return s


def csv_header_decode(s):
    # csv_header_decode("age (INTEGER)") => ("age", INTEGER).
    p = r"STRING|INTEGER|FLOAT|TEXT|BLOB|BOOLEAN|DATE|"
    p = re.match(r"(.*?) \((" + p + r")\)", s)
    s = s.endswith(" ()") and s[:-3] or s
    return p and (string(p.group(1), default=None), p.group(2).lower()) or (string(s) or None, None)


class CSV(list):

    def __new__(cls, rows=[], fields=None, **kwargs):
        """ A list of lists that can be imported and exported as a comma-separated text file (CSV).
        """
        if isinstance(rows, str) and os.path.exists(rows):
            csv = cls.load(rows, **kwargs)
        else:
            csv = list.__new__(cls)
        return csv

    def __init__(self, rows=[], fields=None, **kwargs):
        # List of (name, type)-tuples (STRING, INTEGER, FLOAT, DATE, BOOLEAN).
        fields = fields or kwargs.pop("headers", None)
        fields = fields and [tuple(f) if isinstance(f, (tuple, list)) else (f, None) for f in fields] or None
        self.__dict__["fields"] = fields
        if hasattr(rows, "__iter__"):
            self.extend(rows, **kwargs)

    def extend(self, rows, **kwargs):
        list.extend(self, rows)

    def _set_headers(self, v):
        self.__dict__["fields"] = v

    def _get_headers(self):
        return self.__dict__["fields"]

    headers = property(_get_headers, _set_headers)

    def save(self, path, separator=",", encoder=lambda v: v, headers=False, password=None, **kwargs):
        """ Exports the table to a unicode text file at the given path.
            Rows in the file are separated with a newline.
            Columns in a row are separated with the given separator (by default, comma).
            For data types other than string, int, float, bool or None, a custom string encoder can be given.
        """
        # Optional parameters include all arguments for csv.writer(), see:
        # http://docs.python.org/library/csv.html#csv.writer
        kwargs.setdefault("delimiter", separator)
        kwargs.setdefault("quoting", csvlib.QUOTE_ALL)
        # csv.writer will handle str, int, float and bool:
        s = StringIO()
        w = csvlib.writer(s, **kwargs)
        if headers and self.fields is not None:
            w.writerows([[csv_header_encode(name, type) for name, type in self.fields]])
        w.writerows([[encoder(v) for v in row] for row in self])
        s = s.getvalue()
        s = s.strip()
        s = re.sub("([^\"]|^)\"None\"", "\\1None", s)
        s = s if not password else encrypt_string(s, password)
        f = open(path, "w", encoding="utf-8")
        f.write(BOM_UTF8)
        f.write(s)
        f.close()

    @classmethod
    def load(cls, path, separator=",", decoder=lambda v: v, headers=False, preprocess=None, password=None, **kwargs):
        """ Returns a table from the data in the given text file.
            Rows are expected to be separated by a newline.
            Columns are expected to be separated by the given separator (by default, comma).
            Strings will be converted to int, float, bool, date or None if headers are parsed.
            For other data types, a custom string decoder can be given.
            A preprocess(str) function can be given to change the file content before parsing.
        """
        # Date objects are saved and loaded as strings, but it is easy to convert these back to dates:
        # - set a DATE field type for the column,
        # - or do Table.columns[x].map(lambda s: date(s))
        f = open(path, "r", encoding="utf-8")

        data = f if not password else decrypt_string(f.read(), password)
        data.seek(data.readline().startswith(BOM_UTF8) and 3 or 0)
        data = data if not password else BytesIO(data.replace("\r\n", "\n").replace("\r", "\n"))
        data = data if not preprocess else BytesIO(preprocess(data.read()))
        data = csvlib.reader(data, delimiter=separator)

        i, n = kwargs.get("start"), kwargs.get("count")
        if i is not None and n is not None:
            data = list(islice(data, i, i + n))
        elif i is not None:
            data = list(islice(data, i, None))
        elif n is not None:
            data = list(islice(data, n))
        else:
            data = list(data)

        f.close()
        del f

        if headers:
            fields = [csv_header_decode(field) for field in data.pop(0)]
            fields += [(None, None)] * (max([0] + [len(row) for row in data]) - len(fields))
        else:
            fields = []
        if not fields:
            # Cast fields using the given decoder (by default, all strings + None).
            data = [[decoder(decode_utf8(v) if v != "None" else None) for v in row] for row in data]
        else:
            # Cast fields to their defined field type (STRING, INTEGER, ...)
            for i, row in enumerate(data):
                for j, v in enumerate(row):
                    type = fields[j][1]
                    if row[j] == "None":
                        row[j] = decoder(None)
                    elif type is None:
                        row[j] = decoder(decode_utf8(v))
                    elif type in (STRING, TEXT):
                        row[j] = decode_utf8(v)
                    elif type == INTEGER:
                        row[j] = int(row[j])
                    elif type == FLOAT:
                        row[j] = float(row[j])
                    elif type == BOOLEAN:
                        row[j] = bool(row[j])
                    elif type == DATE:
                        row[j] = date(row[j])
                    elif type == BLOB:
                        row[j] = v
                    else:
                        row[j] = decoder(decode_utf8(v))
        return cls(rows=data, fields=fields, **kwargs)

#--- DATASHEET -------------------------------------------------------------------------------------


class Datasheet(CSV):

    def __init__(self, rows=[], fields=None, **kwargs):
        """ A matrix of rows and columns, where each row and column can be retrieved as a list.
            Values can be any kind of Python object.
        """
        # NumPy array, convert to list of int/float/str/bool.
        if rows.__class__.__name__ == "ndarray":
            rows = rows.tolist()
        self.__dict__["_rows"] = DatasheetRows(self)
        self.__dict__["_columns"] = DatasheetColumns(self)
        self.__dict__["_m"] = 0 # Number of columns per row, see Datasheet.insert().
        list.__init__(self)
        CSV.__init__(self, rows, fields, **kwargs)

    def _get_rows(self):
        return self._rows

    def _set_rows(self, rows):
        # Datasheet.rows property can't be set, except in special case Datasheet.rows += row.
        if isinstance(rows, DatasheetRows) and rows._datasheet == self:
            self._rows = rows
            return
        raise AttributeError("can't set attribute")
    rows = property(_get_rows, _set_rows)

    def _get_columns(self):
        return self._columns

    def _set_columns(self, columns):
        # Datasheet.columns property can't be set, except in special case Datasheet.columns += column.
        if isinstance(columns, DatasheetColumns) and columns._datasheet == self:
            self._columns = columns
            return
        raise AttributeError("can't set attribute")
    columns = cols = property(_get_columns, _set_columns)

    def __getattr__(self, k):
        """ Columns can be retrieved by field name, e.g., Datasheet.date.
        """
        #print("Datasheet.__getattr__", k)
        if k in self.__dict__:
            return self.__dict__[k]
        for i, f in enumerate(f[0] for f in self.__dict__["fields"] or []):
            if f == k:
                return self.__dict__["_columns"][i]
        raise AttributeError("'Datasheet' object has no attribute '%s'" % k)

    def __setattr__(self, k, v):
        """ Columns can be set by field name, e.g., Datasheet.date = [...].
        """
        #print("Datasheet.__setattr__", k)
        if k in self.__dict__:
            self.__dict__[k] = v
            return
        if k == "rows":
            self._set_rows(v)
            return
        if k == "columns":
            self._set_columns(v)
            return
        if k == "headers":
            self._set_headers(v)
            return
        for i, f in enumerate(f[0] for f in self.__dict__["fields"] or []):
            if f == k:
                self.__dict__["_columns"].__setitem__(i, v)
                return
        raise AttributeError("'Datasheet' object has no attribute '%s'" % k)

    def __setitem__(self, index, value):
        """ Sets an item or row in the matrix.
            For Datasheet[i] = v, sets the row at index i to v.
            For Datasheet[i,j] = v, sets the value in row i and column j to v.
        """
        if isinstance(index, tuple):
            list.__getitem__(self, index[0])[index[1]] = value
        elif isinstance(index, int):
            self.pop(index)
            self.insert(index, value)
        else:
            raise TypeError("Datasheet indices must be int or tuple")

    def __getitem__(self, index):
        """ Returns an item, row or slice from the matrix.
            For Datasheet[i], returns the row at the given index.
            For Datasheet[i,j], returns the value in row i and column j.
        """
        if isinstance(index, int):
            # Datasheet[i] => row i.
            return list.__getitem__(self, index)
        elif isinstance(index, slice):
            return Datasheet(rows = list.__getitem__(self, index), fields = self.fields)
        elif isinstance(index, tuple):
            i, j = index
            # Datasheet[i,j] => item from column j in row i.
            # Datasheet[i,j1:j2] => columns j1-j2 from row i.
            if not isinstance(i, slice):
                return list.__getitem__(self, i)[j]
            # Datasheet[i1:i2,j] => column j from rows i1-i2.
            if not isinstance(j, slice):
                return [row[j] for row in list.__getitem__(self, i)]
            # Datasheet[i1:i2,j1:j2] => Datasheet with columns j1-j2 from rows i1-i2.
            return Datasheet(
                  rows = (row[j] for row in list.__getitem__(self, i)),
                fields = self.fields and self.fields[j] or self.fields)
        raise TypeError("Datasheet indices must be int, tuple or slice")

    # Python 2 (backward compatibility)
    __getslice__ = lambda self, i, j: self.__getitem__(slice(i, j))

    def __delitem__(self, index):
        self.pop(index)

    # datasheet1 = datasheet2 + datasheet3
    # datasheet1 = [[...],[...]] + datasheet2
    # datasheet1 += datasheet2
    def __add__(self, datasheet):
        m = self.copy()
        m.extend(datasheet)
        return m

    def __radd__(self, datasheet):
        m = Datasheet(datasheet)
        m.extend(self)
        return m

    def __iadd__(self, datasheet):
        self.extend(datasheet)
        return self

    def insert(self, i, row, default=None, **kwargs):
        """ Inserts the given row into the matrix.
            Missing columns at the end (right) will be filled with the default value.
        """
        try:
            # Copy the row (fast + safe for generators and DatasheetColumns).
            row = [v for v in row]
        except:
            raise TypeError("Datasheet.insert(x): x must be list")
        list.insert(self, i, row)
        m = max((len(self) > 1 and self._m or 0, len(row)))
        if len(row) < m:
            row.extend([default] * (m - len(row)))
        if self._m < m:
            # The given row might have more columns than the rows in the matrix.
            # Performance takes a hit when these rows have to be expanded:
            for row in self:
                if len(row) < m:
                    row.extend([default] * (m - len(row)))
        self.__dict__["_m"] = m

    def append(self, row, default=None, _m=None, **kwargs):
        self.insert(len(self), row, default)

    def extend(self, rows, default=None, **kwargs):
        for row in rows:
            self.insert(len(self), row, default)

    def group(self, j, function=FIRST, key=lambda v: v):
        """ Returns a datasheet with unique values in column j by grouping rows with the given function.
            The function takes a list of column values as input and returns a single value,
            e.g. FIRST, LAST, COUNT, MAX, MIN, SUM, AVG, STDEV, CONCATENATE.
            The function can also be a list of functions (one for each column).
            TypeError will be raised when the function cannot handle the data in a column.
            The key argument can be used to map the values in column j, for example:
            key=lambda date: date.year to group Date objects by year.
        """
        if isinstance(function, tuple):
            function = list(function)
        if not isinstance(function, list):
            function = [function] * self._m
        if len(function) < self._m:
            function += [FIRST] * (self._m - len(function))
        for i, f in enumerate(function):
            if i == j: # Group column j is always FIRST.
                f = FIRST
            if f == FIRST:
                function[i] = lambda a: a[+0]
            if f == LAST:
                function[i] = lambda a: a[-1]
            if f == COUNT:
                function[i] = lambda a: len(a)
            if f == MAX:
                function[i] = lambda a: max(a)
            if f == MIN:
                function[i] = lambda a: min(a)
            if f == SUM:
                function[i] = lambda a: _sum([x for x in a if x is not None])
            if f == AVG:
                function[i] = lambda a: avg([x for x in a if x is not None])
            if f == STDEV:
                function[i] = lambda a: stdev([x for x in a if x is not None])
            if f == CONCATENATE:
                function[i] = lambda a: ",".join(decode_utf8(x) for x in a if x is not None)
        J = j
        # Map unique values in column j to a list of rows that contain this value.
        g = {}
        [g.setdefault(key(v), []).append(i) for i, v in enumerate(self.columns[j])]
        # Map unique values in column j to a sort index in the new, grouped list.
        o = [(g[v][0], v) for v in g]
        o = dict([(v, i) for i, (ii, v) in enumerate(sorted(o))])
        # Create a list of rows with unique values in column j,
        # applying the group function to the other columns.
        u = [None] * len(o)
        for v in g:
            # List the column values for each group row.
            u[o[v]] = [[list.__getitem__(self, i)[j] for i in g[v]] for j in range(self._m)]
            # Apply the group function to each row, except the unique value in column j.
            u[o[v]] = [function[j](column) for j, column in enumerate(u[o[v]])]
            u[o[v]][J] = v # list.__getitem__(self, i)[J]
        return Datasheet(rows=u)

    def record(self, row):
        """ Returns the given row as a dictionary of (field or alias, value)-items.
        """
        return dict(list(zip((f for f, type in self.fields), row)))

    def map(self, function=lambda item: item):
        """ Applies the given function to each item in the matrix.
        """
        for i, row in enumerate(self):
            for j, item in enumerate(row):
                row[j] = function(item)

    def slice(self, i, j, n, m):
        """ Returns a new Datasheet starting at row i and column j and spanning n rows and m columns.
        """
        return Datasheet(rows=[list.__getitem__(self, i)[j:j + m] for i in range(i, i + n)])

    def copy(self, rows=ALL, columns=ALL):
        """ Returns a new Datasheet from a selective list of row and/or column indices.
        """
        if rows == ALL and columns == ALL:
            return Datasheet(rows=self)
        if rows == ALL:
            return Datasheet(rows=list(zip(*(self.columns[j] for j in columns))))
        if columns == ALL:
            return Datasheet(rows=(self.rows[i] for i in rows))
        z = list(zip(*(self.columns[j] for j in columns)))
        return Datasheet(rows=(z[i] for i in rows))

    @property
    def array(self):
        """ Returns a NumPy array.
            Arrays must have elements of the same type, and rows of equal size.
        """
        import numpy
        return numpy.array(self)

    @property
    def json(self, **kwargs):
        """ Returns a JSON-string, as a list of dictionaries (if fields are defined) or as a list of lists.
            This is useful for sending a Datasheet to JavaScript, for example.
        """
        kwargs.setdefault("ensure_ascii", False) # Disable simplejson's Unicode encoder.
        if self.fields is not None:
            s = json.dumps([dict((f[0], row[i]) for i, f in enumerate(self.fields)) for row in self], **kwargs)
        else:
            s = json.dumps(self, **kwargs)
        return decode_utf8(s)

    @property
    def html(self):
        """ Returns a HTML-string with a <table>.
            This is useful for viewing the data, e.g., open("data.html", "wb").write(datasheet.html).
        """
        def encode(s):
            s = "%s" % s
            s = s.replace("&", "&amp;")
            s = s.replace("<", "&lt;")
            s = s.replace(">", "&gt;")
            s = s.replace("-", "&#8209;")
            s = s.replace("\n", "<br>\n")
            return s
        a = []
        a.append("<meta charset=\"utf8\">\n")
        a.append("<style>")
        a.append("table.datasheet { border-collapse: collapse; font: 11px sans-serif; } ")
        a.append("table.datasheet * { border: 1px solid #ddd; padding: 4px; } ")
        a.append("</style>\n")
        a.append("<table class=\"datasheet\">\n")
        if self.fields is not None:
            a.append("<tr>\n")
            a.append("\t<th>%s</th>\n" % "#")
            a.extend("\t<th>%s</th>\n" % encode(f[0]) for f in self.fields)
            a.append("</tr>\n")
        for i, row in enumerate(self):
            a.append("<tr>\n")
            a.append("\t<td>%s</td>\n" % (i + 1))
            a.extend("\t<td>%s</td>\n" % encode(v) for v in row)
            a.append("</tr>\n")
        a.append("</table>")
        return encode_utf8("".join(a))


def flip(datasheet):
    """ Returns a new datasheet with rows for columns and columns for rows.
    """
    return Datasheet(rows=datasheet.columns)


def csv(*args, **kwargs):
    """ Returns a Datasheet from the given CSV file path.
    """
    if len(args) == 0:
        return Datasheet(**kwargs)
    return Datasheet.load(*args, **kwargs)

#--- DATASHEET ROWS --------------------------------------------------------------------------------
# Datasheet.rows mimics the operations on Datasheet:


class DatasheetRows(list):

    def __init__(self, datasheet):
        self._datasheet = datasheet

    def __setitem__(self, i, row):
        self._datasheet.pop(i)
        self._datasheet.insert(i, row)

    def __getitem__(self, i):
        return list.__getitem__(self._datasheet, i)

    def __getslice__(self, i, j):
        return self._datasheet[i:j]

    def __delitem__(self, i):
        self.pop(i)

    def __len__(self):
        return len(self._datasheet)

    def __iter__(self):
        for i in range(len(self)):
            yield list.__getitem__(self._datasheet, i)

    def __repr__(self):
        return repr(self._datasheet)

    def __add__(self, row):
        raise TypeError("unsupported operand type(s) for +: 'Datasheet.rows' and '%s'" % row.__class__.__name__)

    def __iadd__(self, row):
        self.append(row)
        return self

    def __eq__(self, rows):
        return self._datasheet.__eq__(rows)

    def __ne__(self, rows):
        return self._datasheet.__ne__(rows)

    def insert(self, i, row, default=None):
        self._datasheet.insert(i, row, default)

    def append(self, row, default=None):
        self._datasheet.append(row, default)

    def extend(self, rows, default=None):
        self._datasheet.extend(rows, default)

    def remove(self, row):
        self._datasheet.remove(row)

    def pop(self, i):
        return self._datasheet.pop(i)

    def count(self, row):
        return self._datasheet.count(row)

    def index(self, row):
        return self._datasheet.index(row)

    def sort(self, cmp=None, key=None, reverse=False):
        self._datasheet.sort(cmp, key, reverse)

    def reverse(self):
        self._datasheet.reverse()

    def swap(self, i1, i2):
        self[i1], self[i2] = self[i2], self[i1]

#--- DATASHEET COLUMNS -----------------------------------------------------------------------------


class DatasheetColumns(list):

    def __init__(self, datasheet):
        self._datasheet = datasheet
        self._cache = {} # Keep a reference to DatasheetColumn objects generated with Datasheet.columns[j].
                          # This way we can unlink them when they are deleted.

    def __setitem__(self, j, column):
        if self._datasheet.fields is not None and j < len(self._datasheet.fields):
            # Preserve the column header if it exists.
            f = self._datasheet.fields[j]
        else:
            f = None
        self.pop(j)
        self.insert(j, column, field=f)

    def __getitem__(self, j):
        if j < 0:
            j = j % len(self) # DatasheetColumns[-1]
        if j >= len(self):
            raise IndexError("list index out of range")
        return self._cache.setdefault(j, DatasheetColumn(self._datasheet, j))

    def __getslice__(self, i, j):
        return self._datasheet[:, i:j]

    def __delitem__(self, j):
        self.pop(j)

    def __len__(self):
        return len(self._datasheet) > 0 and len(self._datasheet[0]) or 0

    def __iter__(self):
        for i in range(len(self)):
            yield self.__getitem__(i)

    def __repr__(self):
        return repr(list(iter(self)))

    def __add__(self, column):
        raise TypeError("unsupported operand type(s) for +: 'Datasheet.columns' and '%s'" % column.__class__.__name__)

    def __iadd__(self, column):
        self.append(column)
        return self

    def __eq__(self, columns):
        return list(self) == columns

    def __ne__(self, columns):
        return not self.__eq__(self, columns)

    def insert(self, j, column, default=None, field=None):
        """ Inserts the given column into the matrix.
            Missing rows at the end (bottom) will be filled with the default value.
        """
        try:
            column = [v for v in column]
        except:
            raise TypeError("Datasheet.columns.insert(x): x must be list")
        column = column + [default] * (len(self._datasheet) - len(column))
        if len(column) > len(self._datasheet):
            self._datasheet.extend([[None]] * (len(column) - len(self._datasheet)))
        for i, row in enumerate(self._datasheet):
            row.insert(j, column[i])
        self._datasheet.__dict__["_m"] += 1 # Increase column count.
        # Add a new header.
        if self._datasheet.fields is not None:
            self._datasheet.fields += [(None, None)] * (len(self) - len(self._datasheet.fields) - 1)
            self._datasheet.fields.insert(j, field or (None, None))

    def append(self, column, default=None, field=None):
        self.insert(len(self), column, default, field)

    def extend(self, columns, default=None, fields=[]):
        for j, column in enumerate(columns):
            self.insert(len(self), column, default, j < len(fields) and fields[j] or None)

    def remove(self, column):
        if isinstance(column, DatasheetColumn) and column._datasheet == self._datasheet:
            self.pop(column._j)
            return
        raise ValueError("list.remove(x): x not in list")

    def pop(self, j):
        column = list(self[j]) # Return a list copy.
        for row in self._datasheet:
            row.pop(j)
        # At one point a DatasheetColumn object was created with Datasheet.columns[j].
        # It might still be in use somewhere, so we unlink it from the datasheet:
        self._cache[j]._datasheet = Datasheet(rows=[[v] for v in column])
        self._cache[j]._j = 0
        self._cache.pop(j)
        for k in range(j + 1, len(self) + 1):
            if k in self._cache:
                # Shift the DatasheetColumn objects on the right to the left.
                self._cache[k - 1] = self._cache.pop(k)
                self._cache[k - 1]._j = k - 1
        self._datasheet.__dict__["_m"] -= 1 # Decrease column count.
        # Remove the header.
        if self._datasheet.fields is not None:
            self._datasheet.fields.pop(j)
        return column

    def count(self, column):
        return len([True for c in self if c == column])

    def index(self, column):
        if isinstance(column, DatasheetColumn) and column._datasheet == self._datasheet:
            return column._j
        return list(self).index(column)

    def sort(self, cmp=None, key=None, reverse=False, order=None):
        # This makes most sense if the order in which columns should appear is supplied.
        if order and reverse is True:
            o = list(reversed(order))
        if order and reverse is False:
            o = list(order)
        if not order:
            o = _order(self, cmp, key, reverse)
        for i, row in enumerate(self._datasheet):
            # The main difficulty is modifying each row in-place,
            # since other variables might be referring to it.
            r = list(row)
            [row.__setitem__(i2, r[i1]) for i2, i1 in enumerate(o)]
        # Reorder the datasheet headers.
        if self._datasheet.fields is not None:
            self._datasheet.fields = [self._datasheet.fields[i] for i in o]

    def swap(self, j1, j2):
        self[j1], self[j2] = self[j2], self[j1]
        # Reorder the datasheet headers.
        if self._datasheet.fields is not None:
            self._datasheet.fields[j1], self._datasheet.fields[j2] = (
                self._datasheet.fields[j2],
                self._datasheet.fields[j1])

#--- DATASHEET COLUMN ------------------------------------------------------------------------------


class DatasheetColumn(list):

    def __init__(self, datasheet, j):
        """ A dynamic column in a Datasheet.
            If the actual column is deleted with Datasheet.columns.remove() or Datasheet.columms.pop(),
            the DatasheetColumn object will be orphaned (i.e., it is no longer part of the table).
        """
        self._datasheet = datasheet
        self._j = j

    def __getslice__(self, i, j):
        return list(list.__getitem__(self._datasheet, i)[self._j] for i in range(i, min(j, len(self._datasheet))))

    def __getitem__(self, i):
        return list.__getitem__(self._datasheet, i)[self._j]

    def __setitem__(self, i, value):
        list.__getitem__(self._datasheet, i)[self._j] = value

    def __len__(self):
        return len(self._datasheet)

    def __iter__(self): # Can be put more simply but optimized for performance:
        for i in range(len(self)):
            yield list.__getitem__(self._datasheet, i)[self._j]

    def __reversed__(self):
        return reversed(list(iter(self)))

    def __repr__(self):
        return repr(list(iter(self)))

    def __gt__(self, column):
        return list(self) > list(column)

    def __lt__(self, column):
        return list(self) < list(column)

    def __ge__(self, column):
        return list(self) >= list(column)

    def __le__(self, column):
        return list(self) <= list(column)

    def __eq__(self, column):
        return list(self) == column

    def __ne__(self, column):
        return not self.__eq__(column)

    def __add__(self, column):
        return list(self) + list(column)

    def __iadd__(self, column):
        self.extend(column)

    def __contains__(self, value):
        for v in self:
            if v == value:
                return True
        return False

    def count(self, value):
        return len([True for v in self if v == value])

    def index(self, value):
        for i, v in enumerate(self):
            if v == value:
                return i
        raise ValueError("list.index(x): x not in list")

    def remove(self, value):
        """ Removes the matrix row that has the given value in this column.
        """
        for i, v in enumerate(self):
            if v == value:
                self._datasheet.pop(i)
                return
        raise ValueError("list.remove(x): x not in list")

    def pop(self, i):
        """ Removes the entire row from the matrix and returns the value at the given index.
        """
        row = self._datasheet.pop(i)
        return row[self._j]

    def sort(self, cmp=None, key=None, reverse=False):
        """ Sorts the rows in the matrix according to the values in this column,
            e.g. clicking ascending / descending on a column header in a datasheet viewer.
        """
        o = order(list(self), cmp, key, reverse)
        # Modify the table in place, more than one variable may be referencing it:
        r = list(self._datasheet)
        [self._datasheet.__setitem__(i2, r[i1]) for i2, i1 in enumerate(o)]

    def insert(self, i, value, default=None):
        """ Inserts the given value in the column.
            This will create a new row in the matrix, where other columns are set to the default.
        """
        self._datasheet.insert(i, [default] * self._j + [value] + [default] * (len(self._datasheet) - self._j - 1))

    def append(self, value, default=None):
        self.insert(len(self), value, default)

    def extend(self, values, default=None):
        for value in values:
            self.insert(len(self), value, default)

    def map(self, function=lambda value: value):
        """ Applies the given function to each value in the column.
        """
        for j, value in enumerate(self):
            self[j] = function(value)

    def filter(self, function=lambda value: True):
        """ Removes the matrix rows for which function(value) in the column is not True.
        """
        i = len(self)
        for v in reversed(self):
            i -= 1
            if not function(v):
                self._datasheet.pop(i)

    def swap(self, i1, i2):
        self._datasheet.swap(i1, i2)

#---------------------------------------------------------------------------------------------------

_UID = 0


def uid():
    global _UID
    _UID += 1
    return _UID


def truncate(string, length=100):
    """ Returns a (head, tail)-tuple, where the head string length is less than the given length.
        Preferably the string is split at a space, otherwise a hyphen ("-") is injected.
    """
    if len(string) <= length:
        return string, ""
    n, words = 0, string.split(" ")
    for i, w in enumerate(words):
        if n + len(w) > length:
            break
        n += len(w) + 1
    if i == 0 and len(w) > length:
        return (w[:length - 1] + "-",
                (w[length - 1:] + " " + " ".join(words[1:])).strip())
    return (" ".join(words[:i]),
            " ".join(words[i:]))

_truncate = truncate


def pprint(datasheet, truncate=40, padding=" ", fill="."):
    """ Prints a string where the rows in the datasheet are organized in outlined columns.
    """
    # Calculate the width of each column, based on the longest field in each column.
    # Long fields can be split across different lines, so we need to check each line.
    w = [0 for column in datasheet.columns]
    R = []
    for i, row in enumerate(datasheet.rows):
        fields = []
        for j, v in enumerate(row):
            # Cast each field in the row to a string.
            # Strings that span beyond the maximum column width are wrapped.
            # Thus, each "field" in the row is a list of lines.
            lines = []
            if not isinstance(v, str):
                v = str(v)
            for v in v.splitlines():
                v = decode_utf8(v.strip())
                while v:
                    head, v = _truncate(v, truncate)
                    lines.append(head)
                    w[j] = max(w[j], len(head))
            fields.append(lines)
        R.append(fields)
    for i, fields in enumerate(R):
        # Add empty lines to each field so they are of equal height.
        n = max([len(lines) for lines in fields])
        fields = [lines + [""] * (n - len(lines)) for lines in fields]
        # Print the row line per line, justifying the fields with spaces.
        columns = []
        for k in range(n):
            for j, lines in enumerate(fields):
                s = lines[k]
                s += ((k == 0 or len(lines[k]) > 0) and fill or " ") * (w[j] - len(lines[k]))
                s += padding
                columns.append(s)
            print(" ".join(columns))
