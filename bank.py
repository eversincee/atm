import random
import uuid

from models.account import Account
from models.card import Card
from storage import Storage


class Bank:
    def __init__(self, accounts: dict[str, Account], cards: dict[str, Card]):
        self.accounts = accounts
        self.cards = cards

    def find_card(self, card_number: str) -> Card | None:
        return self.cards.get(card_number)

    def find_account(self, account_id: str) -> Account | None:
        return self.accounts.get(account_id)

    def create_account(self, owner: str, initial_balance: float = 0.0) -> Account:
        account_id = str(uuid.uuid4())
        account = Account(account_id, owner, initial_balance)
        self.accounts[account_id] = account
        return account

    def create_card(self, account_id: str, pin: str) -> Card:
        card_number = self._generate_card_number()
        card = Card(card_number, Card.hash_pin(pin), account_id)
        self.cards[card_number] = card
        return card

    def unblock_card(self, card_number: str) -> bool:
        card = self.find_card(card_number)
        if card is None:
            return False
        card.unblock()
        return True

    def get_all_accounts(self) -> list[Account]:
        return list(self.accounts.values())

    def save(self) -> None:
        Storage.save_accounts(self.accounts, self.cards)

    def _generate_card_number(self) -> str:
        while True:
            number = "".join(str(random.randint(0, 9)) for _ in range(16))
            if number not in self.cards:
                return number
