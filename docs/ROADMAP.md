# Finance OS — Product Roadmap

## Current State

The product already supports:

- Dashboard
  - income vs expense chart for the last 12 months
  - spending by category for selected month
- Instruments
  - bank accounts and credit cards
  - currently Santander, XP and BBVA
- Import
- Import History
- Transactions
- Statements
- Categories
- Rules

The system already imports bank and credit card data and allows category-based spending analysis.

---

## Product Direction

The next goal is NOT polish/refinement first.

The next goal is to expand the product with major new functional modules that significantly increase product value.

The next product evolution will be based on 3 major modules:

1. Planning and Control
2. Payables and Recurring Expenses
3. Investments

These 3 modules will transform the system from a transaction tracking app into a more complete personal financial management product.

---

# Phase A — Planning and Control

## Goal

Allow users to define monthly spending goals by category and compare planned vs actual spending.

## Main capabilities

- monthly budget by category
- selected month planning
- planned amount
- actual amount
- remaining amount
- percentage consumed
- over-budget visual indicators
- consolidated month planning view
- category-level planning view
- copy budget from previous month
- optional default monthly template

## Core user questions answered

- How much did I plan to spend this month?
- How much have I already spent in each category?
- Which categories are over budget?
- How much can I still spend?

## Functional notes

- planning is monthly
- planning is category-based
- actual values are computed from categorized transactions
- transfer categories must not count as expense budgets
- income categories may be supported later, but initial focus is expenses

---

# Phase B — Payables and Recurring Expenses

## Goal

Provide a lightweight accounts-payable and recurring-expense management layer.

## Main capabilities

- detect recurring transactions from history
- suggest recurring expense patterns
- allow user to approve, ignore or edit detected recurring patterns
- generate upcoming monthly payable items
- track payable status:
  - expected
  - pending
  - paid
  - ignored
- allow manual payable creation
- due date
- expected amount
- category
- notes

## Core user questions answered

- What recurring bills do I have this month?
- What is still pending?
- What has already been paid?
- Which recurring expenses were automatically detected?

## Functional notes

- recurring detection should be heuristic-based in the beginning
- suggested recurring items should require user confirmation
- manual payables must coexist with detected recurring items
- this module should not depend on automatic bank reconciliation in the first cycle

---

# Phase C — Investments

## Goal

Provide a dedicated module for tracking investments and total financial assets.

## Main capabilities

- manual investment account creation
- asset class support:
  - fixed income
  - stocks
  - ETFs
  - funds
  - crypto
  - pension
  - cash-like assets
- manual asset registration
- current position
- acquisition cost
- current value
- allocation by asset class
- portfolio summary
- simple portfolio snapshot history
- basic net worth view

## Core user questions answered

- What is my current invested balance?
- How is my portfolio allocated?
- How much do I have in each class?
- How is my invested wealth evolving over time?

## Functional notes

- first version is manual only
- automatic brokerage integration is out of scope
- first cycle should focus on portfolio tracking, not trading history complexity

---

# Recommended Execution Order

## 1. Planning and Control
Reason:
- highest value with the current categorized transaction base
- easiest to connect with existing categories, dashboard and transactions

## 2. Payables and Recurring Expenses
Reason:
- strong practical value
- leverages existing imported transaction history
- increases retention

## 3. Investments
Reason:
- high product value, but deserves a more deliberate model
- can be launched after cashflow/planning features are stable

---

# Roadmap Principles

- prioritize new functional modules before visual polish
- avoid unnecessary refactors
- reuse existing backend and frontend architecture
- maintain controlled phase execution
- each phase should be independently usable
- each phase should update CLAUDE.md and TASKS.md before implementation

---

# Future After These Phases

After these three modules are implemented, the next roadmap can focus on:

- dashboard 2.0
- categorization 2.0
- merchant intelligence
- search
- exports
- onboarding
- stronger product branding
- multi-user/auth preparation
- cloud-readiness