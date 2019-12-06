# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

from builtins import str, bytes, dict, int
from builtins import map, zip, filter
from builtins import object, range, next

from io import open

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import datetime
import codecs
import random
import unittest

from pattern import db


#---------------------------------------------------------------------------------------------------


class TestUnicode(unittest.TestCase):

    def setUp(self):
        # Test data with different (or wrong) encodings.
        self.strings = (
            "ünîcøde",
            "ünîcøde".encode("utf-16"),
            "ünîcøde".encode("latin-1"),
            "ünîcøde".encode("windows-1252"),
            "ünîcøde",
            "אוניקאָד"
        )

    def test_decode_utf8(self):
        # Assert unicode.
        for s in self.strings:
            self.assertTrue(isinstance(db.decode_utf8(s), str))
        print("pattern.db.decode_utf8()")

    def test_encode_utf8(self):
        # Assert Python bytestring.
        for s in self.strings:
            self.assertTrue(isinstance(db.encode_utf8(s), bytes))
        print("pattern.db.encode_utf8()")

    def test_string(self):
        # Assert string() with default for "" and None.
        for v, s in ((True, "True"), (1, "1"), (1.0, "1.0"), ("", "????"), (None, "????")):
            self.assertEqual(db.string(v, default="????"), s)
        print("pattern.db.string()")


#---------------------------------------------------------------------------------------------------


class TestDate(unittest.TestCase):

    def setUp(self):
        pass

    def test_date(self):
        # Assert string input and default date formats.
        for s in (
          "2010-09-21 09:27:01",
          "2010-09-21T09:27:01Z",
          "2010-09-21T09:27:01+0000",
          "2010-09-21 09:27",
          "2010-09-21",
          "21/09/2010",
          "21 September 2010",
          "September 21 2010",
          "September 21, 2010",
          1285054021):
            v = db.date(s)
            self.assertEqual(v.format, "%Y-%m-%d %H:%M:%S")
            self.assertEqual(v.year, 2010)
            self.assertEqual(v.month, 9)
            self.assertEqual(v.day, 21)
        # Assert NOW.
        for v in (db.date(), db.date(db.NOW)):
            self.assertEqual(v.year, datetime.datetime.now().year)
            self.assertEqual(v.month, datetime.datetime.now().month)
            self.assertEqual(v.day, datetime.datetime.now().day)
        self.assertEqual(db.date().year, db.YEAR)
        # Assert integer input.
        v1 = db.date(2010, 9, 21, format=db.DEFAULT_DATE_FORMAT)
        v2 = db.date(2010, 9, 21, 9, 27, 1, 0, db.DEFAULT_DATE_FORMAT)
        v3 = db.date(2010, 9, 21, hour=9, minute=27, second=1, format=db.DEFAULT_DATE_FORMAT)
        self.assertEqual(str(v1), "2010-09-21 00:00:00")
        self.assertEqual(str(v2), "2010-09-21 09:27:01")
        self.assertEqual(str(v3), "2010-09-21 09:27:01")
        # Assert week and weekday input
        v4 = db.date(2014, week=1, weekday=1, hour=12, format=db.DEFAULT_DATE_FORMAT)
        self.assertEqual(str(v4), "2013-12-30 12:00:00")
        # Assert Date input.
        v5 = db.date(db.date(2014, 1, 1))
        self.assertEqual(str(v5), "2014-01-01 00:00:00")
        # Assert timestamp input.
        v6 = db.date(db.date(2014, 1, 1).timestamp)
        self.assertEqual(str(v5), "2014-01-01 00:00:00")
        # Assert DateError for other input.
        self.assertRaises(db.DateError, db.date, None)
        print("pattern.db.date()")

    def test_format(self):
        # Assert custom input formats.
        v = db.date("2010-09", "%Y-%m")
        self.assertEqual(str(v), "2010-09-01 00:00:00")
        self.assertEqual(v.year, 2010)
        # Assert custom output formats.
        v = db.date("2010-09", "%Y-%m", format="%Y-%m")
        self.assertEqual(v.format, "%Y-%m")
        self.assertEqual(str(v), "2010-09")
        self.assertEqual(v.year, 2010)
        # Assert strftime() for date < 1900.
        v = db.date(1707, 4, 15)
        self.assertEqual(str(v), "1707-04-15 00:00:00")
        self.assertRaises(ValueError, lambda: v.timestamp)
        print("pattern.db.Date.__str__()")

    def test_timestamp(self):
        # Assert Date.timestamp.
        v = db.date(2010, 9, 21, format=db.DEFAULT_DATE_FORMAT)
        self.assertEqual(v.timestamp, 1285020000)
        print("pattern.db.Date.timestamp")

    def test_time(self):
        # Assert Date + time().
        v = db.date("2010-09-21 9:27:00")
        v = v - db.time(days=1, hours=1, minutes=1, seconds=1)
        self.assertEqual(str(v), "2010-09-20 08:25:59")
        # Assert Date + time(years, months)
        v = db.date(2014, 1, 31)
        v = v + db.time(years=1, months=1)
        self.assertEqual(str(v), "2015-02-28 00:00:00")
        print("pattern.db.time()")

