from app.db import SessionLocal
from app.services.orders import create_order
import traceback

def main():
    db = SessionLocal()
    try:
        # provide customer_data so the service will create the customer inside the transaction
        customer_data = {"first_name": "Script", "last_name": "Buyer", "email": "script@example.com"}
        order = create_order(db, customer_id=None, customer_data=customer_data, items=[{"animal_id":1, "quantity":2}], shipping=0.0, tax=0.0)
        print('ORDER CREATED:', order.id)
    except Exception:
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    main()
