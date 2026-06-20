# Order Deliveries Backend Implementations Needed

This document outlines the required backend changes to fully support the frontend delivery flows (specifically around client approval and revision requests).

## Missing Endpoints

The frontend client application expects the following endpoints which are currently missing in the backend routes (`tuned.apis.order_deliveries.routes.delivery`):

### 1. Delivery Approval
- **Expected Route**: `POST /api/orders/delivery/<order_id>/<delivery_id>/approve`
- **Purpose**: Allows a client to approve a specific delivery.
- **Expected Behavior**:
  - Validates that the client owns the order.
  - Updates the specific Delivery (if necessary) to an "approved" state (or updates the Order's state).
  - Updates the overarching `Order.status` to `COMPLETED`.
  - Triggers any relevant notifications or payment release logic.
  - Returns the updated `OrderDeliveryResponseDTO`.

### 2. Request Delivery Revision
- **Expected Route**: `POST /api/orders/delivery/<order_id>/<delivery_id>/revision`
- **Purpose**: Allows a client to reject a delivery and request a revision.
- **Expected Behavior**:
  - Validates that the client owns the order.
  - Transitions the `Order.status` to `REVISION`.
  - Potentially creates a `RevisionRequest` entity tying the request to the specific delivery.
  - Triggers a notification to the admin/writer.
  - Returns the updated `OrderDeliveryResponseDTO`.

## Missing Enum and Schema Updates

Currently, the backend's `DeliveryStatus` enum is limited to:
- `DELIVERED`
- `REVISED`
- `REDELIVERED`

Depending on the architecture chosen, you may need to either:
1. Extend `DeliveryStatus` to include `APPROVED` and `REVISION_REQUESTED` to strictly track the client's action on the specific delivery.
2. Rely entirely on `OrderStatus` and `RevisionRequest` models, in which case the API should return a new DTO parameter (e.g., `client_action: str`) so the frontend UI can correctly display whether a delivery was approved.

## Testing Needs
- Ensure unit and integration tests are added for both new client-facing routes.
- Validate that the order state correctly synchronizes with the delivery actions.
