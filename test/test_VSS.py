#!/usr/bin/env python

import os
import sys
sys.path.insert(0, '../..')

from tempfile import mkstemp
from types import MethodType
from unittest import TestCase, main as Run

from dbf import Date
from VSS.trulite import ARInvoice, ARAgingLine, ar_open_invoices, ar_invoices
from VSS.utils import cszk
from VSS.wellsfargo import RmInvoice, RmPayment, RMFFRecord, lockbox_payments, Int, FederalHoliday


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
     ('1408 - C EAST BLVD.', 'CHARLOTTE', 'NORTH CAROLINA', '28203', '')),

    (('', 'NEW YORK, NEW YORK 10019'),
     ('', 'NEW YORK', 'NEW YORK', '10019', '')),

    (('', 'LOS ANGELES, CA',),
     ('', 'LOS ANGELES', 'CALIFORNIA', '', '')),

    (('SOME CITY, ONTARIO', 'V6T 9K3 , CANADA'),
     ('', 'SOME CITY', 'ONTARIO', 'V6T 9K3', 'CANADA')),

    )

class TestCSZK(TestCase):
    """
    Test the city, state, zip, country function
    """

    def do_test(self, i):
        self.assertEqual(cszk(*cszk_tests[i][0]), cszk_tests[i][1])

for i in range(len(cszk_tests)):
    setattr(TestCSZK, 'test_%02d' % i, lambda self, i=i: self.do_test(i))



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

    def do_test(self, enum, year, date):
        self.assertEqual(enum.date(year), date)

    ns = vars()
    for enum, values in values:
        for year, date in values:
            ns['test_%s_%d' % (enum.name, year)] = lambda self, enum=enum, year=year, date=date: self.do_test(enum, year, date)

if __name__ == '__main__':
    Run()
