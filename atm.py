from models.account import Account
from exceptions import ATMCashError, CardNotFoundError, InvalidAmountError
from storage import Storage


class ATM:
    def __init__(self, cash_balance: float, bank):
        self.cash_balance = cash_balance
        self.bank = bank

    def withdraw(self, account: Account, amount: float) -> None:
        if amount <= 0:
            raise InvalidAmountError("Сумма должна быть больше нуля")
        if amount > self.cash_balance:
            raise ATMCashError(
                f"В банкомате недостаточно наличных. Доступно: {self.cash_balance:.2f} ₽"
            )
        account.withdraw(amount, "Снятие наличных")
        self.cash_balance -= amount
        self.bank.save()
        Storage.save_atm(self.cash_balance)

    def deposit(self, account: Account, amount: float) -> None:
        if amount <= 0:
            raise InvalidAmountError("Сумма должна быть больше нуля")
        account.deposit(amount, "Внесение наличных")
        self.cash_balance += amount
        self.bank.save()
        Storage.save_atm(self.cash_balance)

    def transfer(self, from_account: Account, to_card_number: str, amount: float) -> None:
        if amount <= 0:
            raise InvalidAmountError("Сумма должна быть больше нуля")
        to_card = self.bank.find_card(to_card_number)
        if to_card is None:
            raise CardNotFoundError(f"Карта {to_card_number} не найдена")
        to_account = self.bank.find_account(to_card.account_id)
        if to_account is None:
            raise CardNotFoundError(f"Счёт карты {to_card_number} не найден")
        from_account.withdraw(amount, f"Перевод на карту {to_card_number}")
        to_account.deposit(amount, f"Перевод с карты {from_account.account_id[:8]}")
        self.bank.save()

    def replenish_cash(self, amount: float) -> None:
        if amount <= 0:
            raise InvalidAmountError("Сумма должна быть больше нуля")
        self.cash_balance += amount
        Storage.save_atm(self.cash_balance)
