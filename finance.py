from .utils import translator

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