#---------------------------------------------------------------------------------------------------


class TestUtilityFunctions(unittest.TestCase):

    def setUp(self):
        pass

    def test_encryption(self):
        # Assert string password encryption.
        v1 = "test"
        v2 = db.encrypt_string(v1, key="1234")
        v3 = db.decrypt_string(v2, key="1234")
        self.assertTrue(v2 != "test")
        self.assertTrue(v3 == "test")
        print("pattern.db.encrypt_string()")
        print("pattern.db.decrypt_string()")

    def test_json(self):
        # Assert JSON input and output.
        v1 = ["a,b", 1, 1.0, True, False, None, [1, 2], {"a:b": 1.2, "a,b": True, "a": [1, {"2": 3}], "1": "None"}]
        v2 = db.json.dumps(v1)
        v3 = db.json.loads(v2)
        self.assertEqual(v1, v3)
        print("pattern.db.json.dumps()")
        print("pattern.db.json.loads()")

    def test_order(self):
        # Assert a list of indices in the order as when the given list is sorted.
        v = [3, 1, 2]
        self.assertEqual(db.order(v), [1, 2, 0])
        self.assertEqual(db.order(v, reverse=True), [0, 2, 1])
        self.assertEqual(db.order(v, cmp=lambda a, b: a - b), [1, 2, 0])
        self.assertEqual(db.order(v, key=lambda i: i), [1, 2, 0])
        print("pattern.db.order()")

    def test_avg(self):
        # Assert (1+2+3+4) / 4 = 2.5.
        self.assertEqual(db.avg([1, 2, 3, 4]), 2.5)
        print("pattern.db.avg()")

    def test_variance(self):
        # Assert 2.5.
        self.assertEqual(db.variance([1, 2, 3, 4, 5]), 2.5)
        print("pattern.db.variance()")

    def test_stdev(self):
        # Assert 2.429.
        self.assertAlmostEqual(db.stdev([1, 5, 6, 7, 6, 8]), 2.429, places=3)
        print("pattern.db.stdev()")



class TestCSV(unittest.TestCase):

    def setUp(self):
        # Create test table.
        self.csv = db.CSV(
            rows=[
                ["Schrödinger", "cat", True, 3, db.date(2009, 11, 3)],
                ["Hofstadter", "labrador", True, 5, db.date(2007, 8, 4)]
            ],
            fields=[
                ["name", db.STRING],
                ["type", db.STRING],
                ["tail", db.BOOLEAN],
                ["age", db.INTEGER],
                ["date", db.DATE],
            ])

    def test_csv_header(self):
        # Assert field headers parser.
        v1 = db.csv_header_encode("age", db.INTEGER)
        v2 = db.csv_header_decode("age (INTEGER)")
        self.assertEqual(v1, "age (INTEGER)")
        self.assertEqual(v2, ("age", db.INTEGER))
        print("pattern.db.csv_header_encode()")
        print("pattern.db.csv_header_decode()")

    def test_csv(self):
        # Assert saving and loading data (field types are preserved).
        v = self.csv
        v.save("test.csv", headers=True)
        v = db.CSV.load("test.csv", headers=True)
        self.assertTrue(isinstance(v, list))
        self.assertTrue(v.headers[0] == ("name", db.STRING))
        self.assertTrue(v[0] == ["Schrödinger", "cat", True, 3, db.date(2009, 11, 3)])
        os.unlink("test.csv")
        print("pattern.db.CSV")
        print("pattern.db.CSV.save()")
        print("pattern.db.CSV.load()")

    def test_file(self):
        # Assert CSV file contents.
        v = self.csv
        v.save("test.csv", headers=True)
        f = open("test.csv", "rb")
        v = f.read()
        f.close()
        v = db.decode_utf8(v.lstrip(codecs.BOM_UTF8))
        v = v.replace("\r\n", "\n")
        self.assertEqual(v,
            '"name (STRING)","type (STRING)","tail (BOOLEAN)","age (INTEGER)","date (DATE)"\n'
            '"Schrödinger","cat","True","3","2009-11-03 00:00:00"\n'
            '"Hofstadter","labrador","True","5","2007-08-04 00:00:00"'
        )
        os.unlink("test.csv")

