from __future__ import with_statement
from datetime import timedelta
from itertools import groupby
from VSS import Table, Month, Weekday, days_per_month, AutoEnum, IntEnum, OrderedDict
from VSS.BBxXlate.bbxfile import BBxFile
from VSS.path import Path
from VSS.utils import one_day, bb_text_to_date, text_to_date, text_to_time, xrange, Date, Time, OrderedDict
from VSS.finance import ACHPayment

try:
    next
except NameError:
    from .dbf import next, property

one_day = timedelta(1)

def Int(text):
    '''return `text` converted into pennies ($ is allowed)'''
    text = text.strip('$ ')
    if not text:
        return 0
    if '.' not in text:
        return int(text)
    if text.count('.') > 1:
        raise ValueError('too many decimal points: %s' % text)
    elif len(text) - text.rfind('.') > 3:
        raise ValueError('precision loss: amounts less than 1 penny: %s' % text)
    dollars, cents = text.split('.')
    cents = cents + '0' * (2 - len(cents))
    return int(dollars + cents)

report_types = {
    'R02'  : 'Outstanding Check Report',
    'R03'  : 'Posted Item Report',
    'R04'  : 'Void and Cancel Report',
    'R05'  : 'Issue Notice Not Received Report',
    'R06'  : 'Prior Paid Report',
    'R07'  : 'Credit Report',
    'R08'  : 'Bank Originated Entry Report',
    'R09'  : 'Stop Payment Report',
    'R10'  : 'Match Paid Report',
    'R11'  : 'Issue This Cycle Report',
    'R12'  : 'Paid Check Report',
    'R14'  : 'Unpaid Check Report',
    'R15'  : 'Reversed Check Report',
    'R18'  : 'Deposits',
    }

transaction_types = {
    '007'  : 'Check Reversal',
    '058'  : 'Other Debit',
    '008'  : 'Other Debit Reversal',
    '078'  : 'Customer Deposit',
    '028'  : 'Customer Deposit Reversal',
    '031'  : 'Report Header',
    '079'  : 'Other Credit',
    '029'  : 'Other Credit Reversal',
    '320'  : 'Check Register',
    '054'  : 'Bank Originated Stop Pay',
    '370'  : 'Cancelled Register -- Item sent to the bank.',
    '055'  : 'Customer Stop Pay',
    '056'  : 'Released or Expired Stop Pay',
    '430'  : 'Void Register with Zero Amount -- Item was not issued.',
    '057'  : 'Check',
    }

class OutboundReportDetail(object):
    def __init__(self, data):
        self._data = data
        self.__doc__ = ' - '.join([
                report_types[self.id],
                transaction_types[self.transaction],
                ])
    @property
    def id(self):
        return self._data[:3]
    @property
    def serial(self):
        return int(self._data[3:13])
    @property
    def transaction(self):
        return self._data[13:16]
    @property
    def issue_date(self):
        return bb_text_to_date(self._data[16:22])
    @property
    def amount(self):
        return int(self._data[22:32])
    @property
    def paid_date(self):
        return bb_text_to_date(self._data[32:38])
    @property
    def misc(self):
        return self._data[39:-1].strip()
    def __repr__(self):
        return "id: %s, serial: %s, transaction: %s, issue_date: %s, amount: %s, paid_date: %s, misc: %s" % (
                self.id, self.serial, self.transaction, self.issue_date,
                self.amount, self.paid_date, self.misc,
                )

class OutboundReportHeader(object):
    def __init__(self, data):
        self._data = data
        self.__doc__ = report_types[self.identifier]
    @property
    def id(self):
        return self._data[:2]
    @property
    def account(self):
        return self._data[2:13]
    @property
    def identifier(self):
        return self._data[13:16]
    @property
    def print_date(self):
        return bb_text_to_date(self._data[16:22])
    @property
    def begin_date(self):
        return bb_text_to_date(self._data[22:28])
    @property
    def end_date(self):
        return bb_text_to_date(self._data[28:34])
    @property
    def misc(self):
        return self._data[34:]
    def __repr__(self):
        return "id: %s, account: %s, identifier: %s, print_date: %s, begin_date: %s, end_date: %s, misc: %s" % (
                self.id, self.account, self.identifier, self.print_date,
                self.begin_date, self.end_date, self.misc,
                )

class OutboundReportTrailer(object):
    def __init__(self, data):
        self._data = data
    @property
    def id(self):
        return self._data[:2]
    @property
    def credit_count(self):
        return int(self._data[3:9])
    @property
    def credit_amount(self):
        return int(self._data[10:21])
    @property
    def debit_count(self):
        return int(self._data[23:29])
    @property
    def debit_amount(self):
        return int(self._data[30:41])
    @property
    def misc(self):
        return self._data[41:]
    def __repr__(self):
        return "id: %s, credit_count: %s, credit_amount: %s, debit_count: %s, debit_amount: %s, misc: %s" % (
                self.id, self.credit_count, self.credit_amount,
                self.debit_count, self.debit_amount, self.misc,
                )


