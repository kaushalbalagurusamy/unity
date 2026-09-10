package ledger

import (
	"errors"
	"sync"
)

// Standard domain errors for ledger operations.
var (
	ErrNotFound          = errors.New("account not found")
	ErrInvalidAmount     = errors.New("amount must be strictly positive")
	ErrInsufficientFunds = errors.New("insufficient funds for withdrawal")
)

// Ledger represents a thread-safe financial ledger storing account balances.
type Ledger struct {
	mu       sync.Mutex
	balances map[string]int64
}

// NewLedger initializes a fresh Ledger instance.
func NewLedger() *Ledger {
	return &Ledger{
		balances: make(map[string]int64),
	}
}

// CreateAccount creates a new account with an initial balance.
func (l *Ledger) CreateAccount(accountID string, initialBalance int64) {
	l.mu.Lock()
	defer l.mu.Unlock()
	l.balances[accountID] = initialBalance
}

// GetBalance queries the current account balance under exclusive lock.
func (l *Ledger) GetBalance(accountID string) (int64, error) {
	l.mu.Lock()
	defer l.mu.Unlock()

	bal, exists := l.balances[accountID]
	if !exists {
		return 0, ErrNotFound
	}
	return bal, nil
}

// Deposit adds funds to an account and returns the new balance.
func (l *Ledger) Deposit(accountID string, amount int64) (int64, error) {
	if amount <= 0 {
		return 0, ErrInvalidAmount
	}

	l.mu.Lock()
	defer l.mu.Unlock()

	current, exists := l.balances[accountID]
	if !exists {
		return 0, ErrNotFound
	}

	newBalance := current + amount
	l.balances[accountID] = newBalance
	return newBalance, nil
}

// Withdraw deducts funds from an account while preserving non-negative balance invariant.
func (l *Ledger) Withdraw(accountID string, amount int64) (int64, error) {
	if amount <= 0 {
		return 0, ErrInvalidAmount
	}

	l.mu.Lock()
	defer l.mu.Unlock()

	current, exists := l.balances[accountID]
	if !exists {
		return 0, ErrNotFound
	}

	if current-amount < 0 {
		return 0, ErrInsufficientFunds
	}

	newBalance := current - amount
	l.balances[accountID] = newBalance
	return newBalance, nil
}