#---------------------------------------------------------------------------------------------------


class TestDatasheet(unittest.TestCase):

    def setUp(self):
        pass

    def test_rows(self):
        # Assert Datasheet.rows DatasheetRows object.
        v = db.Datasheet(rows=[[1, 2], [3, 4]])
        v.rows += [5, 6]
        v.rows[0] = [0, 0]
        v.rows.swap(0, 1)
        v.rows.insert(1, [1, 1])
        v.rows.pop(1)
        self.assertTrue(isinstance(v.rows, db.DatasheetRows))
        self.assertEqual(v.rows, [[3, 4], [0, 0], [5, 6]])
        self.assertEqual(v.rows[0], [3, 4])
        self.assertEqual(v.rows[-1], [5, 6])
        self.assertEqual(v.rows.count([3, 4]), 1)
        self.assertEqual(v.rows.index([3, 4]), 0)
        self.assertEqual(sorted(v.rows, reverse=True), [[5, 6], [3, 4], [0, 0]])
        self.assertRaises(AttributeError, v._set_rows, [])
        # Assert default for new rows with missing columns.
        v.rows.extend([[7], [9]], default=0)
        self.assertEqual(v.rows, [[3, 4], [0, 0], [5, 6], [7, 0], [9, 0]])
        print("pattern.db.Datasheet.rows")

    def test_columns(self):
        # Assert Datasheet.columns DatasheetColumns object.
        v = db.Datasheet(rows=[[1, 3], [2, 4]])
        v.columns += [5, 6]
        v.columns[0] = [0, 0]
        v.columns.swap(0, 1)
        v.columns.insert(1, [1, 1])
        v.columns.pop(1)
        self.assertTrue(isinstance(v.columns, db.DatasheetColumns))
        self.assertEqual(v.columns, [[3, 4], [0, 0], [5, 6]])
        self.assertEqual(v.columns[0], [3, 4])
        self.assertEqual(v.columns[-1], [5, 6])
        self.assertEqual(v.columns.count([3, 4]), 1)
        self.assertEqual(v.columns.index([3, 4]), 0)
        self.assertEqual(sorted(v.columns, reverse=True), [[5, 6], [3, 4], [0, 0]])
        self.assertRaises(AttributeError, v._set_columns, [])
        # Assert default for new columns with missing rows.
        v.columns.extend([[7], [9]], default=0)
        self.assertEqual(v.columns, [[3, 4], [0, 0], [5, 6], [7, 0], [9, 0]])
        print("pattern.db.Datasheet.columns")

    def test_column(self):
        # Assert DatasheetColumn object.
        # It has a reference to the parent Datasheet, as long as it is not deleted from the datasheet.
        v = db.Datasheet(rows=[[1, 3], [2, 4]])
        column = v.columns[0]
        column.insert(1, 0, default=None)
        self.assertEqual(v, [[1, 3], [0, None], [2, 4]])
        del v.columns[0]
        self.assertTrue(column._datasheet, None)
        print("pattern.db.DatasheetColumn")

    def test_fields(self):
        # Assert Datasheet with incomplete headers.
        v = db.Datasheet(rows=[["Schrödinger", "cat"]], fields=[("name", db.STRING)])
        self.assertEqual(v.fields, [("name", db.STRING)])
        # Assert (None, None) for missing headers.
        v.columns.swap(0, 1)
        self.assertEqual(v.fields, [(None, None), ("name", db.STRING)])
        v.columns[0] = ["dog"]
        self.assertEqual(v.fields, [(None, None), ("name", db.STRING)])
        # Assert removing a column removes the header.
        v.columns.pop(0)
        self.assertEqual(v.fields, [("name", db.STRING)])
        # Assert new columns with header description.
        v.columns.append(["cat"])
        v.columns.append([3], field=("age", db.INTEGER))
        self.assertEqual(v.fields, [("name", db.STRING), (None, None), ("age", db.INTEGER)])
        # Assert column by name.
        self.assertEqual(v.name, ["Schrödinger"])
        print("pattern.db.Datasheet.fields")

    def test_group(self):
        # Assert Datasheet.group().
        v1 = db.Datasheet(rows=[[1, 2, "a"], [1, 3, "b"], [1, 4, "c"], [0, 0, "d"]])
        v2 = v1.group(0)
        v3 = v1.group(0, function=db.LAST)
        v4 = v1.group(0, function=(db.FIRST, db.COUNT, db.CONCATENATE))
        v5 = v1.group(0, function=db.CONCATENATE, key=lambda j: j > 0)
        self.assertEqual(v2, [[1, 2, "a"], [0, 0, "d"]])
        self.assertEqual(v3, [[1, 4, "c"], [0, 0, "d"]])
        self.assertEqual(v4, [[1, 3, "a,b,c"], [0, 1, "d"]])
        self.assertEqual(v5, [[True, "2,3,4", "a,b,c"], [False, "0", "d"]])
        print("pattern.db.Datasheet.group()")

    def test_slice(self):
        # Assert Datasheet slices.
        v = db.Datasheet([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        v = v.copy()
        self.assertEqual(v.slice(0, 1, 3, 2), [[2, 3], [5, 6], [8, 9]])
        self.assertEqual(v[2], [7, 8, 9])
        self.assertEqual(v[2, 2], 9)
        self.assertEqual(v[2, 1:], [8, 9])
        self.assertEqual(v[0:2], [[1, 2, 3], [4, 5, 6]])
        self.assertEqual(v[0:2, 1], [2, 5])
        self.assertEqual(v[0:2, 0:2], [[1, 2], [4, 5]])
        # Assert new Datasheet for i:j slices.
        self.assertTrue(isinstance(v[0:2], db.Datasheet))
        self.assertTrue(isinstance(v[0:2, 0:2], db.Datasheet))
        print("pattern.db.Datasheet.slice()")

    def test_copy(self):
        # Assert Datasheet.copy().
        v = db.Datasheet([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        self.assertTrue(v.copy(), [[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        self.assertTrue(v.copy(rows=[0]), [[1, 2, 3]])
        self.assertTrue(v.copy(rows=[0], columns=[0]), [[1]])
        self.assertTrue(v.copy(columns=[0]), [[1], [4], [7]])
        print("pattern.db.Datasheet.copy()")

    def test_map(self):
        # Assert Datasheet.map() (in-place).
        v = db.Datasheet(rows=[[1, 2], [3, 4]])
        v.map(lambda x: x + 1)
        self.assertEqual(v, [[2, 3], [4, 5]])
        print("pattern.db.Datasheet.map()")

    def test_json(self):
        # Assert JSON output.
        v = db.Datasheet(rows=[["Schrödinger", 3], ["Hofstadter", 5]])
        self.assertEqual(v.json, '[["Schrödinger", 3], ["Hofstadter", 5]]')
        # Assert JSON output with headers.
        v = db.Datasheet(rows=[["Schrödinger", 3], ["Hofstadter", 5]],
                       fields=[("name", db.STRING), ("age", db.INT)])
        random.seed(0)
        w = db.json.loads(v.json)
        self.assertTrue({"age": 3, "name": "Schrödinger"} in w)
        self.assertTrue({"age": 5, "name": "Hofstadter"} in w)
        print("pattern.db.Datasheet.json")

    def test_flip(self):
        # Assert flip matrix.
        v = db.flip(db.Datasheet([[1, 2], [3, 4]]))
        self.assertEqual(v, [[1, 3], [2, 4]])
        print("pattern.db.flip()")

    def test_truncate(self):
        # Assert string truncate().
        v1 = "a" * 50
        v2 = "a" * 150
        v3 = "aaa " * 50
        self.assertEqual(db.truncate(v1), (v1, ""))
        self.assertEqual(db.truncate(v2), ("a" * 99 + "-", "a" * 51))
        self.assertEqual(db.truncate(v3), (("aaa " * 25).strip(), "aaa " * 25))
        print("pattern.db.truncate()")

    def test_pprint(self):
        pass

#---------------------------------------------------------------------------------------------------


def suite(**kwargs):

    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestUnicode))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestEntities))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestDate))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestUtilityFunctions))


    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestCSV))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestDatasheet))
    return suite

if __name__ == "__main__":

    result = unittest.TextTestRunner(verbosity=1).run(suite())
    sys.exit(not result.wasSuccessful())