class OutboundReportIterator(object):
    def __init__(self, filename):
        self._data = [l.strip() for l in open(filename).readlines()]
        self.header = OutboundReportHeader(data[0])
        self.trailer = OutboundReportTrailer(data[-1])
        self._data = data[1:-1]
        self._pointer = 0
        self._length = len(self._data)
        self.__doc__ = self._header.__doc__
    def __iter__(self):
        return self
    def __next__(self):
        '''iterates through the data records'''
        if self._pointer >= self._length:
            raise StopIteration
        current = self._pointer
        self._pointer += 1
        return OutboundReportDetail(self._data[current])
    next = __next__
    def reset():
        self._pointer = 0


class IFTRecord(tuple):
    __slots__ = ()
    fields = [
            'action',
            'deposit_date',
            'lockbox_no',
            'site_id',
            'depository_account',
            'batch',
            'transaction_number',
            'record_type',
            'sequence_number',
            'check_amount',
            'serial_number',
            'check_account_number',
            'check_date',
            'check_rtn',
            'remitter_name',
            'invoice_number',
            'invoice_amount',
            'custom_data',
            'front_image_file_name',
            'rear_image_file_name',
            ]
    def __new__(cls, text):
        args = text.split('|')
        if len(args) == 21 and args[20]:
            raise TypeError('invalid format in line:  %r' % text)
        if len(args) == 21:
            args.pop()
        if args[0] != 'A':                  # action Add, Change, Delete (first letter only)
            raise TypeError('invalid action: %r' % args[0])
        ser_num = args[10]
        ser_num.lstrip('0')
        ser_num = '0' * (6 - len(ser_num)) + ser_num
        args[1] = text_to_date(args[1])     # deposit date
        args[5] = Int(args[5])              # batch number
        args[6] = Int(args[6])              # transaction number
        args[8] = Int(args[8])              # sequence number
        args[9] = Int(args[9])              # check amount (in pennies)
        args[10] = ser_num                  # six-char minimum check number
        args[12] = text_to_date(args[12])   # date of check (if given)
        args[16] = Int(args[16])            # invoice amount (in pennies)
        return tuple.__new__(cls, tuple(args))
    def __getattr__(self, name):
        search_name = name.lower()
        rec_type = self[0]
        try:
            index = self.fields.index(search_name)
        except IndexError:
            raise AttributeError(name)
        return self[index]
    def __repr__(self):
        rec_def = self.record_type
        rec_num = self.serial_number or self.invoice_number
        rec_amt = self.check_amount or self.invoice_amount
        if rec_def in ('CHK','INV'):
            result = '<IFT: %s #%s  %s>' % (rec_def, rec_num, rec_amt)
        else:
            front = self.front_image_file_name
            rear = self.rear_image_file_name
            if front and rear:
                result = '<IFT: %s front: %r  rear: %r>' % (rec_def, front, rear)
            elif front:
                result = '<IFT: %s front: %r>' % (rec_def, front, )
            elif rear:
                result = '<IFT: %s rear: %r>' % (rec_def, rear, )
            else:
                result = '<IFT: %s>' % (rec_def, )
        return result


class IFTIterator(object):
    def __init__(self, filename):
        with open(filename) as fn:
            self._data = [l.strip() for l in fn.readlines()]
        self._pointer = 0
        self._length = len(self._data)
    def __iter__(self):
        return self
    def __next__(self):
        '''iterates through the data records'''
        if self._pointer >= self._length:
            raise StopIteration
        current = self._pointer
        self._pointer += 1
        return IFTRecord(self._data[current])
    next = __next__
    def reset(self, offset=None):
        if offset is None:
            self._pointer = 0
        else:
            self._pointer += offset
            if self._pointer > self._length:
                raise ValueError('cannot go bcak that far: index=%d, offset=%d' % (self._pointer, offset))


class IFTBundle(object):
    def __init__(self, filename):
        self._image_iter = IFTIterator(filename)
    def __iter__(self):
        return self
    def __next__(self):
        group = [next(self._image_iter)]
        for rec in self._image_iter:
            if rec.transaction_number != group[0].transaction_number:
                self._image_iter.reset(-1)
                break
            group.append(rec)
        if group:
            return tuple(group)
        raise StopIteration
    next = __next__


