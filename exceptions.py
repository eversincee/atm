class ATMError(Exception):
    pass


class InsufficientFundsError(ATMError):
    pass


class ATMCashError(ATMError):
    pass


class CardBlockedError(ATMError):
    pass


class CardNotFoundError(ATMError):
    pass


class InvalidAmountError(ATMError):
    pass
