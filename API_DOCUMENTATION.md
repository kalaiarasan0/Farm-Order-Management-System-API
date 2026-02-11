# Farmai API Documentation

This document provides a comprehensive reference for the Farmai API endpoints.

## Base URL
All API endpoints are prefixed with `/api/v1`.

---

## 1. Health Check

### Get Health Status
- **Method:** `GET`
- **Path:** `/health/`
- **Description:** check if the API is running.

**Response Example:**
```json
{
  "status": "healthy"
}
```

---

## 2. Business Logic

### Products (Animals)

#### Create Product
- **Method:** `POST`
- **Path:** `/products/create`
- **Description:** Create a new product (animal) in the catalog.

**Request Body Example:**
```json
{
  "sku": "GOAT-001",
  "species": "Goat",
  "name": "Boer Goat",
  "description": "Premium breed",
  "base_price": 250.00,
  "specs": "{\"weight\": \"40kg\"}"
}
```

**Response Example:**
```json
{
  "product_id": 1,
  "sku": "GOAT-001",
  "species": "Goat",
  "name": "Boer Goat",
  "description": "Premium breed",
  "base_price": 250.0,
  "specs": "{\"weight\": \"40kg\"}",
  "created_at": "2023-10-27T10:00:00",
  "updated_at": null
}
```

#### Get Product by ID
- **Method:** `GET`
- **Path:** `/products/id/{product_id}`
- **Description:** Retrieve a product by its ID.

#### List Products
- **Method:** `GET`
- **Path:** `/products/list`
- **Description:** List all products.

### Inventories

#### Create Inventory
- **Method:** `POST`
- **Path:** `/inventories/create`
- **Description:** Add stock for a product.

**Request Body Example:**
```json
{
  "product_id": 1,
  "quantity": 50,
  "unit_price": 250.00,
  "location": "Barn A",
  "status": "available",
  "specs": "Batch 1"
}
```

**Response Example:**
```json
{
  "inventory_id": 1,
  "product_id": 1,
  "quantity": 50,
  "unit_price": 250.0,
  "location": "Barn A",
  "status": "available",
  "specs": "Batch 1",
  "created_at": "2023-10-27T10:00:00"
}
```

#### List Inventories
- **Method:** `GET`
- **Path:** `/inventories/list?limit=50&offset=0`
- **Description:** List all inventory items.

### Customers

#### Create Customer
- **Method:** `POST`
- **Path:** `/customers/create-customer`
- **Description:** Register a new customer.

**Request Body Example:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "phone": "+1234567890"
}
```

**Response Example:**
```json
{
  "customer_id": 1,
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "phone": "+1234567890",
  "created_at": "2023-10-27T10:00:00"
}
```

#### Get Customer by Phone
- **Method:** `GET`
- **Path:** `/customers/by-phone/{phone}`
- **Description:** Lookup a customer by phone number.

### Orders

#### Place Order
- **Method:** `POST`
- **Path:** `/orders/place-order`
- **Description:** Place a new order for products.

**Request Body Example:**
```json
{
  "customer_id": 1,
  "items": [
    {
      "product_id": 1,
      "inventory_id": 1,
      "quantity": 2
    }
  ],
  "shipping": 20.0,
  "tax": 15.0
}
```

**Response Example:**
```json
{
  "order_id": 1,
  "order_number": "ORD-2023-001",
  "customer_id": 1,
  "subtotal": 500.0,
  "shipping": 20.0,
  "tax": 15.0,
  "total": 535.0,
  "items": [
    {
      "order_item_id": 1,
      "product_id": 1,
      "quantity": 2,
      "unit_price": 250.0,
      "total_price": 500.0
    }
  ]
}
```

#### List Orders
- **Method:** `GET`
- **Path:** `/orders/list`
- **Description:** List all orders.

### Addresses

#### Create Address
- **Method:** `POST`
- **Path:** `/addresses/create-address`
- **Description:** Create a new address. `customer_id` is required in the payload.

**Request Body Example:**
```json
{
  "customer_id": 1,
  "label": "Home",
  "line1": "123 Main St",
  "city": "Springfield",
  "state": "IL",
  "postal_code": "62704",
  "country": "USA"
}
```

---

## 3. Tracking (Traceability)

### Track Animals

#### Create Tracked Animal
- **Method:** `POST`
- **Path:** `/track/animals/create`
- **Description:** Register an individual animal for tracking.

**Request Body Example:**
```json
{
  "tag_id": "TAG-12345",
  "main_animal_id": 1,
  "gender": "Female",
  "birth_date": "2023-01-01T00:00:00",
  "purchase_date": "2023-05-01T00:00:00",
  "source": "Farm B",
  "purchase_price": 200.00,
  "status": "active"
}
```

#### List Tracked Animals
- **Method:** `GET`
- **Path:** `/track/animals/list`
- **Description:** List all tracked animals with their event history.

### Animal Events

#### Create Event
- **Method:** `POST`
- **Path:** `/track/animal_events/create`
- **Description:** Log an event (e.g., vaccination, weighing) for an animal.

**Request Body Example:**
```json
{
  "animal_id": 1,
  "event_type": "vaccination",
  "event_date": "2023-10-27T10:00:00",
  "notes": "Administered annual vaccines"
}
```

### Animal Movement (to Inventory)

#### Create Movement
- **Method:** `POST`
- **Path:** `/track/inventory_animals/create`
- **Description:** Move animal history to inventory.

**Request Body Example:**
```json
{
  "animal_id": 1,
  "movement_type": "sold",
  "movement_date": "2023-10-28T10:00:00",
  "notes": "Moving to sold inventory"
}
```

---

## 4. AI Agents

### Verify Order
- **Method:** `POST`
- **Path:** `/ai_work/create_token_order`
- **Description:** Verify customer and inventory availability before placing an order. Returns a verification token.

**Request Body Example:**
```json
{
  "product_id": 1,
  "customer_id": 1,
  "quantity": 5
}
```

**Response Example:**
```json
{
  "status": "success",
  "message": "Order verification successful",
  "verification_token": "abc-123-uuid-token"
}
```

### Place Order (AI)
- **Method:** `POST`
- **Path:** `/ai_work/place_order`
- **Description:** Finalize an order using a verification token.

**Request Body Example:**
```json
{
  "verification_token": "abc-123-uuid-token"
}
```