class RMFFRecord(tuple):
    __slots__ = ()
    def __new__(cls, text):
        args = text.strip('~').split('|')
        rec_def = cls.fields[args[0]]
        for index, func, help in rec_def.values():
            try:
                args[index] = func(args[index])
            except IndexError:
                args.append(None) 
        return tuple.__new__(cls, tuple(args))
    def __getattr__(self, name):
        search_name = name.lower()
        rec_type = self[0]
        try:
            index = self.fields[rec_type][search_name][0]
        except KeyError:
            raise AttributeError(name)
        return self[index]
    def __repr__(self):
        rec_def = self.fields[self[0]]
        result = []
        for name, (index, func, help) in sorted(rec_def.items(), key=lambda item: item[1][0]):
            result.append('%s=%r' % (name, self[index]))
        return '<RMFFRecord: ' + ', '.join(result) + '>'
    @property
    def id(self):
        return self[0]
    fields = {
            'FH' : {
                    'fhrt'  : (0, str, 'file header'),
                    'fhfn'  : (1, str, 'unique control number'),
                    'fhfd'  : (2, text_to_date, 'file creation date'),
                    'fdft'  : (3, text_to_time, 'file creation time'),
                    },
            'FT' : {
                    'ftrt'  : (0, str, 'file trailer'),
                    'ftpc'  : (1, Int, 'payment count'),
                    'ftpa'  : (2, Int, 'total amount of payments and items in the file (in pennies)'),
                    },
            'BH' : {
                    'bhrt'  : (0, str, 'batch header'),
                    'bhbn'  : (1, Int, 'unique batch number within file'),
                    'bhbd'  : (2, text_to_date, 'batch creation date'),
                    'bhbt'  : (3, text_to_time, 'batch creation time'),
                    },
            'BT' : {
                    'btrt'  : (0, str, 'batch trailer'),
                    'btpc'  : (1, Int, 'number of payments and items in the batch'),
                    'btpa'  : (2, Int, 'total amount of payments and items in the batch (in pennies)'),
                    'btnb'  : (3, str, 'first seven digits of batch number'),
                    },
            'PR' : {
                    'prrt'  : (0, str, 'payment record'),
                    'prpt'  : (1, str, 'payment type'),
                    'prcd'  : (2, str, 'credit/debit'),
                    'prpa'  : (3, Int, 'payment amount (in pennies)'),
                    'prdr'  : (4, str, 'destination routing number'),
                    'prda'  : (5, str, 'account number or lockbox number'),
                    'pror'  : (6, str, 'originator routing number'),
                    'proa'  : (7, str, 'originator account number'),
                    'pred'  : (8, text_to_date, 'effective date'),
                    'pro1'  : (9, str, 'originator to benifiary 1'),
                    'pro2'  : (10, str, 'originator to benificiary 2'),
                    'pro3'  : (11, str, 'originator to benificiary 3'),
                    'pro4'  : (12, str, 'originator to benificiary 4'),
                    'pra1'  : (13, str, 'beneficiary advice info 1'),
                    'pra2'  : (14, str, 'beneficiary advice info 2'),
                    'pra3'  : (15, str, 'beneficiary advice info 3'),
                    'srin'  : (16, str, "sender's reference number"),
                    },
            'SP' : {
                    'sprt'  : (0, str, 'supplemental payment record'),
                    'spln'  : (1, str, 'lockbox number'),
                    'spcn'  : (2, str, 'reserved'),
                    'spbn'  : (3, Int, 'lockbox batch number'),
                    'spis'  : (4, Int, 'item sequence number'),
                    'spvt'  : (5, str, 'lockbox control number'),
                    'sppd'  : (6, text_to_date, 'postmark date'),
                    'sprz'  : (7, str, 'reserved'),
                    'spes'  : (8, Int, 'envelope sequence number'),
                    'spc1'  : (9, str, 'user-defined field 1'),
                    'spc2'  : (10, str, 'user-defined field 2'),
                    'spc3'  : (11, str, 'user-defined field 3'),
                    'spc4'  : (12, str, 'user-defined field 4'),
                    'spcd'  : (13, text_to_date, 'check date'),
                    'spf1'  : (14, str, 'payment level remitter account'),
                    'spf2'  : (15, str, 'check number'),
                    'spf3'  : (16, str, 'reserved'),
                    'spf4'  : (17, str, 'reserved'),
                    'sppn'  : (18, str, 'bill-pay processing network'),
                    'spsc'  : (19, str, 'EBX SEC code'),
                    'spf5'  : (20, str, 'biller ID'),
                    'spf6'  : (21, str, 'reserved'),
                    'spf7'  : (22, str, 'reserved'),
                    'spf8'  : (23, str, 'effective date'),
                    'spf9'  : (24, str, 'reserved'),
                    'spdl'  : (25, str, 'deposit location number'),
                    'spdi'  : (26, str, 'deposit ID'),
                    'spcr'  : (27, str, 'customer reference number'),
                    'spcs'  : (28, str, 'credit image sequence number'),
                    'spdd'  : (29, str, 'reserved'),
                    'splb'  : (30, str, 'reserved'),
                    'spda'  : (31, str, 'reserved'),
                    'spf10' : (32, str, 'reserved'),
                    'spf11' : (33, str, 'fed reference number'),
                    'spfr'  : (34, str, 'wire ID'),
                    'spse'  : (35, str, 'ACH SEC Code'),
                    'spoi'  : (36, str, "originator's company ID"),
                    'spii'  : (37, str, 'ID assigned by originator to us'),
                    'spdt'  : (38, text_to_date, 'descriptive date (not used for settlement nor posting)'),
                    'sptn'  : (39, str, 'ACH trace number'),
                    'spat'  : (40, str, 'foreign ACH trace number'),
                    'spr1'  : (41, str, 'ACH ref info 1'),
                    'spr2'  : (42, str, 'ACH ref info 2'),
                    'spad'  : (43, str, 'addenda data 1'),
                    'spad1' : (44, str, 'addenda data 2'),
                    'spfxc' : (45, str, 'foreign exchange contract number'),
                    'spitc' : (46, str, 'international type code'),
                    'spasd' : (47, str, 'ACH settlement date'),
                    'spf17' : (48, str, 'reserved'),
                    'spf18' : (49, str, 'reserved'),
                    'spf19' : (50, str, 'reserved'),
                    },
            'PA' : {
                    'part'  : (0, str, 'payment address'),
                    'paec'  : (1, str, 'entity ID code'),
                    'pan1'  : (2, str, 'name 1'),
                    'paan'  : (3, str, 'name 2'),
                    'pasa1' : (4, str, 'address 1'),
                    'pasa2' : (5, str, 'address 2'),
                    'pac1'  : (6, str, 'city'),
                    'pasp'  : (7, str, 'state or province'),
                    'papc'  : (8, str, 'postal code'),
                    'pacc'  : (9, str, 'country code'),
                    'pacn'  : (10, str, 'country name'),
                    'pacy'  : (11, str, 'currency code'),
                    'pabi'  : (12, str, 'bank ID type'),
                    'pa27'  : (13, str, 'Lockbox remitter ZIP code, ACH identifier, wire originating bank ID, or wire sending bank ID'),
                    'pa29'  : (14, str, 'reserved'),
                    'pa31'  : (15, str, 'reserved'),
                    'pa33'  : (16, str, 'reserved'),
                    'pa35'  : (17, str, 'reserved'),
                    'pa37'  : (18, str, "originator's reference number"),
                    'pa39'  : (19, str, 'beneficiary bank info'),
                    'pa41'  : (20, str, 'bank to bank instructions 1'),
                    'pa43'  : (21, str, 'bank to bank instructions 2'),
                    'pa45'  : (22, str, 'bank to bank instructions 1'),
                    'pa47'  : (23, str, 'bank to bank instructions 1'),
                    'pa49'  : (24, str, 'bank to bank instructions 1'),
                    'pa51'  : (25, str, 'bank to bank instructions 1'),
                    'pa53'  : (26, text_to_date, 'wire processing date'),
                    'pa55'  : (27, text_to_time, 'wire processing time'),
                    },
            'IV' : {
                    'ivrt'  : (0, str, 'invoice'),
                    'ivrq'  : (1, str, 'reference ID qualifier'),
                    'ivri'  : (2, str, 'reference ID'),
                    'ivac'  : (3, str, 'payment action code'),
                    'ivpd'  : (4, Int, 'amount paid (in pennies)'),
                    'ivga'  : (5, Int, 'gross invoice amount incl charges less allowances (in pennies)'),
                    'ivda'  : (6, Int, 'discount amount (in pennies)'),
                    'ivar'  : (7, str, 'adjustment reason code'),
                    'ivaa'  : (8, Int, 'adjustment amount (in pennies)'),
                    },
            'SI' : {
                    'sirt'  : (0, str, 'supplemental invoice'),
                    'sisn'  : (1, Int, 'item sequence number'),
                    'sion'  : (2, Int, 'overflow sequence number'),
                    'sioi'  : (3, str, 'overflow indicator (0=yes, 9=no)'),
                    'sira'  : (4, str, 'invoice remitter account'),
                    'sies'  : (5, Int, 'envelope sequence number'),
                    'siia'  : (6, Int, 'invoice amount due (in pennies)'),
                    'sic1'  : (7, str, 'user-defined field 1'),
                    'sic2'  : (8, str, 'user-defined field 2'),
                    'sic3'  : (9, str, 'user-defined field 3'),
                    'sic4'  : (10, str, 'user-defined field 4'),
                    'sic5'  : (11, str, 'user-defined field 5 (in pennies)'),
                    'sic6'  : (12, str, 'user-defined field 6 (in pennies)'),
                    'sic7'  : (13, str, 'user-defined field 7 (in pennies)'),
                    'sic8'  : (14, str, 'user-defined field 8 (in pennies)'),
                    'siid'  : (15, text_to_date, 'invoice date'),
                    'sic9'  : (16, str, 'user-defined field 9'),
                    'sif1'  : (17, str, 'reserved'),
                    'sif2'  : (18, str, 'reserved'),
                    'sif3'  : (19, str, 'reserved'),
                    'sif4'  : (20, str, 'reserved'),
                    'sitn'  : (21, str, 'EBX trace number'),
                    'sirn'  : (22, str, 'routing/transit number'),
                    'sics'  : (23, str, 'capture sequence number'),
                    'sidi'  : (24, str, 'deposit check ID'),
                    'sict'  : (25, str, 'check type (A=converted, I=standard)'),
                    'sirc'  : (26, str, 'reason code'),
                    'sidl'  : (27, str, 'discretionary data code'),
                    'sill'  : (28, str, 'discretionary data label'),
                    'sidd'  : (29, str, 'discretionary data'),
                    'sicn'  : (30, str, 'check number'),
                    'sif5'  : (31, str, 'reserved'),
                    'sior'  : (32, str, 'origination bank info'),
                    'sif6'  : (33, str, 'reserved'),
                    'sif7'  : (34, str, 'reserved'),
                    'sif8'  : (35, str, 'reserved'),
                    'sif9'  : (36, str, 'reserved'),
                    'sif10' : (37, str, 'reserved'),
                    'siri'  : (38, str, 'PO reference'),
                    'side'  : (39, str, 'PO description'),
                    'siir'  : (40, str, 'invoice reference'),
                    'sids'  : (41, str, 'invoice description'),
                    'sivr'  : (42, str, 'voucher reference'),
                    'sivd'  : (43, str, 'voucher description'),
                    'sidt'  : (44, text_to_date, 'invoice date'),
                    'sif11' : (45, str, 'reserved'),
                    'sif12' : (46, str, 'reserved'),
                    'sif13' : (47, str, 'reserved'),
                    'sif14' : (48, str, 'reserved'),
                    'sif15' : (49, str, 'reserved'),
                  },
             }


