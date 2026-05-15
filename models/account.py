from models.transaction import Transaction
from exceptions import InsufficientFundsError, InvalidAmountError


class Account:
    def __init__(self, account_id: str, owner: str, balance: float = 0.0):
        self.account_id = account_id
        self.owner = owner
        self.balance = balance
        self.transactions: list[Transaction] = []

    def deposit(self, amount: float, description: str = "Пополнение") -> None:
        if amount <= 0:
            raise InvalidAmountError("Сумма должна быть больше нуля")
        self.balance += amount
        self.transactions.append(Transaction("deposit", amount, description))

    def withdraw(self, amount: float, description: str = "Снятие") -> None:
        if amount <= 0:
            raise InvalidAmountError("Сумма должна быть больше нуля")
        if amount > self.balance:
            raise InsufficientFundsError(
                f"Недостаточно средств. Баланс: {self.balance:.2f} ₽"
            )
        self.balance -= amount
        self.transactions.append(Transaction("withdraw", amount, description))

    def get_history(self) -> list[Transaction]:
        return list(self.transactions)

    def to_dict(self) -> dict:
        return {
            "account_id": self.account_id,
            "owner": self.owner,
            "balance": self.balance,
            "transactions": [t.to_dict() for t in self.transactions],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Account":
        acc = cls(data["account_id"], data["owner"], data["balance"])
        acc.transactions = [
            Transaction.from_dict(t) for t in data.get("transactions", [])
        ]
        return acc
