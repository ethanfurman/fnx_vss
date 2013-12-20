#!/usr/bin/env python
from __future__ import with_statement

import os
import sys
sys.path.insert(0, '../..')

from tempfile import mkstemp
from types import MethodType
from unittest import TestCase, main as Run

from VSS import Table
from VSS.dbf import Date, Time
from VSS.trulite import ARInvoice, ARAgingLine, ar_open_invoices, ar_invoices, Batch
from VSS.utils import cszk, normalize_address, xrange, suppress, all_equal
from VSS.wellsfargo import RmInvoice, RmPayment, RMFFRecord, lockbox_payments, Int, FederalHoliday, ACHStore, ACHPayment, ACHFile, ACH_ETC, Customer

globals().update(Customer.__members__)

class Test_all_equal(TestCase):

    def test_simple_equal(self):
        for items in (
                (1, 1, 1, 1, 1),
                (21, 21, 21),
                [827, 827, 827, 827, 827],
                [None, None],
                [],
                ):
            self.assertTrue(all_equal(items), '%r not all equal?' % (items, ))

    def test_simple_not_equal(self):
        for items in (
                (1, 1, 1, 1, 11),
                (21, 2, 21),
                [3, 827, 827, 827, 827],
                [None, None, False],
                ):
            self.assertFalse(all_equal(items), '%r all equal?' % (items, ))

    def test_function_equal(self):
        for items, func in (
                ((10, 12, 26, 4, 100), lambda x: x % 2 == 0),
                (('abc', 'def', 'ghi'), lambda x: len(x) == 3),
                ([827, 27, 87, 71, 99], lambda x: x % 2 == 1),
                ([None, None], lambda x: x is None),
                ([], lambda x: x is True),
                ):
            self.assertTrue(all_equal(items, func), '%r not all equal?' % (items, ))

    def test_function_not_equal(self):
        for items, func in (
                ((10, 12, 26, 4, 101), lambda x: x % 2 == 0),
                (('abc', 'defg', 'hij'), lambda x: len(x) == 3),
                ([82, 27, 87, 71, 99], lambda x: x % 2 == 1),
                ([None, None, True], lambda x: x is None),
                ):
            self.assertFalse(all_equal(items, func), '%r all equal?' % (items, ))

cszk_tests = (

    (('SAINT-BRUNO LAC-SAINT-JEAN', '(QUEBEC) GOW 2LO  CANADA'),
     ('', 'SAINT-BRUNO LAC-SAINT-JEAN', 'QUEBEC', 'G0W 2L0', 'CANADA')),

    (('', 'ST-PAUL, QUEBEC JOL 2KO'),
     ('', 'ST-PAUL', 'QUEBEC', 'J0L 2K0', 'CANADA')),

    (('ST-PHILIPPE (QUEBEC)', 'JOL 2KO  CANADA'),
     ('', 'ST-PHILIPPE', 'QUEBEC', 'J0L 2K0', 'CANADA')),

    (('33 PILCHER GATE', 'NOTTINGHAM NG1 1QF  UK'),
     ('33 PILCHER GATE', 'NOTTINGHAM', '', 'NG1 1QF', 'UNITED KINGDOM')),

    (('SACRAMENTO, CA', '95899-7300'),
     ('', 'SACRAMENTO', 'CALIFORNIA', '95899', '')),

    (('106-108 DESVOEUX RD', 'CENTRAL, HONG KONG'),
     ('106-108 DESVOEUX RD', 'CENTRAL', '', '', 'HONG KONG')),

    (('142 G/F WING LOK ST', 'HONG KONG, CHINA'),
     ('142 G/F WING LOK ST', 'HONG KONG', '', '', 'CHINA')),

    (('1408 - C EAST BLVD.', 'CHARLOTTE, N.C. 28203'),
     ('1408 - C EAST BLVD', 'CHARLOTTE', 'NORTH CAROLINA', '28203', '')),

    (('', 'NEW YORK, NEW YORK 10019'),
     ('', 'NEW YORK', 'NEW YORK', '10019', '')),

    (('', 'LOS ANGELES, CA',),
     ('', 'LOS ANGELES', 'CALIFORNIA', '', '')),

    (('SOME CITY, ONTARIO', 'V6T 9K3 , CANADA'),
     ('', 'SOME CITY', 'ONTARIO', 'V6T 9K3', 'CANADA')),

    (('34 MEKIAS EL RODA ST', 'CAIRO, EGYPT'),
     ('34 MEKIAS EL RODA ST', 'CAIRO', '', '', 'EGYPT')),

    (('19 ADISON PL', 'VALLEY STREAM, NY 11580'),
     ('19 ADISON PL', 'VALLEY STREAM', 'NEW YORK', '11580', '')),

    (('19 ADISON PL', 'VALLEY STREAM NY 11580'),
     ('19 ADISON PL', 'VALLEY STREAM', 'NEW YORK', '11580', '')),

    (('COL. DOCTORES', 'MONTERREY N.L. 64710, MEXICO'),
     ('COL DOCTORES', 'MONTERREY NL', '', '64710', 'MEXICO')),

    )

class TestCSZK(TestCase):
    """
    Test the city, state, zip, country function
    """

    def do_test(self, i):
        self.assertEqual(cszk(*cszk_tests[i][0]), cszk_tests[i][1])

for i in range(len(cszk_tests)):
    setattr(TestCSZK, 'test_%02d' % i, lambda self, i=i: self.do_test(i))