class RMFlatFileIterator(object):
    def __init__(self, filename):
        self._data = [l.strip() for l in open(filename).readlines()]
        self.header = RMFFRecord(self._data[0])
        self.trailer = RMFFRecord(self._data[-1])
        self._data = self._data[1:-1]
        self._pointer = 0
        self._length = len(self._data)
    def __iter__(self):
        return self
    def __next__(self):
        '''iterates through the data records'''
        if self._pointer >= self._length:
            raise StopIteration
        current = self._pointer
        self._pointer += 1
        return RMFFRecord(self._data[current])
    next = __next__
    def reset():
        self._pointer = 0

class RmPayment(object):
    def __init__(self, fh_rec, bh_rec, pr_rec):
        self.fh = fh_rec
        self.bh = bh_rec
        self.pr = pr_rec
        self.pa = []
        self.sp = ()
        self.ad = ()
        self.al = ()
        self.ri = ()
        self._invoices = OrderedDict()
        self._total_discount = 0
        self._duplicate_invoices = {}
        orig_rtng = pr_rec.pror
        self._orig_rtng = orig_rtng.lstrip('0')
        orig_acct = pr_rec.proa
        self._orig_acct = orig_acct.lstrip('0')
    def __getattr__(self, name):
        search_name = name.lower()
        if search_name[:3] == 'pa_' and name[-2:].upper() in self.pa:
            return getattr(self, name.upper())
        for obj in (self.fh, self.bh, self.pr, self.sp, self.pa, self.ad, self.al, self.ri):
            try:
                return getattr(obj, search_name)
            except AttributeError:
                pass
        if not self._invoices:
            raise AttributeError(name)
        result = []
        for obj in self._invoices.values():
            result.append(getattr(obj, search_name))
        return result
    def __repr__(self):
        return '<RmPayment: payer-> %s  date-> %s  ck_num-> %s  credit-> %s  debit-> %s total_discount-> %s >' % (self.payer, self.date, self.ck_num, self.credit, self.debit, self.total_discount)
    @property
    def batch_control(self):
        return self.bh.bhbn
    @property
    def ck_num(self):
        return self._ck_num
    @property
    def credit(self):
        if self.pr.prcd == 'C':
            return self.pr.prpa
        return 0
    @property
    def date(self):
        return self.pr.pred
    @property
    def debit(self):
        if self.pr.prcd == 'D':
            return self.pr.prpa
        return 0
    @property
    def file_control(self):
        return self.fh.fhfn
    @property
    def invoices(self):
        return self._invoices.copy()
    @property
    def payer(self):
        return self.PA_PR.pan1
    @property
    def orig_acct(self):
        return self._orig_acct
    @property
    def orig_rtng(self):
        return self._orig_rtng
    @property
    def total_discount(self):
        return self._total_discount
    @total_discount.setter
    def total_discount(self, value):
        self._total_discount = value
    def add_record(self, rec):
        if rec.id in ('FH', 'BH', 'AD', 'AL', 'RI'):
            setattr(self, rec.id.lower(), rec)
        elif rec.id == 'SP':
            setattr(self, rec.id.lower(), rec)
            ck_num = rec.spf2.lstrip('0')
            ck_num = '0' * (6 - len(ck_num)) + ck_num
            self._ck_num = ck_num
        elif rec.id == 'PA':
            self.pa.append(rec.paec)
            setattr(self, '%s_%s' % rec[:2], rec)
        else:
            raise ValueError('%r: unknown record type: %r' % (self.__class__.__name__, rec.id))
    def add_invoice(self, inv, replace=False):
        inv_num = inv.inv_num
        if inv_num in self._duplicate_invoices and not replace:
            count = self._duplicate_invoices[inv_num]
            count += 1
            self._duplicate_invoices[inv_num] = count
            dup_num = inv_num + '-dup%d' % count
            inv.duplicate_number(dup_num)
            self._invoices[dup_num] = inv
        elif inv_num in self._invoices and not replace:
            d1 = inv_num + '-dup1'
            d2 = inv_num + '-dup2'
            old_invoice = self._invoices[inv_num]
            del self._invoices[inv_num]
            old_invoice.duplicate_number(d1)
            inv.duplicate_number(d2)
            self._invoices[d1] = old_invoice
            self._invoices[d2] = inv
            self._duplicate_invoices[inv_num] = 2
        else:
            self._invoices[inv_num] = inv
    def remove_invoice(self, inv_num):
        del self._invoices[inv_num]


