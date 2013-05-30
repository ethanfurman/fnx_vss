import datetime
#from fenx.BBxXlate.bbxfile import BBxFile
from VSS.BBxXlate.bbxfile import BBxFile
from VSS.utils import one_day, text_to_date

#ARAgingLine = NamedTuple('ARAgingLine', 'cust_num cust_name trans_date desc trans_type inv_num gl_acct debit credit')

class ARAgingLine(tuple):
    __slots__ = ()
    def __new__(cls, text):
        data = [f.strip('* ') for f in text.split('\t')]
        data[2] = text_to_date(data[2], 'mdy')
        data[7] = int(data[7])
        data[8] = int(data[8])
        return tuple.__new__(cls, tuple(data))
    @property
    def cust_num(self):
        return self[0]
    @property
    def cust_name(self):
        return self[1]
    @property
    def trans_date(self):
        return self[2]
    @property
    def desc(self):
        return self[3]
    @property
    def trans_type(self):
        return self[4]
    @property
    def inv_num(self):
        return self[5]
    @property
    def gl_acct(self):
        return self[6]
    @property
    def debit(self):
        return self[7]
    @property
    def credit(self):
        return self[8]

class ARAgingIter(object):
    """Iterates over AR Aging files"""
    def __init__(self, filename):
        self.data = [l.strip() for l in open(filename).readlines()]
        self.data.pop(0)
        for i, line in enumerate(self.data):
            self.data[i] = ARAgingLine(line)
    def __iter__(self):
        return iter(self.data)

class ARInvoice(object):
    def __init__(self, rec):
        self._inv_num = rec.inv_num
        self._cust_num = rec.cust_num
        self._cust_name = rec.cust_name
        self._gl_acct = rec.gl_acct
        self._transactions = [rec]
        self._balance = 0
    def add_transaction(self, trans):
        self._transactions.append(trans)
        self._balance += trans.debit - trans.credit
        if self._gl_acct != trans.gl_acct:
            self._gl_acct = None
    @property
    def balance(self):
        return self._balance
    @property
    def cust_id(self):
        return self._cust_num
    @property
    def gl_acct(self):
        return self._gl_acct
    @property
    def name(self):
        return self._cust_name
    @property
    def inv_num(self):
        return self._inv_num
    @property
    def transactions(self):
        return self._transactions[:]




def ar_open_invoices(filename):
    '''returns invoices with outstanding balances'''
    temp = {}
    for rec in ARAgingIter(filename):
        if rec.inv_num in temp:
            invoice = temp[rec.inv_num]
            invoice.add_transaction(rec)
        else:
            invoice = ARInvoice(rec)
            temp[rec.inv_num] = invoice
    result = {}
    for num, inv in temp.items():
        if inv.balance > 0:
            result[num] = inv
    return result
        
