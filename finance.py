from __future__ import with_statement

from itertools import groupby
from VSS.path import Path
from VSS.time_machine import PropertyDict
from VSS.utils import translator, one_day, xrange, AutoEnum, IntEnum, Month, Weekday, Table, Date, Time, days_per_month

# ACHStore keeps track of which ACH files have been transmitted, and the name of the next ACH file
# ACHPayment stores one payment from TRU to a vendor
# ACHFile takes the payments and makes a WFB achfile for transmission


class ACHError(Exception):
    "generic ACH error"


class ACHStore(object):
    "remembers previous ACHFiles, generates new file names"

    def __init__(self, table_name):
        self.store = Table(table_name)
        with self.store:
            self.index = self.store.create_index(lambda rec: (rec.filedate, rec.filemod))

    def get_file_and_mod(self):
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
        return filename, mod


class ACHFile(object):
    """Accepts multiple ACH payments and generates file for tranmission to WFB."""

    file_header = '101 %(immed_dest_rtng)09d%(immed_origin)s%(date)s%(time)s%(id_mod)s094101%(immed_dest_name)-23s%(company)-23s        '
    batch_header = '5200%(company)-16s%(discretionary)-20s%(company_id)s%(sec)s%(description)-10s%(ref_date)-6s%(eff_date)s   1%(origin_dfi)08d%(batch_number)07d'
    entry_detail = '6%(code)d%(routing_nbr)s%(account)-17s%(amount)010d%(payee_id)-15s%(payee_name)-22s  %(addenda)d%(origin_dfi)08d%(entry_number)07d'
    batch_control = '8200%(entries)06d%(entry_hash)010d%(debit)012d%(credit)012d%(company_id)s                         %(origin_dfi)08d%(batch_number)07d'
    file_control = '9%(batches)06d%(blocks)06d%(entries)08d%(entry_hash)010d%(debit)012d%(credit)012d                                       '


    def __init__(self, oe_server, ach_store, ach_account=None):
        if ach_account is not None:
            raise ValueError('specifying an ach_account is not implemented')
        self.oe_server = oe_server
        self._get_bank_ach_info()
        fn, mod = ach_store.get_file_and_mod()
        self.filename = Path(fn)
        self.modifier = mod
        self.today = Date.today()
        self.time = Time.now()
        self.payments = []
        self.lines = [
                self.file_header % dict(
                    immed_dest_rtng=self.immed_dest,
                    immed_dest_name=self.immed_dest_name,
                    immed_origin=self.immed_origin,
                    date=self.today.strftime('%y%m%d'), time=self.time.strftime('%H%M'),
                    id_mod=mod, company=self.immed_origin_name[:23],
                    )]
        self.open = True

    def __repr__(self):
        return "<%s(%r, %r)>" % (self.__class__.__name__, self.filename, self.modifier)

    def add_payment(self, payment):
        if not self.open:
            raise ValueError("%r is closed" % self)
        self.payments.append(payment)

    def _get_bank_ach_info(self):
        "gets bank data from OpenERP"
        res_partner_bank = self.oe_server.get_model('res.partner.bank')
        try:
            ach_account = PropertyDict(res_partner_bank.search_read(
                    fields=['ach_bank_name', 'ach_bank_number', 'ach_bank_id', 'ach_company_name', 'ach_company_number', 'ach_company_name_short', 'ach_company_id'],
                    domain=[('ach_default','=',True)],
                    )[0])
        except IndexError:
            raise ACHError('Default ACH account not set up.')
        self.immed_dest_name = ach_account.ach_bank_name
        self.immed_dest = int(ach_account.ach_bank_number)
        self.origin_dfi = int(ach_account.ach_bank_id)
        self.immed_origin_name = ach_account.ach_company_name
        self.immed_origin = ach_account.ach_company_number
        self.company_name = ach_account.ach_company_name_short
        self.company_id = ach_account.ach_company_id
            
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
                    origin_dfi=self.origin_dfi,
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
                        origin_dfi=self.origin_dfi,
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
                    origin_dfi=self.origin_dfi,
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


class ACHPayment(object):
    """A single payment from company to a vendor."""

    _strip = staticmethod(translator(delete=' -'))

    def __init__(self,
            description, sec_code, 
            vendor_name, vendor_inv_num, vendor_rtng, vendor_acct,
            transaction_code, vendor_acct_type, amount):
        """
        description:  10 chars
        sec_code: CCD or CTX
        vendor_name: 22 chars
        vendor_inv_num: 15 chars
        vendor_rtng: 9 chars
        vendor_acct: 17 chars
        transaction_code: ACH_ETC code
        vendor_acct_type: 'domestic' or 'foreign'
        amount: 10 digits (pennies)
        """
        self.description = description.upper()
        self.sec_code = sec_code.upper()
        self.vendor_name = vendor_name.upper()
        self.vendor_inv_num = str(vendor_inv_num).upper()
        self.vendor_rtng = self._strip(vendor_rtng)
        self.vendor_acct = self._strip(vendor_acct)
        self.transaction_code = transaction_code
        self.vendor_acct_type = vendor_acct_type
        self.amount = amount
        self.validate_routing(self.vendor_rtng)

    def __repr__(self):
        return 'ACHPayment(%s)' % (', '.join([
            repr(v) for v in (
                self.description, self.sec_code, self.vendor_name, self.vendor_inv_num, self.vendor_rtng, self.vendor_acct,
                self.transaction_code, self.vendor_acct_type, self.amount,
                )]))

    @staticmethod
    def validate_routing(rtng):
        total = 0
        for digit, weight in zip(rtng, (3, 7, 1, 3, 7, 1, 3, 7)):
            total += int(digit) * weight
        chk_digit = (10 - total % 10) % 10
        if chk_digit != int(rtng[-1]):
            raise ValueError('Routing number %s fails check digit calculation' % rtng)


class Customer(AutoEnum):
    domestic = "Customer, and customer's bank, are located in the US"
    foreign = "Customer, and/or customer's bank, are located outside the US"


class PaymentType(AutoEnum):
    POSITIVE_PAY = 'Written checks submitted positive verification'
    ACH = 'Electronic checks submitted for disbursement'