class RmInvoice(object):
    def __init__(self, iv_rec=None, inv_num=None, amount=None):
        if iv_rec is None and (inv_num is None or amount is None):
            raise TypeError('either iv_rec must be given, or both inv_num and amount must be given')
        self.iv = iv_rec
        if iv_rec is not None:
            self._inv_num = '0' * (6 - len(iv_rec.ivri)) + iv_rec.ivri
            self._amount = iv_rec.ivpd
        else:
            self._inv_num = inv_num
            self._amount = amount
        self.sup_iv = []
        self.ad = ()
        self.al = ()
    def __getattr__(self, name):
        search_name = name.lower()
        for obj in (self.iv, self.ad, self.al):
            try:
                return getattr(obj, search_name)
            except AttributeError:
                pass
        if not self.sup_iv:
            raise AttributeError(name)
        result = []
        for obj in self.sup_iv:
            result.append(getattr(obj, search_name))
        return result
    def __repr__(self):
        return '<RmInvoice: number->%s  amount->%s>' % (self.inv_num, self.amount)
    @property
    def amount(self):
        return self._amount
    @amount.setter
    def amount(self, new_value):
        self._amount = new_value
    @property
    def inv_num(self):
        return self._inv_num
    def add_record(self, rec):
        if rec.id == 'SI':
            self.sup_iv.append(rec)
        elif rec.id in ('AD', 'AL'):
            setattr(self, rec.id.lower(), rec)
        else:
            raise ValueError("%r: unknown record type: %r" % (self.__class__.__name__, rec.id))
    def duplicate_number(self, new_number):
        self._inv_num = new_number

