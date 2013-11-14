from VSS.BBxXlate.bbxfile import BBxFile
from VSS.utils import one_day, text_to_date
from VSS import AutoEnum

GL_ACCT_REC = '1100-00'
GL_CASH = '1000-15'
GL_DISCOUNTS = '4100-00'
DUMMY_CUSTOMER_ID = '001001'
DUMMY_GL_ACCT = '1100-00'
DISCOUNT_CUTOFF = 15

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
        self.end_discount_date = rec.trans_date.replace(delta_month=1, day=DISCOUNT_CUTOFF)
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

class Inv(object):
    def __init__(self, inv_num, amount, quality, discount, ar_inv):
        self.inv_num = self.actual_inv_num = inv_num
        self.amount = amount
        self.quality = quality
        self.discount = discount
        self.ar_inv = ar_inv
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.inv_num == other.inv_num
    def __ne__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.inv_num != other.inv_num
    def __repr__(self):
        return 'Inv# %s: %10d (%d)' % (self.inv_num, self.amount, self.discount)

class FakeInv(ARInvoice):
    """
    Used when a match could not be found.
    """
    def __init__(self, cust_num, cust_name, inv_num, amount, trans_date, desc, gl_acct):
        self._inv_num = self._actual_inv_num = inv_num
        self._cust_num = cust_num
        self._cust_name = cust_name
        self._date = trans_date
        self.end_discount_date = trans_date.replace(delta_month=1, day=DISCOUNT_CUTOFF)
        self._starred = False
        self._transactions = []
        self._amount = amount
        self._balance = amount
        self._desc = desc
        self._gl_acct = gl_acct
    def __repr__(self):
        return ('<FakeInv: cust_id=%r, name=%r, date=%r, inv_num=%r, balance=%r>'
                % (self.cust_id, self.name, self.date, self.inv_num, self.balance))
    @property
    def desc(self):
        return self._desc
    @property
    def transactions(self):
        return list()


class Batch(object):
    """
    A collection af `Inv`s that must balance to the creation amount.

    """

    def __init__(self, number, amount, date):
        self.ck_nbr = number
        self.ck_amt = amount
        self.ck_date = date
        self.transactions = []
        self.discount_allowed = None

    def __contains__(self, inv):
        "inv should be either an AR_Invoice or an invoice number; compares against actual_inv_num"
        if not inv:
            return False
        if isinstance(inv, ARInvoice):
            inv = inv.actual_inv_num
        return inv in [inv.actual_inv_num for inv in self.transactions]

    def __repr__(self):
        return "Batch:  check %r for %r on %r, %d transactions" % (self.ck_nbr, self.ck_amt, self.ck_date, len(self.transactions))

    def __str__(self):
        result = ["Batch:  check %r on %r" % (self.ck_nbr, self.ck_date)]
        result.append('')
        result.append("payment: %r" % self.ck_amt)
        result.append('')
        calc = 0
        for tran in self.transactions:
            calc += tran.amount
            result.append("transaction: %r" % tran)
        if not self.transactions:
            result.append("transaction: None")
        result.append('=======================================')
        result.append('                          %10d' % calc)
        return '\n'.join(result)

    def __len__(self):
        return len(self.transactions)

    @property
    def balance(self):
        "amount of check - amount owed on all invoices (negative when discounts are taken)"
        return self.ck_amt - self.total_paid

    @property
    def is_balanced(self):
        return self.balance == 0 

    @property
    def total_owed(self):
        total = 0
        for inv in self.transactions:
            total += inv.ar_inv.balance or inv.ar_inv.amount
        return total

    @property
    def total_paid(self):
        total = 0
        for inv in self.transactions:
            total += inv.amount
        return total

    def add_invoice(self, ar_inv, amount, quality, discount=0, replace=False):
        self.discount_allowed = max(
                self.discount_allowed,
                self.ck_date <= ar_inv.end_discount_date,
                )
        inv_num = ar_inv.actual_inv_num
        if inv_num in self and inv_num != self.ck_nbr:
            if not replace:
                raise ValueError("%s already in batch %r" % (inv_num, self.ck_nbr))
            for invoice in self.transactions:
                if invoice.inv_num == inv_num:
                    invoice.amount = amount
                    invoice.quality = quality
                    break
            else:
                raise AssertionError('Invoice #%s passed _contains__, failed loop (batch %r)' % (inv_num, self.ck_nbr))
        else:
            self.transactions.append(Inv(inv_num, amount, quality, discount, ar_inv))

    def balance_batch(self, amount=None):
        if not self.transactions:
            raise ValueError('cannot balance a batch %r -- it has no invoices' % self.ck_nbr)
        adjustment = self.ck_amt - self.total_paid
        if self.is_balanced and amount in (0, None):
            return
        if amount is None:
            # allow positive amounts equal to 1 penny per invoice
            if adjustment > len(self):
                raise ValueError("unable to balance batch %r" % self.ck_nbr)
            amount = sum([inv.discount for inv in self.transactions]) or adjustment
        if adjustment != amount:
            raise ValueError('amount %s will not put batch %r in balance' % (amount, self.ck_nbr))
        if abs(adjustment) <= len(self):
            # write off pennies
            desc = 'transcription error'
            gl_acct = GL_DISCOUNTS
        elif adjustment < 0:
            discount = 100 - int((float(self.total_owed) / self.total_paid) * 100)
            if self.discount_allowed and discount >= 98:
                desc = '%d%% DISCOUNT TAKEN' % discount
                gl_acct = GL_DISCOUNTS
            else:
                recorded = False
                for invoice in self.transactions:
                    # if discounts have been recorded, undo it
                    if invoice.discount:
                        recorded = True
                        amount = invoice.discount
                        if amount < adjustment:
                            amount = adjustment
                        invoice.amount += amount
                        adjustment -= amount
                if not recorded:
                    discount = 1 - (float(self.ck_amt) / self.total_paid)
                    if discount < 0.01005:
                        discount = -0.01005
                    elif discount < 0.02005:
                        discount = -0.02005
                    else:
                        discount = -discount
                    for invoice in self.transactions:
                        amount = int(invoice.amount * discount)
                        if amount < adjustment:
                            amount = adjustment
                        invoice.amount += amount
                        adjustment -= amount
                return
        else:
            desc = 'SERVICE CHARGE PAID'
            gl_acct = GL_ACCT_REC
        inv_num = self.ck_nbr
        template = self.transactions[0].ar_inv
        invoice = FakeInv(
                template.cust_id,
                template.name,
                inv_num,
                adjustment,
                template.date,
                desc,
                gl_acct
                )
        self.add_invoice(invoice, adjustment, excellent)


class Status(AutoEnum):
    __order__ = 'bad review okay good excellent'
    excellent = ()
    good = ()
    okay = ()
    review = ()
    bad = ()
globals().update(Status.__members__)

