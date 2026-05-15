import hashlib

from exceptions import CardBlockedError

MAX_PIN_ATTEMPTS = 3


class Card:
    def __init__(
        self,
        card_number: str,
        pin_hash: str,
        account_id: str,
        is_blocked: bool = False,
        pin_attempts: int = 0,
    ):
        self.card_number = card_number
        self.pin_hash = pin_hash
        self.account_id = account_id
        self.is_blocked = is_blocked
        self.pin_attempts = pin_attempts

    @staticmethod
    def hash_pin(pin: str) -> str:
        return hashlib.sha256(pin.encode()).hexdigest()

    def verify_pin(self, pin: str) -> bool:
        if self.is_blocked:
            raise CardBlockedError("Карта заблокирована. Обратитесь к администратору.")
        if self.pin_hash == Card.hash_pin(pin):
            self.pin_attempts = 0
            return True
        self.pin_attempts += 1
        if self.pin_attempts >= MAX_PIN_ATTEMPTS:
            self.is_blocked = True
            raise CardBlockedError(
                "Карта заблокирована после 3 неверных попыток ввода PIN."
            )
        return False

    def unblock(self) -> None:
        self.is_blocked = False
        self.pin_attempts = 0

    def to_dict(self) -> dict:
        return {
            "card_number": self.card_number,
            "pin_hash": self.pin_hash,
            "account_id": self.account_id,
            "is_blocked": self.is_blocked,
            "pin_attempts": self.pin_attempts,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Card":
        return cls(
            data["card_number"],
            data["pin_hash"],
            data["account_id"],
            data.get("is_blocked", False),
            data.get("pin_attempts", 0),
        )
