#!/usr/bin/env python3
"""Python re-implementation of src/program.cbl (BOOKFORUM). Run from the cobol/ directory."""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS = os.path.join(BASE, "data", "ACCOUNTS.DAT")
BOOKS = os.path.join(BASE, "data", "BOOKS.DAT")
TRANSACTIONS = os.path.join(BASE, "data", "TRANSACTIONS.DAT")
INPUT = os.path.join(BASE, "src", "INPUT.DAT")

ACC_LEN, BOOK_LEN, TRANS_LEN, INPUT_LEN = 34, 28, 22, 22


def read_records(path, size):
    """Fixed-length sequential records; a short final record is space-padded."""
    if not os.path.exists(path):
        return []
    with open(path, "rb") as f:
        data = f.read()
    recs = []
    for i in range(0, len(data), size):
        recs.append(bytearray(data[i:i + size].ljust(size, b" ")))
    return recs


def write_records(path, recs):
    with open(path, "wb") as f:
        for r in recs:
            f.write(bytes(r))


def display_num(field):
    """GnuCOBOL-style numeric DISPLAY decode: each byte contributes its low nibble."""
    n = 0
    for b in field:
        n = n * 10 + ((b & 0x0F) % 10)
    return n


def pic9(n, digits=10):
    """Store into an unsigned PIC 9(n): sign dropped, high-order digits truncated."""
    return str(abs(int(n)) % (10 ** digits)).zfill(digits).encode()


def main():
    inputs = read_records(INPUT, INPUT_LEN)
    if not inputs:
        print("Error: Input file is empty")
        return
    rec = inputs[0]
    buyer, seller, book = bytes(rec[0:4]), bytes(rec[4:8]), bytes(rec[8:12])
    amount = display_num(rec[12:22])  # integer part of 9(10)V99

    accounts = read_records(ACCOUNTS, ACC_LEN)
    books = read_records(BOOKS, BOOK_LEN)
    buyer_found = any(bytes(a[0:4]) == buyer for a in accounts)
    seller_found = any(bytes(a[0:4]) == seller for a in accounts)
    book_found = valid_owner = False
    for b in books:
        if bytes(b[0:4]) == book:
            book_found = True
            if bytes(b[24:28]) == seller:
                valid_owner = True
    print(" ")

    if not (buyer_found and seller_found and book_found and valid_owner):
        print("Transaction failed due to validation errors")
        return

    for a in accounts:
        if bytes(a[0:4]) == buyer:
            a[24:34] = pic9(display_num(a[24:34]) - amount)
        if bytes(a[0:4]) == seller:
            a[24:34] = pic9(display_num(a[24:34]) + amount)
    write_records(ACCOUNTS, accounts)

    for b in books:
        if bytes(b[0:4]) == book:
            b[24:28] = buyer
    write_records(BOOKS, books)

    with open(TRANSACTIONS, "ab") as f:
        f.write(book + pic9(amount) + seller + buyer)

    print("Transaction completed successfully")


if __name__ == "__main__":
    main()
    sys.exit(0)
