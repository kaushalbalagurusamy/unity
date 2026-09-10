"""
Concurrent Bank Ledger Implementation in Python.
Serves as the Python Golden Source Anchor for Project Unity.
"""

from __future__ import annotations
import threading
from typing import Dict
import deal


class LedgerError(Exception):
    """Base exception for ledger failures."""
    pass


class NotFoundError(LedgerError):
    """Account does not exist."""
    pass


class InvalidAmountError(LedgerError):
    """Amount must be strictly positive."""
    pass


class InsufficientFundsError(LedgerError):
    """Account balance cannot cover withdrawal."""
    pass


class Ledger:
    """Thread-safe financial ledger storing account balances."""

    def __init__(self) -> None:
        self.balances: Dict[str, int] = {}
        self.mu: threading.Lock = threading.Lock()

    def create_account(self, account_id: str, initial_balance: int = 0) -> None:
        """Create a new account with an initial balance."""
        with self.mu:
            self.balances[account_id] = initial_balance

    @deal.pre(lambda self, account_id: account_id in self.balances, exception=NotFoundError)
    def get_balance(self, account_id: str) -> int:
        """Query account balance under exclusive lock."""
        with self.mu:
            if account_id not in self.balances:
                raise NotFoundError(f"Account '{account_id}' not found")
            return self.balances[account_id]

    @deal.pre(lambda self, account_id, amount: amount > 0, exception=InvalidAmountError)
    @deal.pre(lambda self, account_id, amount: account_id in self.balances, exception=NotFoundError)
    @deal.ensure(lambda self, account_id, amount, result: result == self.balances[account_id])
    @deal.raises(NotFoundError, InvalidAmountError)
    def deposit(self, account_id: str, amount: int) -> int:
        """Deposit funds into an account and return the new balance."""
        if amount <= 0:
            raise InvalidAmountError("Deposit amount must be strictly positive")

        with self.mu:
            if account_id not in self.balances:
                raise NotFoundError(f"Account '{account_id}' not found")
            new_balance = self.balances[account_id] + amount
            self.balances[account_id] = new_balance
            return new_balance

    @deal.pre(lambda self, account_id, amount: amount > 0, exception=InvalidAmountError)
    @deal.pre(lambda self, account_id, amount: account_id in self.balances, exception=NotFoundError)
    @deal.pre(
        lambda self, account_id, amount: self.balances[account_id] >= amount,
        exception=InsufficientFundsError,
    )
    @deal.ensure(lambda self, account_id, amount, result: self.balances[account_id] >= 0)
    @deal.raises(NotFoundError, InvalidAmountError, InsufficientFundsError)
    def withdraw(self, account_id: str, amount: int) -> int:
        """Withdraw funds from an account under balance invariant preservation."""
        if amount <= 0:
            raise InvalidAmountError("Withdrawal amount must be strictly positive")

        with self.mu:
            if account_id not in self.balances:
                raise NotFoundError(f"Account '{account_id}' not found")
            current = self.balances[account_id]
            if current - amount < 0:
                raise InsufficientFundsError("Insufficient funds for withdrawal")
            new_balance = current - amount
            self.balances[account_id] = new_balance
            return new_balance


if __name__ == "__main__":
    ledger = Ledger()
    ledger.create_account("acc-001", 1000)

    # Concurrency verification test
    def worker_withdraw() -> None:
        for _ in range(10):
            ledger.withdraw("acc-001", 10)

    def worker_deposit() -> None:
        for _ in range(10):
            ledger.deposit("acc-001", 10)

    threads = [
        threading.Thread(target=worker_withdraw) for _ in range(5)
    ] + [
        threading.Thread(target=worker_deposit) for _ in range(5)
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    final_balance = ledger.get_balance("acc-001")
    assert final_balance == 1000, f"Expected 1000, got {final_balance}"
    print(f"Python Ledger verified green! Final balance: {final_balance}")
