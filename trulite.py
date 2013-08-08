from VSS.BBxXlate.bbxfile import BBxFile
from VSS.utils import one_day, text_to_date

#ARAgingLine = NamedTuple('ARAgingLine', 'cust_num cust_name trans_date desc trans_type inv_num gl_acct debit credit')

class ARAgingLine(tuple):
    __slots__ = ()
    def __new__(cls, text):
        data = [f.strip() for f in text.split('\t')]
        data[2] = text_to_date(data[2], 'mdy')
        data[7] = int(data[7])
        data[8] = int(data[8])
        data.append(data[1].startswith('**'))
        data[1] = data[1].strip('*')
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
    @property
    def starred(self):
        return self[9]

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
        self._inv_num = self._actual_inv_num = rec.inv_num
        self._cust_num = rec.cust_num
        self._cust_name = rec.cust_name
        self._gl_acct = rec.gl_acct
        self._date = rec.trans_date
        self.end_discount_date = rec.trans_date.replace(delta_month=1, day=15)
        self._starred = rec.starred
        self._transactions = []
        if '1-INVCE' in rec.trans_type:
            self._amount = rec.debit - rec.credit
        else:
            self._amount = 0
        self._balance = 0
        self.add_transaction(rec)
    def __repr__(self):
        return ('<ARInvoice: cust_id->%s  name->%s  date->%s  inv_num->%s  balance->%s>'
                % (self.cust_id, self.name, self.date, self.inv_num, self.balance))
    def add_transaction(self, trans):
        self._transactions.append(trans)
        self._balance += trans.debit - trans.credit
        if self._gl_acct != trans.gl_acct:
            self._gl_acct = None
    @property
    def actual_inv_num(self):
        return self._actual_inv_num
    @property
    def amount(self):
        return self._amount
    @property
    def balance(self):
        return self._balance
    @property
    def cust_id(self):
        return self._cust_num
    @property
    def date(self):
        return self._date
    @property
    def desc(self):
        return '; '.join([trans.desc for trans in self.transactions])
    @property
    def gl_acct(self):
        return self._gl_acct
    @property
    def inv_num(self):
        return self._inv_num
    @property
    def name(self):
        return self._cust_name
    @property
    def order_num(self):
        num, desc = self.transactions[0].desc.split(':', 1)
        if num and desc not in ('SERVICE CHARGE','APPLY','REAPPLY'):
            return num
        return ''
    @property
    def starred(self):
        return self._starred
    @property
    def transactions(self):
        return self._transactions[:]
    def shadow_inv_num(self, value):
        self._inv_num = value


def ar_invoices(filename):
    '''returns all invoices'''
    result = {}
    for rec in ARAgingIter(filename):
        if rec.inv_num in result:
            result[rec.inv_num].add_transaction(rec)
        else:
            invoice = ARInvoice(rec)
            result[rec.inv_num] = invoice
    return result


def ar_open_invoices(filename):
    '''returns invoices with outstanding balances'''
    temp = ar_invoices(filename)
    result = {}
    for num, inv in temp.items():
        if inv.balance != 0:
            result[num] = inv
    return result

        