norm_tests = (
    ('160 EILEEN WAY',                  '160 EILEEN WAY'),
    ('18930 HWY 145',                   '18930 HIGHWAY 145'),
    ('P.O. BOX 709',                    'PO BOX 709'),
    ('P. O. BOX 182',                   'PO BOX 182'),
    ('P O BOX 555',                     'PO BOX 555'),
    ('PO BOX 339',                      'PO BOX 339'),
    ('POBOX 718',                       'PO BOX 718'),
    ('1097 YATES ST.',                  '1097 YATES ST'),
    ('15908 98TH AVE.',                 '15908 98TH AVE'),
    ('141 LANZA AVENUE',                '141 LANZA AVE'),
    ('85 NE 5TH ST',                    '85 NE 5TH ST'),
    ('111 89TH AVE SW',                 '111 89TH AVE SW'),
    ('1827 FIRST SOUTHWEST',            '1827 FIRST SOUTHWEST'),
    ('1827 FIRST SW',                   '1827 FIRST SOUTHWEST'),
    ('050 E',                           '050 E'),
    ('050 EAST',                        '050 EAST'),
    ('975 WEST ST',                     '975 WEST ST'),
    ('274 EAST ST SOUTH',               '274 EAST ST S'),
    ('274 E ST SOUTH',                  '274 E ST S'),
    ('582 NORTH SOUTH ST',              '582 N SOUTH ST'),
    ('111 N MAIN S',                    '111 N MAIN S'),
    ('819 VALLEY NORTH RD',             '819 VALLEY NORTH RD'),
    ('160 EILEEN WAY # NORTH',          '160 EILEEN WAY # NORTH'),
    ('160 EILEEN WAY #47 NORTH',        '160 EILEEN WAY #47 NORTH'),
    ('18930 HWY 145',                   '18930 HIGHWAY 145'),
    ('1097 YATES ST. FLOOR 5',          '1097 YATES ST FLOOR 5'),
    ('15908 98TH AVE., UNIT 9',         '15908 98TH AVE UNIT 9'),
    ('141 LANZA AVENUE LOWER',          '141 LANZA AVE LOWER'),
    ('85 NE 5TH ST LBBY',               '85 NE 5TH ST LOBBY'),
    ('111 89TH AVE SW DEPARTMENT 23B',  '111 89TH AVE SW DEPT 23B'),
    ('1827 FIRST SOUTHWEST SUITE 11',   '1827 FIRST SOUTHWEST STE 11'),
    ('1827 FIRST SW SUITE 11',          '1827 FIRST SOUTHWEST STE 11'),
    ('050 E SLIP 192',                  '050 E SLIP 192'),
    ('050 EAST SPACE 29',               '050 EAST SPC 29'),
    ('975 WEST ST PIER 9',              '975 WEST ST PIER 9'),
    ('274 EAST ST SOUTH LOT 1',         '274 EAST ST S LOT 1'),
    ('274 E ST SOUTH BUILDING 8',       '274 E ST S BLDG 8'),
    ('582 NORTH SOUTH ST REAR',         '582 N SOUTH ST REAR'),
    ('111 N MAIN S UPPER',              '111 N MAIN S UPPER'),
    ('819 VALLEY NORTH RD ROOM 3',      '819 VALLEY NORTH RD RM 3'),
    )


class TestNormalizeAddress(TestCase):
    """
    Test the normalize address function.
    """

    def do_test(self, i):
        self.assertEqual(normalize_address(norm_tests[i][0]), norm_tests[i][1])

for i in range(len(norm_tests)):
    setattr(TestNormalizeAddress, 'test_%02d' % i, lambda self, i=i: self.do_test(i))

aging_line_tests = (
    (('005002	FORDERER CORNICE WORKS   	053113	557521:2433.50/VARIAN	1-INVCE	475214	1100-00	2917	0'),
     ('005002','FORDERER CORNICE WORKS',Date(2013, 5, 31),'557521:2433.50/VARIAN','1-INVCE','475214','1100-00',2917,0,False)),

    (('005009	**ALUM ROCK HARDWARE &     	042413	526712:GARCIA	1-INVCE	454426	1100-00	15255	0'),
     ('005009','ALUM ROCK HARDWARE &',Date(2013, 4, 24),'526712:GARCIA','1-INVCE','454426','1100-00',15255,0,True)),

    (('005129	CASH SALES - FREMONT     	060513	558300:GREGORY/REMAKE	1-INVCE	476504	1100-00	0	0'),
     ('005129','CASH SALES - FREMONT',Date(2013, 6, 5),'558300:GREGORY/REMAKE','1-INVCE','476504','1100-00',0,0,False)),

    )

class TestARAgingline(TestCase):

    def do_test(self, i):
        self.assertEqual(ARAgingLine(aging_line_tests[i][0]), aging_line_tests[i][1])

for i in range(len(aging_line_tests)):
    setattr(TestARAgingline, 'test_%02d' % i, lambda self, i=i: self.do_test(i))



ar_invoice_tests_text = '''\
fake header :)
005002\tFORDERER CORNICE WORKS   \t051513\t541817:2458.50\t1-INVCE\t465876\t1100-00\t2593\t0
005002\tFORDERER CORNICE WORKS   \t051513\t542587:2458.50\t1-INVCE\t465877\t1100-00\t1701\t0
005002\tFORDERER CORNICE WORKS   \t053113\t557521:2433.50/VARIAN\t1-INVCE\t475214\t1100-00\t2917\t0
005153\tBOB THE GLASSMAN         \t051513\t543806:APPLY\t1-INVCE\t465678\t1100-00\t9517\t0
005153\tBOB THE GLASSMAN         \t051513\t543817:STOCK\t1-INVCE\t465678\t1100-00\t52849\t0
005153\tBOB THE GLASSMAN         \t052913\t546617:LAMI S/S\t4-PAYMT\t465678\t1100-00\t0\t62366
005315\tJOHN MC LAUGHLIN WINDOW  \t050213\t533195:662 MISSION ST\t1-INVCE\t460275\t1100-00\t104232\t0
005315\tJOHN MC LAUGHLIN WINDOW  \t060713\t0606AD:5659\t4-PAYMT\t460275\t1100-00\t0\t104232
005315\tJOHN MC LAUGHLIN WINDOW  \t050213\t533201:662 MISSION ST\t1-INVCE\t460276\t1100-00\t19852\t0
005315\tJOHN MC LAUGHLIN WINDOW  \t060713\t0606AD:5659\t4-PAYMT\t460276\t1100-00\t0\t10000
005319\tDISTINCTIVE DOOR & GLASS \t060513\t561527:559769 RETURN\t1-INVCE\t476612\t1100-00\t0\t0
005337\tI G S GLASS              \t053013\t558161:PILK 6MM\t1-INVCE\t474499\t1100-00\t4387\t0
005338\tKONG MING COMPANY        \t060613\t561236:005338\t1-INVCE\t478320\t1100-00\t5023\t0
005338\tKONG MING COMPANY        \t060613\t0605AD:1704\t4-PAYMT\t478320\t1100-00\t0\t5023'''

