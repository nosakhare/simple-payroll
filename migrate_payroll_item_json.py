from app import create_app, db
from models import PayrollItem
import json


def convert_json_fields():
    app = create_app()
    with app.app_context():
        items = PayrollItem.query.all()
        converted = 0
        for item in items:
            changed = False
            if isinstance(item.allowances, str):
                try:
                    item.allowances = json.loads(item.allowances) if item.allowances else {}
                    changed = True
                except Exception:
                    pass
            if isinstance(item.deductions, str):
                try:
                    item.deductions = json.loads(item.deductions) if item.deductions else {}
                    changed = True
                except Exception:
                    pass
            if isinstance(item.tax_details, str):
                try:
                    item.tax_details = json.loads(item.tax_details) if item.tax_details else {}
                    changed = True
                except Exception:
                    pass
            if changed:
                db.session.add(item)
                converted += 1
        if converted:
            db.session.commit()
        print(f"Converted {converted} payroll items")


if __name__ == "__main__":
    convert_json_fields()
