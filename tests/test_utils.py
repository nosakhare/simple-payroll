import os
import sys
import types
import pytest

# Ensure project root is on sys.path so utils can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

class DummyQuery:
    def order_by(self, *args, **kwargs):
        return self
    def all(self):
        return []

class DummyTaxBracket:
    lower_limit = 0
    query = DummyQuery()

# Provide a dummy 'models' module so utils imports without database dependencies
sys.modules['models'] = types.SimpleNamespace(
    TaxBracket=DummyTaxBracket,
    Employee=None,
    Payroll=None,
    PayrollItem=None,
    SalaryConfiguration=None,
)

import utils

def test_calculate_paye_tax_default_brackets(monkeypatch):
    monkeypatch.setattr(utils, 'TaxBracket', DummyTaxBracket)
    tax, details = utils.calculate_paye_tax(4_000_000)
    assert pytest.approx(tax) == 752_000
    assert len(details) == 6

def test_calculate_paye_tax_partial_bracket(monkeypatch):
    monkeypatch.setattr(utils, 'TaxBracket', DummyTaxBracket)
    tax, details = utils.calculate_paye_tax(250_000)
    assert pytest.approx(tax) == 17_500
    assert len(details) == 1

def test_calculate_pension_standard():
    amount = utils.calculate_pension(50_000, 10_000, 15_000, False)
    assert pytest.approx(amount) == 6_000

def test_calculate_pension_contract():
    amount = utils.calculate_pension(50_000, 10_000, 15_000, True)
    assert amount == 0

