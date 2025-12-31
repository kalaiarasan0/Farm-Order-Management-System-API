import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas.ai_work import VerifyOrder, VerifyOrderResponse, PlaceOrderRequest
from app.models.tables import Customer, Inventory, OrderVerificationToken
# from app.services.animals import create_animal, get_animal_by_id, get_animal_by_name, list_animals

router = APIRouter(prefix="/api/v1/ai_work", tags=["ai_work"])


@router.post("/create_token_order", response_model=VerifyOrderResponse)
def create_token_order(request: VerifyOrder, db: Session = Depends(get_db)):
    # 1. Verify Customer
    customer = db.query(Customer).filter(Customer.id == request.customer_id).first()
    if not customer:
        return VerifyOrderResponse(status="error", message="Customer not found")

    # 2. Check Inventory (via Animal ID)
    # The request has product_id which maps to animal_id in inventory
    inventory = (
        db.query(Inventory).filter(Inventory.animal_id == request.product_id).first()
    )

    if not inventory:
        return VerifyOrderResponse(
            status="error", message="Product (Inventory) not found"
        )

    if inventory.quantity < request.quantity:
        return VerifyOrderResponse(
            status="error",
            message=f"Insufficient inventory. Available: {inventory.quantity}, Requested: {request.quantity}",
        )

    # 3. Generate Verification Token
    token = str(uuid.uuid4())

    # 4. Store Token
    verification_entry = OrderVerificationToken(
        token=token,
        customer_id=request.customer_id,
        product_id=request.product_id,
        quantity=request.quantity,
    )
    db.add(verification_entry)
    db.commit()
    db.refresh(verification_entry)

    return VerifyOrderResponse(
        status="success",
        message="Order verification successful",
        verification_token=token,
    )


@router.post("/place_order", response_model=dict)
def place_order(request: PlaceOrderRequest, db: Session = Depends(get_db)):
    # 1. Retrieve Token
    token_entry = (
        db.query(OrderVerificationToken)
        .filter(OrderVerificationToken.token == request.verification_token)
        .first()
    )
    if not token_entry:
        return {"status": "error", "message": "Invalid or expired verification token"}

    # 2. Place Order using Service
    try:
        # Construct item list as expected by create_order
        # Extract values before committing (which expires objects)
        items = [
            {"animal_id": token_entry.product_id, "quantity": token_entry.quantity}
        ]
        customer_id = token_entry.customer_id

        # Determine strict transaction boundary:
        # The create_order service uses `with db.begin():` which requires no active transaction.
        # The query above started an implicit transaction. We must end it.
        db.commit()

        from app.services.orders import create_order

        # We pass customer_id from token
        order = create_order(db, customer_id=customer_id, items=items)

        # 3. (Optional) Delete token to prevent reuse
        # db.delete(token_entry)
        # db.commit()

    except ValueError as e:
        return {"status": "error", "message": str(e)}
    except Exception as e:
        return {"status": "error", "message": f"An error occurred: {str(e)}"}

    return {
        "status": "success",
        "message": "Order placed successfully",
        "order_id": order.id,
        "order_number": order.order_number,
    }
