A lightweight, opinionated payroll engine and self‑hostable admin UI, built with Flask & SQLAlchemy, tuned for Nigerian payroll rules but easily extensible to any locale.

Payroll Calculation Logic:
Net = Gross − (PAYE + Pension + NHF + NHIS) − Deductions + Allowances

All rules live in services/payroll/calculators.py. Add or override by subclassing BaseRule and registering via entry‑point.
