from datetime import datetime

from exceptions import InvalidAmountError

ALLOWED_TYPES = {"deposit", "withdraw", "transfer"}


class Transaction:
    def __init__(self, type: str, amount: float, description: str = ""):
        if type not in ALLOWED_TYPES:
            raise ValueError(f"Недопустимый тип транзакции: {type!r}")
        if amount <= 0:
            raise InvalidAmountError("Сумма транзакции должна быть больше нуля")
        self.type = type
        self.amount = amount
        self.timestamp = datetime.now().isoformat()
        self.description = description

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        t = cls(data["type"], data["amount"], data.get("description", ""))
        t.timestamp = data["timestamp"]
        return t