def lockbox_payments(filename):
    """Return payments from filename"""

    in_lockbox = False
    result = []
    batch_header = None
    batch_footer = None
    rmgr = RMFlatFileIterator(filename)
    for rec in rmgr:
        if rec.id == 'BH':
            batch_header = rec
        elif rec.id == 'BT':
            batch_footer = rec
            in_lockbox = False
        if not in_lockbox:
            if rec.id != 'PR' or rec.prpt != 'LBX':
                continue
            in_lockbox = True
            payment = RmPayment(rmgr.header, batch_header, rec)
            result.append(payment)
        elif rec.id == 'PR':
            payment = RmPayment(rmgr.header, batch_header, rec)
            result.append(payment)
        if rec.id in ('PA', 'SP'):
            payment.add_record(rec)
        elif rec.id == 'IV':
            new_invoice = RmInvoice(rec)
            payment.add_invoice(new_invoice)
        elif rec.id == 'SI':
            new_invoice.add_record(rec)
    return result


# ACHStore keeps track of which ACH files have been transmitted, and the name of the next ACH file
# ACHPayment stores one payment from TRU to a vendor
# ACHFile takes the payments and makes a WFB achfile for transmission

class ACHStore(object):
    "remembers previous ACHFiles, generates new file names"

    def __init__(self, filename):
        self.store = Table(filename)
        with self.store:
            self.index = self.store.create_index(lambda rec: (rec.filedate, rec.filemod))

    def get_achfile(self, company_name, company_id, file_id):
        today = Date.today()
        with self.index:
            mod = 'A'
            if self.store:
                rec = self.store[-1]
                if rec.filedate == today:
                    mod = chr(ord(rec.filemod) +1)
                    if mod > 'Z':
                        raise ValueError('already generated 26 files today, wait until tomorrow')
            self.store.append(dict(filedate=today, filemod=mod))
        filename = 'ACH_%s_%s' % (today.ymd(), mod)
        return ACHFile(company_name, company_id, file_id, filename, mod)