ar_invoice_expected = {
    '005002' : {'465876' : [2593, '005002', Date(2013, 5, 15), '541817:2458.50', '1100-00', 'FORDERER CORNICE WORKS', '465876', '465876',
        [
            ARAgingLine('005002\tFORDERER CORNICE WORKS   \t051513\t541817:2458.50\t1-INVCE\t465876\t1100-00\t2593\t0'),
        ],
        False, '541817'],
    '465877' : [1701, '005002', Date(2013, 5, 15), '542587:2458.50', '1100-00', 'FORDERER CORNICE WORKS', '465877', '465877',
        [
            ARAgingLine('005002\tFORDERER CORNICE WORKS   \t051513\t542587:2458.50\t1-INVCE\t465877\t1100-00\t1701\t0'),
        ],
        False, '542587'],
    '475214' : [2917, '005002', Date(2013, 5, 31), '557521:2433.50/VARIAN', '1100-00', 'FORDERER CORNICE WORKS', '475214', '475214',
        [
            ARAgingLine('005002\tFORDERER CORNICE WORKS   \t053113\t557521:2433.50/VARIAN\t1-INVCE\t475214\t1100-00\t2917\t0'),
        ],
        False, '557521']},
    '005153' : {'465678' : [0, '005153', Date(2013, 5, 15), '543806:APPLY; 543817:STOCK; 546617:LAMI S/S', '1100-00', 'BOB THE GLASSMAN', '465678', '465678',
        [
            ARAgingLine('005153\tBOB THE GLASSMAN         \t051513\t543806:APPLY\t1-INVCE\t465678\t1100-00\t9517\t0'),
            ARAgingLine('005153\tBOB THE GLASSMAN         \t051513\t543817:STOCK\t1-INVCE\t465678\t1100-00\t52849\t0'),
            ARAgingLine('005153\tBOB THE GLASSMAN         \t052913\t546617:LAMI S/S\t4-PAYMT\t465678\t1100-00\t0\t62366'),
        ],
        False, '']},
    '005315' : {'460275' : [0, '005315', Date(2013, 5, 2), '533195:662 MISSION ST; 0606AD:5659', '1100-00', 'JOHN MC LAUGHLIN WINDOW', '460275', '460275',
        [
            ARAgingLine('005315\tJOHN MC LAUGHLIN WINDOW  \t050213\t533195:662 MISSION ST\t1-INVCE\t460275\t1100-00\t104232\t0'),
            ARAgingLine('005315\tJOHN MC LAUGHLIN WINDOW  \t060713\t0606AD:5659\t4-PAYMT\t460275\t1100-00\t0\t104232'),
        ],
        False, '533195'],
    '460276' : [9852, '005315', Date(2013, 5, 2), '533201:662 MISSION ST; 0606AD:5659', '1100-00', 'JOHN MC LAUGHLIN WINDOW', '460276', '460276',
        [
            ARAgingLine('005315\tJOHN MC LAUGHLIN WINDOW  \t050213\t533201:662 MISSION ST\t1-INVCE\t460276\t1100-00\t19852\t0'),
            ARAgingLine('005315\tJOHN MC LAUGHLIN WINDOW  \t060713\t0606AD:5659\t4-PAYMT\t460276\t1100-00\t0\t10000'),
        ],
        False, '533201']},
    '005319' : {'476612' : [0, '005319', Date(2013, 6, 5), '561527:559769 RETURN', '1100-00', 'DISTINCTIVE DOOR & GLASS', '476612', '476612',
        [
            ARAgingLine('005319\tDISTINCTIVE DOOR & GLASS \t060513\t561527:559769 RETURN\t1-INVCE\t476612\t1100-00\t0\t0'),
        ],
        False, '561527']},
    '005337' : {'474499' : [4387, '005337', Date(2013, 5, 30), '558161:PILK 6MM', '1100-00', 'I G S GLASS', '474499', '474499',
        [
            ARAgingLine('005337\tI G S GLASS              \t053013\t558161:PILK 6MM\t1-INVCE\t474499\t1100-00\t4387\t0'),
        ],
        False, '558161']},
    '005338' : {'478320' : [0, '005338', Date(2013, 6, 6), '561236:005338; 0605AD:1704', '1100-00', 'KONG MING COMPANY', '478320', '478320',
        [
            ARAgingLine('005338\tKONG MING COMPANY        \t060613\t561236:005338\t1-INVCE\t478320\t1100-00\t5023\t0'),
            ARAgingLine('005338\tKONG MING COMPANY        \t060613\t0605AD:1704\t4-PAYMT\t478320\t1100-00\t0\t5023'),
        ],
        False, '561236']},
    }

