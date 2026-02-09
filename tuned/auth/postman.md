# Auth Blueprint Postman Documentation

## Collection Variables

- `baseUrl`: `http://localhost:5000/api` (Adjust based on your environment)
- `accessToken`: `<JWT Access Token>`
- `refreshToken`: `<JWT Refresh Token>`

## Authentication Folders

### 1. Register

**Endpoint**: `POST {{baseUrl}}/auth/register`
**Description**: Register a new user account.
**Auth**: None

**Body (JSON)**:

```json
{
  "username": "newuser123",
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "confirm_password": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe",
  "gender": "male",
  "phone_number": "+1234567890" // Optional
}
```

**Responses**:

- `201 Created`: Registration successful.
- `400 Bad Request`: Validation error.
- `422 Unprocessable Entity`: Invalid data format.

---

### 2. Login

**Endpoint**: `POST {{baseUrl}}/auth/login`
**Description**: Authenticate user and receive JWT tokens.
**Auth**: None

**Body (JSON)**:

```json
{
  "email": "user@example.com", // Or username
  "password": "SecurePassword123!",
  "remember_me": true // Optional, default false
}
```

**Responses**:

- `200 OK`: Login successful. Returns `access_token`, `refresh_token`, and `user` data.
  - _Test Script_: `pm.environment.set("accessToken", pm.response.json().data.access_token); pm.environment.set("refreshToken", pm.response.json().data.refresh_token);`
- `401 Unauthorized`: Invalid credentials.
- `403 Forbidden`: Account locked or email not verified.

---

### 3. Logout

**Endpoint**: `POST {{baseUrl}}/auth/logout`
**Description**: Logout user and blacklist current token.
**Auth**: Bearer Token (`{{accessToken}}`)

**Responses**:

- `200 OK`: Logout successful.
- `401 Unauthorized`: Invalid or missing token.

---

### 4. Refresh Token

**Endpoint**: `POST {{baseUrl}}/auth/refresh`
**Description**: Refresh access token using a valid refresh token.
**Auth**: Bearer Token (`{{refreshToken}}`)

**Header**:

- `Authorization`: `Bearer {{refreshToken}}`

**Responses**:

- `200 OK`: Returns new `access_token`.
  - _Test Script_: `pm.environment.set("accessToken", pm.response.json().data.access_token);`
- `401 Unauthorized`: Invalid or expired refresh token.
- `403 Forbidden`: Account issue.

---

### 5. Verify Token

**Endpoint**: `GET {{baseUrl}}/auth/verify-token`
**Description**: Check if the current access token is valid.
**Auth**: Bearer Token (`{{accessToken}}`)

**Responses**:

- `200 OK`: Token is valid, returns user info.
- `401 Unauthorized`: Token invalid/expired.

---

### 6. Email Verification

**Endpoint**: `POST {{baseUrl}}/auth/verify-email`
**Description**: Verify email address with token received in email.
**Auth**: None

**Body (JSON)**:

```json
{
  "token": "<verification_token_from_email>"
}
```

**Responses**:

- `200 OK`: Email verified.
- `400 Bad Request`: Invalid/expired token.

---

### 7. Resend Verification

**Endpoint**: `POST {{baseUrl}}/auth/resend-verification`
**Description**: Resend email verification link.
**Auth**: None

**Body (JSON)**:

```json
{
  "email": "user@example.com"
}
```

**Responses**:

- `200 OK`: Email sent (or generic success).

---

### 8. Password Reset Request

**Endpoint**: `POST {{baseUrl}}/auth/password-reset/request`
**Description**: Request a password reset link.
**Auth**: None

**Body (JSON)**:

```json
{
  "email": "user@example.com"
}
```

**Responses**:

- `200 OK`: Email sent (or generic success).

---

### 9. Password Reset Confirm

**Endpoint**: `POST {{baseUrl}}/auth/password-reset/confirm`
**Description**: Reset password using token.
**Auth**: None

**Body (JSON)**:

```json
{
  "token": "<reset_token_from_email>",
  "new_password": "NewSecurePassword123!",
  "confirm_password": "NewSecurePassword123!"
}
```

**Responses**:

- `200 OK`: Password reset successful.
- `400 Bad Request`: Invalid/expired token.