class ACHFile(object):
    """Accepts multiple ACH payments and generates file for tranmission to WFB."""

    origin_rtng = 91000019
    origin_id = 9100001
    origin_bank = 'WELLS FARGO'

    file_header = '101 %(origin_rtng)09d%(file_id)s%(date)s%(time)s%(id_mod)s094101%(origin_bank)-23s%(company)-23s        '
    batch_header = '5200%(company)-16s%(discretionary)-20s%(company_id)s%(sec)s%(description)-10s%(ref_date)-6s%(eff_date)s   1%(origin_id)08d%(batch_number)07d'
    entry_detail = '6%(code)d%(routing_nbr)s%(account)-17s%(amount)010d%(payee_id)-15s%(payee_name)-22s  %(addenda)d%(origin_id)08d%(entry_number)07d'
    batch_control = '8200%(entries)06d%(entry_hash)010d%(debit)012d%(credit)012d%(company_id)s                         %(origin_id)08d%(batch_number)07d'
    file_control = '9%(batches)06d%(blocks)06d%(entries)08d%(entry_hash)010d%(debit)012d%(credit)012d                                       '

    def __init__(self, company_name, company_id, file_id, filename, modifier):
        if len(company_id) > 10 or len(file_id) > 10:
            raise ValueError('company_id and file_id cannot be longer than 10 characters (%r, %r)' % (company_id, file_id))
        self.today = Date.today()
        self.time = Time.now()
        self.company_name = company_name.upper()
        self.company_id = company_id.upper().zfill(10)
        self.file_id = file_id.upper().zfill(10)
        self.filename = Path(filename)
        self.modifier = modifier.upper()
        self.payments = []
        self.lines = [
                self.file_header % dict(
                    origin_rtng=self.origin_rtng,
                    origin_bank=self.origin_bank,
                    file_id=file_id,
                    date=self.today.strftime('%y%m%d'), time=self.time.strftime('%H%M'),
                    id_mod=modifier, company=self.company_name[:23],
                    )]
        self.open = True

    def __repr__(self):
        return "<%s(%r, %r)>" % (self.__class__.__name__, self.filename, self.modifier)

    def add_payment(self, payment):
        if not self.open:
            raise ValueError("%r is closed" % self)
        self.payments.append(payment)

    def save_at(self, path):
        """
        Create the file, write the entries, close the file.
        """
        path = Path(path)
        ref_date = self.today.strftime('%b %d').upper()
        lines = self.lines
        batches = 0
        total_blocks = 0
        total_entries = 0
        total_hash = 0
        total_debit = 0
        total_credit = 0
        eff_date = FederalHoliday.next_business_day(self.today, days=2).strftime('%y%m%d')

        def pdscd(rec):
            return rec.sec_code, rec.description

        payments = sorted(self.payments, key=pdscd)
        
        for (sec_code, description), group in groupby(payments, pdscd):
            batch_entries = 0
            batch_hash = 0
            batch_debit = 0
            batch_credit = 0
            batches += 1
            if batches > 10**7:
                raise ValueError("too many batches for this file, need to split")
            lines.append(self.batch_header % dict(
                    origin_id=self.origin_id,
                    company=self.company_name[:16],
                    company_id=self.company_id,
                    discretionary='',
                    description=description[:10],
                    ref_date=ref_date,
                    eff_date=eff_date,
                    batch_number=batches,
                    sec=sec_code
                    ))
            for pymnt in group:
                total_entries += 1
                batch_entries += 1
                batch_hash += int(pymnt.vendor_rtng) // 10
                if total_entries > 10**8:
                    raise ValueError("Too many entries for file, need to split")
                if batch_entries > 10**6:
                    raise ValueError("Too many entries for batch %d, need to split" % batches)
                trans_code = pymnt.transaction_code
                if trans_code in (ACH_ETC.ck_credit, ACH_ETC.ck_prenote_credit, ACH_ETC.sv_credit, ACH_ETC.sv_prenote_credit):
                    total_credit += pymnt.amount
                    batch_credit += pymnt.amount
                    if total_credit > 10**12:
                        raise ValueError("total credit amount for file too large, need to split")
                    if batch_credit > 10**12:
                        raise ValueError("total credit amount for batch %d too large, need to split" % batches)
                elif trans_code in (ACH_ETC.ck_debit, ACH_ETC.ck_prenote_debit, ACH_ETC.sv_debit, ACH_ETC.sv_prenote_debit):
                    total_debit += pymnt.amount
                    batch_debit += pymnt.amount
                    if total_debit > 10**12:
                        raise ValueError("total debit amount for file too large, need to split")
                    if batch_debit > 10**12:
                        raise ValueError("total debit amount for batch %d too large, need to split" % batches)
                else:
                    raise ValueError("Unknown transaction code (%s) for payment %s" % (trans_code, pymnt))
                lines.append(self.entry_detail % dict(
                        origin_id=self.origin_id,
                        code=trans_code,
                        routing_nbr=pymnt.vendor_rtng,
                        account=pymnt.vendor_acct[-17:],
                        amount=pymnt.amount,
                        payee_id=pymnt.vendor_inv_num[:15],
                        payee_name=pymnt.vendor_name[:22],
                        addenda=0,
                        entry_number=batch_entries,
                        ))
            total_hash += batch_hash
            lines.append(self.batch_control % dict(
                    origin_id=self.origin_id,
                    company_id=self.company_id,
                    sec=sec_code,
                    entries=batch_entries,
                    entry_hash=batch_hash%10**10,
                    debit=batch_debit,
                    credit=batch_credit,
                    batch_number=batches,
                    ))
        lines.append(self.file_control % dict(
                batches=batches,
                blocks=(len(lines)+10)//10,
                entries=total_entries,
                entry_hash=total_hash%10**10,
                debit=total_debit,
                credit=total_credit,
                ))
        with open(path/self.filename, 'w') as ach_file:
            ach_file.write('\n'.join(lines) + '\n')