class TestARInvoice(TestCase):

    def setUp(self, _cache={}):
        if not _cache:
            fd, self.filename = mkstemp()
            os.write(fd, ar_invoice_tests_text)
            os.close(fd)
            _cache = ar_invoices(self.filename)
        self.invoices = _cache

    def tearDown(self):
        os.remove(self.filename)

    def do_test(self, cust_id):
        calc_invoices = self.invoices
        expt_invoices = ar_invoice_expected.pop(cust_id)
        for inv_num in expt_invoices:
            cinv = calc_invoices[inv_num]
            xinv_values = expt_invoices[inv_num]
            self.assertEqual(cinv.balance, xinv_values[0])
            self.assertEqual(cinv.cust_id, xinv_values[1])
            self.assertEqual(cinv.date, xinv_values[2])
            self.assertEqual(cinv.desc, xinv_values[3])
            self.assertEqual(cinv.gl_acct, xinv_values[4])
            self.assertEqual(cinv.name, xinv_values[5])
            self.assertEqual(cinv.actual_inv_num, xinv_values[6])
            self.assertEqual(cinv.inv_num, xinv_values[7])
            self.assertEqual(cinv.transactions, xinv_values[8])
            self.assertEqual(cinv.starred, xinv_values[9])
            self.assertEqual(cinv.order_num, xinv_values[10])

    def test_000000_ar_open_invoices(self):
        aoi_inv = ar_open_invoices(self.filename)
        aio_inv = dict([(k, v) for (k, v) in self.invoices.items() if v.balance > 0])
        self.assertEqual(aoi_inv.keys(), aio_inv.keys())

    def test_zz(self):
        self.assertEqual(ar_invoice_expected.keys(), [])

for cust_id in ar_invoice_expected:
    setattr(TestARInvoice, 'test_%s' % cust_id, lambda self, cust_id=cust_id: self.do_test(cust_id))


class TestRMFFRecord(TestCase):

    def test_PR(self):
        rmffrec = RMFFRecord('PR|LBX|C|9450|121000248|74478|122242649|001868454|130613||||||||~')
        test_tuple = (('PR','LBX','C',9450,'121000248','74478','122242649','001868454',Date(2013,6,13),'','','','','','','',''))
        self.assertEqual(rmffrec, test_tuple)
        self.assertEqual(rmffrec.prrt, test_tuple[0])
        self.assertEqual(rmffrec.prpt, test_tuple[1])
        self.assertEqual(rmffrec.prcd, test_tuple[2])
        self.assertEqual(rmffrec.prpa, test_tuple[3])
        self.assertEqual(rmffrec.prdr, test_tuple[4])
        self.assertEqual(rmffrec.prda, test_tuple[5])
        self.assertEqual(rmffrec.pror, test_tuple[6])
        self.assertEqual(rmffrec.proa, test_tuple[7])
        self.assertEqual(rmffrec.pred, test_tuple[8])

    def test_SP(self):
        rmffrec = RMFFRecord('SP|74478||0001|000001|2293859|||001||||00000000000|||995319|||||||||||||||||||||||||||||||||||~')
        test_tuple = (('SP','74478','',1,1,'2293859',Date(),'',1,'','','','00000000000',Date(),'','995319','','','','','','','','','','','','','','','','','','','','','','',Date(),'','','','','','','','','','','',''))
        self.assertEqual(rmffrec.sprt, test_tuple[0])
        self.assertEqual(rmffrec.spln, test_tuple[1])
        self.assertEqual(rmffrec.spcn, test_tuple[2])
        self.assertEqual(rmffrec.spbn, test_tuple[3])
        self.assertEqual(rmffrec.spis, test_tuple[4])
        self.assertEqual(rmffrec.spvt, test_tuple[5])
        self.assertEqual(rmffrec.sppd, test_tuple[6])
        self.assertEqual(rmffrec.sprz, test_tuple[7])
        self.assertEqual(rmffrec.spes, test_tuple[8])
        self.assertEqual(rmffrec.spc1, test_tuple[9])
        self.assertEqual(rmffrec.spc2, test_tuple[10])
        self.assertEqual(rmffrec.spc3, test_tuple[11])
        self.assertEqual(rmffrec.spc4, test_tuple[12])
        self.assertEqual(rmffrec.spcd, test_tuple[13])
        self.assertEqual(rmffrec.spf1, test_tuple[14])
        self.assertEqual(rmffrec.spf2, test_tuple[15])

    def test_PA(self):
        rmffrec = RMFFRecord('PA|PR|JERRY L PICKARD||||||||||ABA|||||||||||||||~')
        test_tuple = (('PA','PR','JERRY L PICKARD','','','','','','','','','','ABA','','','','','','','','','','','','','',Date(),Date()))
        self.assertEqual(rmffrec.part, test_tuple[0])
        self.assertEqual(rmffrec.paec, test_tuple[1])
        self.assertEqual(rmffrec.pan1, test_tuple[2])
        self.assertEqual(rmffrec.paan, test_tuple[3])
        self.assertEqual(rmffrec.pasa1, test_tuple[4])
        self.assertEqual(rmffrec.pasa2, test_tuple[5])
        self.assertEqual(rmffrec.pac1, test_tuple[6])
        self.assertEqual(rmffrec.pasp, test_tuple[7])
        self.assertEqual(rmffrec.papc, test_tuple[8])
        self.assertEqual(rmffrec.pacc, test_tuple[9])
        self.assertEqual(rmffrec.pacn, test_tuple[10])
        self.assertEqual(rmffrec.pacy, test_tuple[11])
        self.assertEqual(rmffrec.pabi, test_tuple[12])

    def test_IV(self):
        rmffrec = RMFFRecord('IV|IV|XXXXXXXXXXX||9450|00000000000000000|00000000000000000||~')
        test_tuple = (('IV','IV','XXXXXXXXXXX','',9450,0,0,'',0))
        self.assertEqual(rmffrec.ivrt, test_tuple[0])
        self.assertEqual(rmffrec.ivrq, test_tuple[1])
        self.assertEqual(rmffrec.ivri, test_tuple[2])
        self.assertEqual(rmffrec.ivac, test_tuple[3])
        self.assertEqual(rmffrec.ivpd, test_tuple[4])
        self.assertEqual(rmffrec.ivga, test_tuple[5])
        self.assertEqual(rmffrec.ivda, test_tuple[6])
        self.assertEqual(rmffrec.ivar, test_tuple[7])
        self.assertEqual(rmffrec.ivaa, test_tuple[8])

    def test_SI(self):
        rmffrec = RMFFRecord('SI|000001|001|9||001|00000000000|011141||||00000000000|00000000000|00000000000|00000000000|||||||||||||||||||||||||||||||||||~')
        test_tuple = (('SI',1,1,'9','',1,0,'011141','','','','00000000000','00000000000','00000000000','00000000000',Date(),'','','','','','','','','','','','','','','','','','','','','','','','','','','','',Date(),'','','','',''))
        self.assertEqual(rmffrec.sirt, test_tuple[0])
        self.assertEqual(rmffrec.sisn, test_tuple[1])
        self.assertEqual(rmffrec.sion, test_tuple[2])
        self.assertEqual(rmffrec.sioi, test_tuple[3])
        self.assertEqual(rmffrec.sira, test_tuple[4])
        self.assertEqual(rmffrec.sies, test_tuple[5])
        self.assertEqual(rmffrec.siia, test_tuple[6])


