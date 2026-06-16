# Circulation subsystem rules

- A copy cannot have more than one active loan.
- Checkout requires an available copy.
- Return requires an active loan.
- Loan mutations must be transactional.
- Historical loans must remain visible after archival.
- Every change requires unit or property-based tests.