class Customer(AutoEnum):
    domestic = "Customer, and customer's bank, are located in the US"
    foreign = "Customer, and/or customer's bank, are located outside the US"

class ACH_ETC(IntEnum):
    """
    Entry Transaction Codes
    """
    ck_credit = 22
    ck_prenote_credit = 23
    ck_debit = 27
    ck_prenote_debit = 28
    sv_credit = 32
    sv_prenote_credit = 33
    sv_debit = 37
    sv_prenote_debit = 38

class FederalHoliday(AutoEnum):
    __order__ = 'NewYear MartinLutherKingJr President Memorial Independence Labor Columbus Veterans Thanksgiving Christmas'
    NewYear = "First day of the year.", 'absolute', Month.JANUARY, 1
    MartinLutherKingJr = "Birth of Civil Rights leader.", 'relative', Month.JANUARY, Weekday.MONDAY, 3
    President = "Birth of George Washington", 'relative', Month.FEBRUARY, Weekday.MONDAY, 3
    Memorial = "Memory of fallen soldiers", 'relative', Month.MAY, Weekday.MONDAY, 5
    Independence = "Declaration of Independence", 'absolute', Month.JULY, 4
    Labor = "American Labor Movement", 'relative', Month.SEPTEMBER, Weekday.MONDAY, 1
    Columbus = "Americas discovered", 'relative', Month.OCTOBER, Weekday.MONDAY, 2
    Veterans = "Recognition of Armed Forces service", 'relative', Month.NOVEMBER, 11, 1
    Thanksgiving = "Day of Thanks", 'relative', Month.NOVEMBER, Weekday.THURSDAY, 4
    Christmas = "Birth of Jesus Christ", 'absolute', Month.DECEMBER, 25

    def __init__(self, doc, type, month, day, occurance=None):
        self.__doc__ = doc
        self.type = type
        self.month = month
        self.day = day
        self.occurance = occurance

    def date(self, year):
        "returns the observed date of the holiday for `year`"
        if self.type == 'absolute' or isinstance(self.day, int):
            holiday =  Date(year, self.month, self.day)
            if Weekday(holiday.isoweekday()) is Weekday.SUNDAY:
                holiday = holiday.replace(delta_day=1)
            return holiday
        days_in_month = days_per_month(year)
        target_end = self.occurance * 7 + 1
        if target_end > days_in_month[self.month]:
            target_end = days_in_month[self.month]
        target_start = target_end - 7
        target_week = list(xrange(start=Date(year, self.month, target_start), step=one_day, count=7))
        for holiday in target_week:
            if Weekday(holiday.isoweekday()) is self.day:
                return holiday

    @classmethod
    def next_business_day(cls, date, days=1):
        """
        Return the next `days` business day from date.
        """
        holidays = cls.year(date.year)
        years = set([date.year])
        while days > 0:
            date = date.replace(delta_day=1)
            if date.year not in years:
                holidays.extend(cls.year(date.year))
                years.add(date.year)
            if Weekday(date.isoweekday()) in (Weekday.SATURDAY, Weekday.SUNDAY) or date in holidays:
                continue
            days -= 1
        return date

    @classmethod
    def year(cls, year):
        """
        Return a list of the actual FederalHoliday dates for `year`.
        """
        holidays = []
        for fh in cls:
            holidays.append(fh.date(year))
        return holidays