rm_invoice_tests = (
    (('IV|IV|XXXXXXXXXXX||9450|00000000000000000|00000000000000000||~',
      'SI|000001|001|9||001|00000000000|011141||||00000000000|00000000000|00000000000|00000000000|||||||||||||||||||||||||||||||||||~',
      ('XXXXXXXXXXX', 9450),
      )),
    (('IV|IV|467223||13737|00000000000000000|00000000000000000||~',
      'SI|000003|001|0||003|00000000000|0000000||||00000000000|00000000000|00000000000|00000000000|||||||||||||||||||||||||||||||||||~',
      ('467223', 13737),
      )),
    (('IV|IV|99999999999||-2488|00000000000000000|00000000000000000||~',
      'SI|000011|012|9||011|00000000000|9999999||||00000000000|00000000000|00000000000|00000000000|||||||||||||||||||||||||||||||||||~',
      ('99999999999', -2488),
      )),
    (('IV|IV|99999999999||106938|00000000000000000|00000000000000000||~',
      'SI|000031|013|9||031|00000000000|9999999||||00000000000|00000000000|00000000000|00000000000|||||||||||||||||||||||||||||||||||~',
      ('99999999999', 106938),
      )),
    )

class TestRmInvoice(TestCase):

    def do_test(self, i):
        iv_text = rm_invoice_tests[i][0]
        si_text = rm_invoice_tests[i][1]
        inv_num, amount = rm_invoice_tests[i][2]
        rmi = RmInvoice(RMFFRecord(iv_text))
        rmi.add_record(RMFFRecord(si_text))
        self.assertEqual(rmi.inv_num, inv_num)
        self.assertEqual(rmi.amount, amount)

for i in range(len(rm_invoice_tests)):
    setattr(TestRmInvoice, 'test_%02d' % i, lambda self, i=i: self.do_test(i))



rm_payment_tests = (
    (('FH|79|130521|2307~',
      'BH|2|130613|2307~',
      'PR|LBX|C|9450|121000248|74478|122242649|001868454|130613||||||||~',
      'SP|74478||0001|000001|2293859|||001||||00000000000|||995319|||||||||||||||||||||||||||||||||||~',
      'PA|PR|JERRY L PICKARD||||||||||ABA|||||||||||||||~',
      'IV|IV|XXXXXXXXXXX||9450|00000000000000000|00000000000000000||~',
      'SI|000001|001|9||001|00000000000|011141||||00000000000|00000000000|00000000000|00000000000|||||||||||||||||||||||||||||||||||~'),
      ('79', 2, '995319', 9450, Date(2013, 6, 13), 0, 'JERRY L PICKARD'),
    ),
    (('FH|83|130613|2307~',
      'BH|5|130613|2307~',
      'PR|LBX|C|23303|121000248|74478|121137027|0302406770|130613||||||||~',
      'SP|74478||0001|000015|0656835|||015||||00000000000|||031535|||||||||||||||||||||||||||||||||||~',
      'PA|PR|HOUSE OF GLASS||||||||||ABA|||||||||||||||~',
      'IV|IV|452940||7308|00000000000000000|00000000000000000||~',
      'SI|000015|001|0||015|00000000000|012817||||00000000000|00000000000|00000000000|00000000000|||||||||||||||||||||||||||||||||||~',
      'IV|IV|452941||15995|00000000000000000|00000000000000000||~',
      'SI|000015|002|9||015|00000000000|012817||||00000000000|00000000000|00000000000|00000000000|||||||||||||||||||||||||||||||||||~',),
      ('83', 5, '031535', 23303, Date(2013, 6, 13), 0, 'HOUSE OF GLASS'),
    ),
    )

class TestRmPayment(TestCase):

    def do_test(self, i):
        fh = RMFFRecord(rm_payment_tests[i][0][0])
        bh = RMFFRecord(rm_payment_tests[i][0][1])
        pr = RMFFRecord(rm_payment_tests[i][0][2])
        sp = RMFFRecord(rm_payment_tests[i][0][3])
        pa = RMFFRecord(rm_payment_tests[i][0][4])
        payment = RmPayment(fh, bh, pr)
        payment.add_record(sp)
        payment.add_record(pa)
        for rec in rm_payment_tests[i][0][5:]:
            rec = RMFFRecord(rec)
            if rec.id == 'IV':
                invoice = RmInvoice(rec)
                payment.add_invoice(invoice)
            elif rec.id == 'SI':
                invoice.add_record(rec)
            else:
                raise ValueError("unexpected record: %r" % rec)
        fn, bn, chk_num, credit, post_date, debit, payer = rm_payment_tests[i][1]
        self.assertEqual(fn, payment.file_control)
        self.assertEqual(bn, payment.batch_control)
        self.assertEqual(chk_num, payment.ck_num)
        self.assertEqual(credit, payment.credit)
        self.assertEqual(post_date, payment.date)
        self.assertEqual(debit, payment.debit)
        self.assertEqual(payer, payment.payer)

for i in range(len(rm_payment_tests)):
    setattr(TestRmPayment, 'test_%02d' % i, lambda self, i=i: self.do_test(i))

