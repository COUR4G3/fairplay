import decimal


def decimal_compare(amount, other, prec=2):
    if not isinstance(amount, decimal.Decimal):
        amount = decimal.Decimal(amount)
    if not isinstance(other, decimal.Decimal):
        other = decimal.Decimal(other)

    with decimal.localcontext() as ctx:
        ctx.prec = prec
        return amount.normalize().compare(other.normalize())
