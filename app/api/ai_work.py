import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import get_async_db
from app.schemas.ai_work import VerifyOrder, VerifyOrderResponse, PlaceOrderRequest
from app.models.tables import Customer, Inventory, OrderVerificationToken
from app.api.auth import get_current_active_user
# from app.services.animals import create_animal, get_animal_by_id, get_animal_by_name, list_animals

router = APIRouter(prefix="/api/v1/ai_work", tags=["ai_work"])


@router.post("/create_token_order", response_model=VerifyOrderResponse)
async def create_token_order(
    request: VerifyOrder,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    # 1. Verify Customer
    customer = (
        await db.execute(select(Customer).filter(Customer.id == request.customer_id))
    ).scalar_one_or_none()
    if not customer:
        return VerifyOrderResponse(status="error", message="Customer not found")

    # 2. Check Inventory (via Animal ID)
    # The request has category_id which maps to animal_id in inventory
    inventory = (
        await db.execute(
            select(Inventory).filter(Inventory.animal_id == request.category_id)
        )
    ).scalar_one_or_none()

    if not inventory:
        return VerifyOrderResponse(
            status="error", message="category (Inventory) not found"
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
        category_id=request.category_id,
        quantity=request.quantity,
        created_by=str(current_user.unique_id),
    )
    db.add(verification_entry)
    await db.commit()
    await db.refresh(verification_entry)

    return VerifyOrderResponse(
        status="success",
        message="Order verification successful",
        verification_token=token,
    )


@router.post("/place_order", response_model=dict)
async def place_order(
    request: PlaceOrderRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    # 1. Retrieve Token
    token_entry = (
        await db.execute(
            select(OrderVerificationToken).filter(
                OrderVerificationToken.token == request.verification_token
            )
        )
    ).scalar_one_or_none()

    if not token_entry:
        return {"status": "error", "message": "Invalid or expired verification token"}

    # 2. Place Order using Service
    try:
        # Construct item list as expected by create_order
        # Extract values before committing (which expires objects)
        items = [
            {"animal_id": token_entry.category_id, "quantity": token_entry.quantity}
        ]
        customer_id = token_entry.customer_id

        # Determine strict transaction boundary:
        # The create_order service uses `with db.begin():` which requires no active transaction.
        # But here we are merely reading (autocommit mode usually for AsyncSession if not explicit begin?)
        # Actually AsyncSession usually starts transaction on first execute.
        # But create_order manages its own transaction?
        # create_order uses `async with db.begin():`. Accessing db.begin() when transaction is active raises error.
        # So we should close/commit current transaction if any.
        # But we only did SELECTs.
        # We can commit to be safe.
        await db.commit()

        from app.services.orders import create_order

        # We pass customer_id from token
        order = await create_order(
            db, customer_id=customer_id, items=items, current_user=current_user
        )

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