class TestInt(TestCase):

    errors = (
            '1.0.91',
            '9.827',
            '$ .001',
            '$73.918.2192',
            )

    values = (
            ('81729', 81729),
            ('81729.', 8172900),
            ('247.1', 24710),
            ('59.12', 5912),
            ('$ 4821', 4821),
            ('$817.9', 81790),
            ('$33.99', 3399),
            )

    def test_error(self):
        for text in self.errors:
            self.assertRaises(ValueError, Int, text)

    def test_int(self):
        for text, value in self.values:
            self.assertEqual(Int(text), value)


class TestFederalHoliday(TestCase):

    values = (
            (FederalHoliday.NewYear,
                ((2012, Date(2012, 1, 2)), (2013, Date(2013, 1, 1)), (2014, Date(2014, 1, 1)), (2015, Date(2015, 1, 1)), (2016, Date(2016, 1, 1)), (2017, Date(2017, 1, 2)))),
            (FederalHoliday.MartinLutherKingJr,
                ((2012, Date(2012, 1, 16)),(2013, Date(2013, 1, 21)),(2014, Date(2014, 1, 20)),(2015, Date(2015, 1, 19)),(2016, Date(2016, 1, 18)),(2017, Date(2017, 1, 16)))),
            (FederalHoliday.President,
                ((2012, Date(2012, 2, 20)),(2013, Date(2013, 2, 18)),(2014, Date(2014, 2, 17)),(2015, Date(2015, 2, 16)),(2016, Date(2016, 2, 15)),(2017, Date(2017, 2, 20)))),
            (FederalHoliday.Memorial,
                ((2012, Date(2012, 5, 28)),(2013, Date(2013, 5, 27)),(2014, Date(2014, 5, 26)),(2015, Date(2015, 5, 25)),(2016, Date(2016, 5, 30)),(2017, Date(2017, 5, 29)))),
            (FederalHoliday.Independence,
                ((2012, Date(2012, 7, 4)),(2013, Date(2013, 7, 4)),(2014, Date(2014, 7, 4)),(2015, Date(2015, 7, 4)),(2016, Date(2016, 7, 4)),(2017, Date(2017, 7, 4)))),
            (FederalHoliday.Labor,
                ((2012, Date(2012, 9, 3)),(2013, Date(2013, 9, 2)),(2014, Date(2014, 9, 1)),(2015, Date(2015, 9, 7)),(2016, Date(2016, 9, 5)),(2017, Date(2017, 9, 4)))),
            (FederalHoliday.Columbus,
                ((2012, Date(2012, 10, 8)),(2013, Date(2013, 10, 14)),(2014, Date(2014, 10, 13)),(2015, Date(2015, 10, 12)),(2016, Date(2016, 10, 10)),(2017, Date(2017, 10, 9)))),
            (FederalHoliday.Veterans,
                ((2012, Date(2012, 11, 12)),(2013, Date(2013, 11, 11)),(2014, Date(2014, 11, 11)),(2015, Date(2015, 11, 11)),(2016, Date(2016, 11, 11)),(2017, Date(2017, 11, 11)))),
            (FederalHoliday.Thanksgiving,
                ((2012, Date(2012, 11, 22)),(2013, Date(2013, 11, 28)),(2014, Date(2014, 11, 27)),(2015, Date(2015, 11, 26)),(2016, Date(2016, 11, 24)),(2017, Date(2017, 11, 23)))),
            (FederalHoliday.Christmas,
                ((2012, Date(2012, 12, 25)),(2013, Date(2013, 12, 25)),(2014, Date(2014, 12, 25)),(2015, Date(2015, 12, 25)),(2016, Date(2016, 12, 26)),(2017, Date(2017, 12, 25)))),
            )


    def _test_self_date(self, enum, year, date):
        self.assertEqual(enum.date(year), date)

    ns = vars()
    for enum, dates in values:
        for year, date in dates:
            ns['test_%s_%d' % (enum.name, year)] = lambda self, enum=enum, year=year, date=date: self._test_self_date(enum, year, date)


    def _test_holidays_by_year(self, year, holidays):
        enum_holidays = tuple([e.date(year) for e in FederalHoliday])
        self.assertEqual(enum_holidays, holidays)

    enums = []
    date_values = []
    for enum, dates in values:
        enums.append(enum)
        target_year = []
        for year, date in dates:
            target_year.append(date)
        date_values.append(target_year)
    for yearly_holidays in zip(*date_values):
        year = yearly_holidays[0].year
        ns['test_%s_holidays' % year] = lambda self, year=year, holidays=yearly_holidays: self._test_holidays_by_year(year, holidays)

    
    next_business_day_values = (
            (Date(2013, 12, 30), (Date(2013, 12, 31), Date(2014,  1,  2), Date(2014,  1,  3), Date(2014,  1,  6))),
            (Date(2008,  3, 15), (Date(2008,  3, 17), Date(2008,  3, 18), Date(2008,  3, 19), Date(2008,  3, 20))),
            (Date(2008,  3, 16), (Date(2008,  3, 17), Date(2008,  3, 18), Date(2008,  3, 19), Date(2008,  3, 20))),
            (Date(2010,  5, 21), (Date(2010,  5, 25), Date(2010,  5, 26), Date(2010,  5, 27), Date(2010,  5, 28))),
            )

    def _test_next_business_day(self, current, forward, next):
        self.assertEqual(FederalHoliday.next_business_day(current, forward), next)

    for src_date, target_dates in next_business_day_values:
        for i, tgt_date in enumerate(target_dates):
            i += 1
            ns['test_%s-%s-%s_forward_%d' % (src_date.year, src_date.month, src_date.day, i)] = (
                lambda self, date=src_date, correct=tgt_date, forward=i: self._test_next_business_day(current=date, forward=forward, next=correct)
                )

