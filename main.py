from storage import Storage
from bank import Bank
from atm import ATM
from exceptions import ATMError, CardBlockedError

ADMIN_PASSWORD = "admin"


def get_amount(prompt: str) -> float:
    while True:
        try:
            value = float(input(prompt))
            if value <= 0:
                print("Сумма должна быть больше нуля.")
                continue
            return value
        except ValueError:
            print("Введите числовое значение.")


def show_history(account) -> None:
    history = account.get_history()
    if not history:
        print("\nИстория операций пуста.")
        return
    print("\n--- История операций ---")
    for t in history:
        sign = "+" if t.type == "deposit" else "-"
        print(f"  {t.timestamp[:19]}  {sign}{t.amount:.2f} ₽  {t.description}")


def user_menu(atm: ATM, card_number: str) -> None:
    card = atm.bank.find_card(card_number)
    account = atm.bank.find_account(card.account_id)

    while True:
        print("\n--- Меню ---")
        print("1. Проверить баланс")
        print("2. Снять наличные")
        print("3. Внести наличные")
        print("4. Перевести на другую карту")
        print("5. История операций")
        print("0. Завершить сеанс")

        choice = input("Выберите действие: ").strip()

        if choice == "1":
            print(f"\nБаланс: {account.balance:.2f} ₽")

        elif choice == "2":
            amount = get_amount("Сумма для снятия: ")
            try:
                atm.withdraw(account, amount)
                print(f"Выдано {amount:.2f} ₽. Остаток: {account.balance:.2f} ₽")
            except ATMError as e:
                print(f"Ошибка: {e}")

        elif choice == "3":
            amount = get_amount("Сумма для внесения: ")
            try:
                atm.deposit(account, amount)
                print(f"Внесено {amount:.2f} ₽. Остаток: {account.balance:.2f} ₽")
            except ATMError as e:
                print(f"Ошибка: {e}")

        elif choice == "4":
            to_card = input("Номер карты получателя: ").strip()
            amount = get_amount("Сумма перевода: ")
            try:
                atm.transfer(account, to_card, amount)
                print(f"Переведено {amount:.2f} ₽. Остаток: {account.balance:.2f} ₽")
            except ATMError as e:
                print(f"Ошибка: {e}")

        elif choice == "5":
            show_history(account)

        elif choice == "0":
            print("Сеанс завершён.")
            break

        else:
            print("Неверный выбор.")


def admin_menu(atm: ATM) -> None:
    bank = atm.bank

    while True:
        print("\n--- Меню администратора ---")
        print("1. Создать счёт и карту")
        print("2. Пополнить кассу банкомата")
        print("3. Просмотреть все счета")
        print("4. Разблокировать карту")
        print("0. Выход")

        choice = input("Выберите действие: ").strip()

        if choice == "1":
            owner = input("Имя владельца: ").strip()
            if not owner:
                print("Имя не может быть пустым.")
                continue
            try:
                initial_balance = float(input("Начальный баланс (₽, 0 — без средств): ").strip())
                initial_balance = max(initial_balance, 0.0)
            except ValueError:
                initial_balance = 0.0
            pin = input("PIN-код (4 цифры): ").strip()
            account = bank.create_account(owner, initial_balance)
            card = bank.create_card(account.account_id, pin)
            bank.save()
            print("\nСчёт создан.")
            print(f"Номер карты: {card.card_number}")
            print(f"Баланс:      {initial_balance:.2f} ₽")

        elif choice == "2":
            amount = get_amount("Сумма пополнения кассы: ")
            try:
                atm.replenish_cash(amount)
                print(f"Касса пополнена. Итого в кассе: {atm.cash_balance:.2f} ₽")
            except ATMError as e:
                print(f"Ошибка: {e}")

        elif choice == "3":
            accounts = bank.get_all_accounts()
            print(f"\n--- Все счета ({len(accounts)}) ---")
            for acc in accounts:
                cards = [
                    c.card_number
                    for c in bank.cards.values()
                    if c.account_id == acc.account_id
                ]
                blocked = any(
                    c.is_blocked
                    for c in bank.cards.values()
                    if c.account_id == acc.account_id
                )
                status = " [ЗАБЛОКИРОВАНА]" if blocked else ""
                print(
                    f"  {acc.owner}: {acc.balance:.2f} ₽"
                    f"  Карты: {', '.join(cards)}{status}"
                )

        elif choice == "4":
            card_number = input("Номер карты: ").strip()
            if bank.unblock_card(card_number):
                bank.save()
                print(f"Карта {card_number} разблокирована.")
            else:
                print("Карта не найдена.")

        elif choice == "0":
            break

        else:
            print("Неверный выбор.")


def login_user(atm: ATM) -> None:
    bank = atm.bank
    card_number = input("Введите номер карты: ").strip()
    card = bank.find_card(card_number)
    if card is None:
        print("Карта не найдена.")
        return
    if card.is_blocked:
        print("Карта заблокирована. Обратитесь к администратору.")
        return

    for _ in range(3):
        pin = input("Введите PIN: ").strip()
        try:
            if card.verify_pin(pin):
                bank.save()
                user_menu(atm, card_number)
                return
            remaining = 3 - card.pin_attempts
            print(f"Неверный PIN. Осталось попыток: {remaining}")
            bank.save()
        except CardBlockedError as e:
            print(str(e))
            bank.save()
            return


def main() -> None:
    data = Storage.load_accounts()
    bank = Bank(data["accounts"], data["cards"])
    atm = ATM(Storage.load_atm(), bank)

    print("=" * 40)
    print("           БАНКОМАТ")
    print("=" * 40)

    while True:
        print("\n1. Войти как пользователь")
        print("2. Войти как администратор")
        print("0. Выход")

        choice = input("Выберите: ").strip()

        if choice == "1":
            login_user(atm)

        elif choice == "2":
            password = input("Пароль администратора: ").strip()
            if password == ADMIN_PASSWORD:
                admin_menu(atm)
            else:
                print("Неверный пароль.")

        elif choice == "0":
            print("До свидания!")
            break

        else:
            print("Неверный выбор.")


if __name__ == "__main__":
    main()
