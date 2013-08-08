#!/usr/bin/env python

from types import MethodType
from unittest import TestCase, main as Run

from utils import cszk

tests = (

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
        self.assertEqual(cszk(*tests[i][0]), tests[i][1])

for i in range(len(tests)):
    setattr(TestCSZK, 'test_%02d' % i, lambda self, i=i: self.do_test(i))

if __name__ == '__main__':
    Run()