class TestACH(TestCase):

    ns = vars()

    def setUp(self):
        hndl, self.tmpfile = mkstemp()
        os.close(hndl)
        self.store = Table(self.tmpfile, 'filedate D; filemod C(1)', dbf_type='db3')
        self.ACHStore = ACHStore(self.tmpfile)
        self.today = Date.today()
        self.file_id = '1900918292'
        self.company_name = 'TRULITE WSG LLC'
        self.company_id = self.file_id
    
    def tearDown(self):
        os.remove(self.tmpfile)

    def test_too_many_files(self):
        with self.store:
            self.store.append((self.today, 'Z'))
        self.assertRaises(ValueError, self.ACHStore.get_achfile, self.company_name, self.company_id, self.file_id)

    def test_empty_file(self):
        filen = self.ACHStore.get_achfile(self.company_name, self.company_id, self.file_id)
        with self.store:
            self.assertEqual(self.store[-1], (self.today, 'A'))

    def test_all_filenames(self):
        for letter in xrange(start='A', count=26, step=lambda ltr: chr(ord(ltr)+1)):
            filename = self.ACHStore.get_achfile(self.company_name, self.company_id, self.file_id).filename
            self.assertEqual(filename, 'ACH_%s_%s' % (self.today.ymd(), letter))
            with self.store:
                self.assertEqual(self.store[-1], (self.today, letter))

    routing_numbers = (
            '076401251',
            '123456120',
            '987654320',
            '369246576',
            '864123592',
            '192837644',
            '641699773',
            )

    def _test_validate_routing(self, rtng):
        bad_chk_digits = '0123456789'.replace(rtng[-1],'')
        self.assertEqual(ACHPayment.validate_routing(rtng), None)
        for bcd in bad_chk_digits:
            rtng = rtng[:-1] + bcd
            self.assertRaises(ValueError, ACHPayment.validate_routing, rtng)

    for rn in routing_numbers:
            ns['test_routing_number_%s' % rn] = (
                lambda self, rn=rn: self._test_validate_routing(rtng=rn)
                )


    vendors = (
            ('INVOICES', 'CCD', 'GLASS SOURCE', '123456', '071000039', '8172904027', ACH_ETC.ck_credit, 'domestic', 100),
            ('INVOICES', 'CCD', 'GLASS SOURCE', '246855', '071000039', '8172904027', ACH_ETC.ck_credit, 'domestic', 37118),
            ('INVOICES', 'CCD', 'Super Silica Sands', '987654', '071000013', '24584196', ACH_ETC.ck_credit, 'domestic', 299),
            ('supplies', 'CCD', 'Wax on Wax off', '192837', '043000096', '1642615987224584196', ACH_ETC.ck_credit, 'domestic', 795),
            ('Supplies', 'CCD', 'ACME Glass and Coffee Grounds', '579135', '125000105', '9154876', ACH_ETC.ck_credit, 'domestic', 25),
            )
    def test_single_vendor_single_payment(self):
        target = [
                '101 0910000191900918292YYYYYYTTTTA094101WELLS FARGO            TRULITE WSG LLC                ',
                '5200TRULITE WSG LLC                     1900918292CCDINVOICES  yyyyyyYYYYYY   1091000010000001',
				'6220710000398172904027       0000000100123456         GLASS SOURCE            0091000010000001',
				'820000000100071000030000000000000000000001001900918292                         091000010000001',
				'9000001000001000000010007100003000000000000000000000100                                       ',
                ]

        ach_file = self.ACHStore.get_achfile(self.company_name, self.company_id, self.file_id)
        today = ach_file.today
        time = ach_file.time
        next_business_day = FederalHoliday.next_business_day(today, 2)
        target[0] = target[0].replace('YYYYYY', today.strftime('%y%m%d')).replace('TTTT', time.strftime('%H%M'))
        target[1] = target[1].replace('yyyyyy', today.strftime('%b %d').upper()).replace('YYYYYY', next_business_day.strftime('%y%m%d'))
        payment = ACHPayment(*self.vendors[0])
        ach_file.add_payment(payment)
        ach_file.save_at('.')
        with open(ach_file.filename) as file:
            contents = file.read()
        lines = contents.split('\n')
        for should_be, found in zip(target, lines):
            self.assertEqual(should_be, found)

    def test_single_vendor_multi_payment(self):
        target = [
                '101 0910000191900918292YYYYYYTTTTA094101WELLS FARGO            TRULITE WSG LLC                ',
                '5200TRULITE WSG LLC                     1900918292CCDINVOICES  yyyyyyYYYYYY   1091000010000001',
				'6220710000398172904027       0000000100123456         GLASS SOURCE            0091000010000001',
				'6220710000398172904027       0000037118246855         GLASS SOURCE            0091000010000002',
				'820000000200142000060000000000000000000372181900918292                         091000010000001',
				'9000001000001000000020014200006000000000000000000037218                                       ',
                ]

        ach_file = self.ACHStore.get_achfile(self.company_name, self.company_id, self.file_id)
        today = ach_file.today
        time = ach_file.time
        next_business_day = FederalHoliday.next_business_day(today, 2)
        target[0] = target[0].replace('YYYYYY', today.strftime('%y%m%d')).replace('TTTT', time.strftime('%H%M'))
        target[1] = target[1].replace('yyyyyy', today.strftime('%b %d').upper()).replace('YYYYYY', next_business_day.strftime('%y%m%d'))
        ach_file.add_payment(ACHPayment(*self.vendors[0]))
        ach_file.add_payment(ACHPayment(*self.vendors[1]))
        ach_file.save_at('.')
        with open(ach_file.filename) as file:
            contents = file.read()
        lines = contents.split('\n')
        for should_be, found in zip(target, lines):
            self.assertEqual(should_be, found)

    def test_multi_vendor_multi_payment(self):
        target = [
                '101 0910000191900918292YYYYYYTTTTA094101WELLS FARGO            TRULITE WSG LLC                ',
                '5200TRULITE WSG LLC                     1900918292CCDINVOICES  yyyyyyYYYYYY   1091000010000001',
				'6220710000398172904027       0000000100123456         GLASS SOURCE            0091000010000001',
				'6220710000398172904027       0000037118246855         GLASS SOURCE            0091000010000002',
				'62207100001324584196         0000000299987654         SUPER SILICA SANDS      0091000010000003',
				'820000000300213000070000000000000000000375171900918292                         091000010000001',
				'9000001000001000000030021300007000000000000000000037517                                       ',
                ]

        ach_file = self.ACHStore.get_achfile(self.company_name, self.company_id, self.file_id)
        today = ach_file.today
        time = ach_file.time
        next_business_day = FederalHoliday.next_business_day(today, 2)
        target[0] = target[0].replace('YYYYYY', today.strftime('%y%m%d')).replace('TTTT', time.strftime('%H%M'))
        target[1] = target[1].replace('yyyyyy', today.strftime('%b %d').upper()).replace('YYYYYY', next_business_day.strftime('%y%m%d'))
        ach_file.add_payment(ACHPayment(*self.vendors[0]))
        ach_file.add_payment(ACHPayment(*self.vendors[1]))
        ach_file.add_payment(ACHPayment(*self.vendors[2]))
        ach_file.save_at('.')
        with open(ach_file.filename) as file:
            contents = file.read()
        lines = contents.split('\n')
        for should_be, found in zip(target, lines):
            self.assertEqual(should_be, found)

    def test_multi_batch(self):
        target = [
                '101 0910000191900918292YYYYYYTTTTA094101WELLS FARGO            TRULITE WSG LLC                ',
                '5200TRULITE WSG LLC                     1900918292CCDINVOICES  yyyyyyYYYYYY   1091000010000001',
				'6220710000398172904027       0000000100123456         GLASS SOURCE            0091000010000001',
				'6220710000398172904027       0000037118246855         GLASS SOURCE            0091000010000002',
				'62207100001324584196         0000000299987654         SUPER SILICA SANDS      0091000010000003',
				'820000000300213000070000000000000000000375171900918292                         091000010000001',
                '5200TRULITE WSG LLC                     1900918292CCDSUPPLIES  yyyyyyYYYYYY   1091000010000002',
				'622043000096426159872245841960000000795192837         WAX ON WAX OFF          0091000010000001',
				'820000000100043000090000000000000000000007951900918292                         091000010000002',
				'9000002000001000000040025600016000000000000000000038312                                       ',
                ]

        ach_file = self.ACHStore.get_achfile(self.company_name, self.company_id, self.file_id)
        today = ach_file.today
        time = ach_file.time
        next_business_day = FederalHoliday.next_business_day(today, 2)
        target[0] = target[0].replace('YYYYYY', today.strftime('%y%m%d')).replace('TTTT', time.strftime('%H%M'))
        target[1] = target[1].replace('yyyyyy', today.strftime('%b %d').upper()).replace('YYYYYY', next_business_day.strftime('%y%m%d'))
        target[6] = target[6].replace('yyyyyy', today.strftime('%b %d').upper()).replace('YYYYYY', next_business_day.strftime('%y%m%d'))
        ach_file.add_payment(ACHPayment(*self.vendors[0]))
        ach_file.add_payment(ACHPayment(*self.vendors[1]))
        ach_file.add_payment(ACHPayment(*self.vendors[2]))
        ach_file.add_payment(ACHPayment(*self.vendors[3]))
        ach_file.save_at('.')
        with open(ach_file.filename) as file:
            contents = file.read()
        lines = contents.split('\n')
        for should_be, found in zip(target, lines):
            self.assertEqual(should_be, found)

    def test_multi_batch2(self):
        target = [
                '101 0910000191900918292YYYYYYTTTTA094101WELLS FARGO            TRULITE WSG LLC                ',
                '5200TRULITE WSG LLC                     1900918292CCDINVOICES  yyyyyyYYYYYY   1091000010000001',
				'6220710000398172904027       0000000100123456         GLASS SOURCE            0091000010000001',
				'6220710000398172904027       0000037118246855         GLASS SOURCE            0091000010000002',
				'62207100001324584196         0000000299987654         SUPER SILICA SANDS      0091000010000003',
				'820000000300213000070000000000000000000375171900918292                         091000010000001',
                '5200TRULITE WSG LLC                     1900918292CCDSUPPLIES  yyyyyyYYYYYY   1091000010000002',
				'622043000096426159872245841960000000795192837         WAX ON WAX OFF          0091000010000001',
				'6221250001059154876          0000000025579135         ACME GLASS AND COFFEE   0091000010000002',
				'820000000200168000190000000000000000000008201900918292                         091000010000002',
				'9000002000002000000050038100026000000000000000000038337                                       ',
                ]


        ach_file = self.ACHStore.get_achfile(self.company_name, self.company_id, self.file_id)
        today = ach_file.today
        time = ach_file.time
        next_business_day = FederalHoliday.next_business_day(today, 2)
        target[0] = target[0].replace('YYYYYY', today.strftime('%y%m%d')).replace('TTTT', time.strftime('%H%M'))
        target[1] = target[1].replace('yyyyyy', today.strftime('%b %d').upper()).replace('YYYYYY', next_business_day.strftime('%y%m%d'))
        target[6] = target[6].replace('yyyyyy', today.strftime('%b %d').upper()).replace('YYYYYY', next_business_day.strftime('%y%m%d'))
        ach_file.add_payment(ACHPayment(*self.vendors[0]))
        ach_file.add_payment(ACHPayment(*self.vendors[1]))
        ach_file.add_payment(ACHPayment(*self.vendors[2]))
        ach_file.add_payment(ACHPayment(*self.vendors[3]))
        ach_file.add_payment(ACHPayment(*self.vendors[4]))
        ach_file.save_at('.')
        with open(ach_file.filename) as file:
            contents = file.read()
        lines = contents.split('\n')
        for should_be, found in zip(target, lines):
            self.assertEqual(should_be, found)

class Test_suppress(TestCase):

    def test_no_exception(self):
        with suppress(ValueError):
            self.assertEqual(pow(2, 5), 32)

    def test_exact_exception(self):
        with suppress(TypeError):
            len(5)

    def test_multiple_exception_args(self):
        with suppress(ZeroDivisionError, TypeError):
            len(5)

    def test_exception_hierarchy(self):
        with suppress(LookupError):
            'Hello'[50]

if __name__ == '__main__':
    Run()
