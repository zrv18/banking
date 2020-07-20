import random
from sys import exit
from os.path import isfile
from os import getcwd
import sqlite3

global logged_in, accounts, balances, database_name, table_name


def print_menu():
    print("1. Create an account")
    print("2. Log into account")
    print("0. Exit")


def create_checksum(card_number_without_checksum):
    auxiliary_list = []
    # In the original algorithm odd digits should be multipied by 2,
    # but here is used the list - numeration starts from zero -
    # therefore even digits will be multiplied by 2.
    for _i in range(len(card_number_without_checksum)):
        if _i % 2:
            auxiliary_list.append(int(card_number_without_checksum[_i]))
        elif not _i % 2:
            auxiliary_list.append(int(card_number_without_checksum[_i]) * 2)
    # Subtract 9 to numbers over 9:
    for _i in range(len(auxiliary_list)):
        if auxiliary_list[_i] > 9:
            auxiliary_list[_i] -= 9
    checksum = 10 - sum(auxiliary_list) % 10
    return "0" if checksum == 10 else str(checksum)


def generate_card_number():
    # Algorithm:
    # 1) Create Issuer Identification Number (IIN)
    issuer_identification_number = "400000"
    # 2) Generate account identifier.
    # To do this, first generate a pseudo-random integer between 0 and 999999999, and then add the leading zeros.
    random.seed()
    pseudo_random_int = random.randint(0, 999999999)
    account_identifier = "0" * (9 - len(str(pseudo_random_int))) + str(pseudo_random_int)
    # 3) Generate checksum with Luhn algorithm.
    return issuer_identification_number\
        + account_identifier\
        + create_checksum(issuer_identification_number + account_identifier)


def generate_pin_code():
    # First generate a pseudo-random integer between 0 and 9999 and then add the leading zeros.
    random.seed()
    raw_pin = random.randint(0, 9999)
    return "0" * (4 - len(str(raw_pin))) + str(raw_pin)


def create_an_account():
    card_number = generate_card_number()
    print(f'\nYour card has been created\nYour card number:\n{card_number}')
    pin_code = generate_pin_code()
    print(f'Your card PIN:\n{pin_code}\n')
    cur.execute(f'insert into {table_name}(number, pin) values (?, ?)', (card_number, pin_code))
    accounts[card_number] = pin_code
    balances[card_number] = 0
    conn.commit()


def print_account_menu():
    print()
    print("1. Balance")
    print("2. Add income")
    print("3. Do transfer")
    print("4. Close account")
    print("5. Log out")
    print("0. Exit")


def print_balance(card):
    cur.execute(f'select balance from card where number={card}')
    balance = cur.fetchone()[0]
    print(f'\nBalance: {balance}')


def add_income(card_number):
    income = int(input("\nEnter income:\n>"))
    cur.execute(f'update card set balance=balance+{income} where number={card_number}')
    conn.commit()
    print('Income was added!')


def do_transfer(card_number):
    print("\nTransfer\nEnter card number:")
    card_number_to_transfer = input('>')
    while True:
        if card_number_to_transfer == card_number:
            print("You can't transfer money to the same account!")
            break
        if not check_checksum(card_number_to_transfer):
            print("Probably you made mistake in the card number. Please try again!")
            break
        if cur.execute(f'select id from card where number={card_number_to_transfer}').fetchone() is None:
            print('Such a card does not exist.')
            break
        print('Enter how much money you want to transfer:\n>')
        money_to_transfer = int(input())
        if money_to_transfer > cur.execute(f'select balance from card where number={card_number}').fetchone()[0]:
            print('Not enough money!')
            break
        else:
            cur.execute(f'update card set balance=balance+{money_to_transfer} where number={card_number_to_transfer}')
            conn.commit()
            cur.execute(f'update card set balance=balance-{money_to_transfer} where number={card_number}')
            conn.commit()
            print('Success!')
            break


def close_account(card_number):
    cur.execute(f'delete from card where number={card_number}')
    conn.commit()
    print('\nThe account has been closed!')


def check_checksum(card_number):
    # Algorithm:
    # 1) Drop the last digit:
    aux_list = [int(x) for x in card_number[:-1]]
    # 2) In the original algorithm odd digits should be multiplied by 2,
    # but here is used the list - numeration starts from zero -
    # therefore even digits will be multiplied by 2.
    for _i in range(len(aux_list)):
        if not _i % 2:
            aux_list[_i] *= 2
    # Subtract 9 to numbers over 9:
    for _i in range(len(aux_list)):
        if aux_list[_i] > 9:
            aux_list[_i] -= 9
    checksum = 10 - sum(aux_list) % 10
    return True if card_number[-1] == str(checksum) else False


def are_in_table(card_number, pin_code):
    cur.execute(f'select number, pin from card where number={card_number} and pin={pin_code}')
    return True if (cur.fetchone() is not None) else False


def log_into_account():
    entered_card_number = input("\nEnter your card number:\n>")
    entered_pin_code = input("Enter your PIN:\n>")
    # if check_checksum(entered_card_number) and accounts.get(entered_card_number) == entered_pin_code:
    if check_checksum(entered_card_number) and are_in_table(entered_card_number, entered_pin_code):
        global logged_in
        logged_in = True
        print("\nYou have successfully logged in!")
        while logged_in:
            print_account_menu()
            account_menu_item = int(input(">"))
            if account_menu_item == 1:
                print_balance(entered_card_number)
            elif account_menu_item == 2:
                add_income(entered_card_number)
            elif account_menu_item == 3:
                do_transfer(entered_card_number)
            elif account_menu_item == 4:
                close_account(entered_card_number)
            elif account_menu_item == 5:
                print("\nYou have successfully logged out!\n")
                logged_in = False
                break
            elif account_menu_item == 0:
                close_connection_to_database()
                exit()
    else:
        print("Wrong card number or PIN!")


def exit_from_program():
    print("\nBye!")
    close_connection_to_database()
    exit()


def database_exists():
    return isfile(f'{getcwd()}/{database_name}')


def close_connection_to_database():
    conn.close()


if __name__ == "__main__":
    # At first there are no accounts:
    accounts = {}
    # The balances are zeros yet:
    balances = {}
    # The user has not logged in yet:
    logged_in = False
    database_name = 'card.s3db'
    table_name = 'card'
    # Check if database is created and create if does not.
    if not database_exists():
        conn = sqlite3.connect(database_name)
        cur = conn.cursor()
        cur.execute(
            f'create table {table_name}(id integer primary key, number text, pin text, balance integer default 0)')
    else:
        conn = sqlite3.connect(database_name)
        cur = conn.cursor()
    while True:
        print_menu()
        chosen_menu_item = int(input('> '))
        if chosen_menu_item == 1:
            create_an_account()
        elif chosen_menu_item == 2:
            log_into_account()
        elif chosen_menu_item == 0:
            exit_from_program()
