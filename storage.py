import os
import pathlib
import sqlite3
import uuid

from models.account import Account
from models.card import Card
from models.transaction import Transaction

_BASE = pathlib.Path(__file__).parent
_DB_PATH = str(_BASE / "data" / "atm.db")

DEFAULT_CARD_NUMBER = "1234567890123456"
DEFAULT_PIN = "1234"
DEFAULT_OWNER = "Иван Иванов"
DEFAULT_BALANCE = 10000.0
DEFAULT_ATM_CASH = 500000.0


class Storage:

    @staticmethod
    def _db_path() -> str:
        return _DB_PATH

    @staticmethod
    def _get_connection() -> sqlite3.Connection:
        os.makedirs(os.path.dirname(Storage._db_path()), exist_ok=True)
        conn = sqlite3.connect(Storage._db_path())
        conn.execute("PRAGMA foreign_keys = ON")
        Storage._init_schema(conn)
        return conn

    @staticmethod
    def _init_schema(conn: sqlite3.Connection) -> None:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS accounts (
                account_id TEXT PRIMARY KEY,
                owner      TEXT NOT NULL,
                balance    REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS cards (
                card_number  TEXT PRIMARY KEY,
                pin_hash     TEXT NOT NULL,
                account_id   TEXT NOT NULL REFERENCES accounts(account_id),
                is_blocked   INTEGER NOT NULL DEFAULT 0,
                pin_attempts INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id  TEXT NOT NULL REFERENCES accounts(account_id),
                type        TEXT NOT NULL,
                amount      REAL NOT NULL,
                timestamp   TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS atm_state (
                id           INTEGER PRIMARY KEY CHECK (id = 1),
                cash_balance REAL NOT NULL
            );
        """)
        # Seed defaults if the default card doesn't exist yet
        existing = conn.execute(
            "SELECT COUNT(*) FROM cards WHERE card_number = ?",
            (DEFAULT_CARD_NUMBER,),
        ).fetchone()[0]
        if existing == 0:
            account_id = str(uuid.uuid4())
            conn.execute(
                "INSERT OR IGNORE INTO accounts VALUES (?, ?, ?)",
                (account_id, DEFAULT_OWNER, DEFAULT_BALANCE),
            )
            conn.execute(
                "INSERT INTO cards VALUES (?, ?, ?, 0, 0)",
                (DEFAULT_CARD_NUMBER, Card.hash_pin(DEFAULT_PIN), account_id),
            )
            conn.execute(
                "INSERT OR IGNORE INTO atm_state VALUES (1, ?)",
                (DEFAULT_ATM_CASH,),
            )
            conn.commit()

    @staticmethod
    def load_accounts() -> dict:
        conn = Storage._get_connection()
        try:
            with conn:
                accounts = {}
                for row in conn.execute("SELECT account_id, owner, balance FROM accounts"):
                    acc = Account(row[0], row[1], row[2])
                    accounts[row[0]] = acc

                for row in conn.execute(
                    "SELECT account_id, type, amount, timestamp, description FROM transactions ORDER BY id"
                ):
                    acc = accounts.get(row[0])
                    if acc is None:
                        continue
                    t = Transaction(row[1], row[2], row[4])
                    t.timestamp = row[3]
                    acc.transactions.append(t)

                cards = {}
                for row in conn.execute(
                    "SELECT card_number, pin_hash, account_id, is_blocked, pin_attempts FROM cards"
                ):
                    cards[row[0]] = Card(row[0], row[1], row[2], bool(row[3]), row[4])

            return {"accounts": accounts, "cards": cards}
        finally:
            conn.close()

    @staticmethod
    def save_accounts(accounts: dict, cards: dict) -> None:
        conn = Storage._get_connection()
        try:
            with conn:
                conn.execute("DELETE FROM transactions")
                conn.execute("DELETE FROM cards")
                conn.execute("DELETE FROM accounts")

                for acc in accounts.values():
                    conn.execute(
                        "INSERT INTO accounts VALUES (?, ?, ?)",
                        (acc.account_id, acc.owner, acc.balance),
                    )

                for card in cards.values():
                    conn.execute(
                        "INSERT INTO cards VALUES (?, ?, ?, ?, ?)",
                        (
                            card.card_number,
                            card.pin_hash,
                            card.account_id,
                            int(card.is_blocked),
                            card.pin_attempts,
                        ),
                    )

                for acc in accounts.values():
                    for t in acc.transactions:
                        conn.execute(
                            "INSERT INTO transactions (account_id, type, amount, timestamp, description) VALUES (?, ?, ?, ?, ?)",
                            (acc.account_id, t.type, t.amount, t.timestamp, t.description),
                        )
        finally:
            conn.close()

    @staticmethod
    def load_atm() -> float:
        conn = Storage._get_connection()
        try:
            with conn:
                row = conn.execute("SELECT cash_balance FROM atm_state WHERE id = 1").fetchone()
            if row is None:
                return DEFAULT_ATM_CASH
            return row[0]
        finally:
            conn.close()

    @staticmethod
    def save_atm(cash_balance: float) -> None:
        conn = Storage._get_connection()
        try:
            with conn:
                conn.execute(
                    "UPDATE atm_state SET cash_balance = ? WHERE id = 1",
                    (cash_balance,),
                )
        finally:
            conn.close()
