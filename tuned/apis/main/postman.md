# Main Blueprint Postman Documentation

## Collection Variables

- `baseUrl`: `http://localhost:5000/api` (Adjust based on your environment)

## Homepage Folders

### 1. Global Search

**Endpoint**: `GET {{baseUrl}}/search`
**Description**: Search across services, samples, blogs, FAQs, and tags.
**Params**:

- `q`: Search query (Required, min 2 chars)
- `type`: Filter by type (Optional: `all`, `service`, `sample`, `blog`, `faq`, `tag`. Default: `all`)
- `page`: Page number (Optional, default 1)
- `per_page`: Items per page (Optional, default 20)

**Responses**:

- `200 OK`: Search results with pagination and counts.
- `400 Bad Request`: Validation error.

---

### 2. Newsletter Subscribe

**Endpoint**: `POST {{baseUrl}}/newsletter/subscribe`
**Description**: Subscribe to newsletter.
**Body (JSON)**:

```json
{
  "email": "user@example.com",
  "name": "John Doe" // Optional
}
```

**Responses**:

- `201 Created`: Subscription successful.
- `200 OK`: Resubscribed successfully.
- `400 Bad Request`: Validation error.
- `409 Conflict`: Email already exists (checked via integrity error, but logic handles existing active users with 200).

---

### 3. Quote Form Options

**Endpoint**: `GET {{baseUrl}}/quote-form/options`
**Description**: Get all options for populating quote form dropdowns.
**Responses**:

- `200 OK`: Returns services, academic levels, deadlines, and pricing categories.

---

### 4. Testimonials

**Endpoint**: `GET {{baseUrl}}/testimonials`
**Description**: Get approved testimonials.
**Params**:

- `service_id`: Filter by service ID (Optional)
- `page`: Page number (Optional, default 1)
- `per_page`: Items per page (Optional, default 10)

**Responses**:

- `200 OK`: List of testimonials.

---

### 5. Featured Content

**Endpoint**: `GET {{baseUrl}}/featured`
**Description**: Get featured content for homepage (services, samples, blogs).
**Responses**:

- `200 OK`: Featured content data.

## Services Folders

### 1. List Services

**Endpoint**: `GET {{baseUrl}}/services`
**Description**: List all services with filtering.
**Params**:

- `category_id`: Filter by category ID (Optional)
- `featured`: Filter by featured status (Optional: `true` or `false`)
- `is_active`: Filter by active status (Optional, default `true`)
- `q`: Search query (Optional)
- `sort`: Sort field (`name`, `created_at`, `category`. Default: `name`)
- `order`: Sort order (`asc`, `desc`. Default: `asc`)
- `page`: Page number (Optional)
- `per_page`: Items per page (Optional)

**Responses**:

- `200 OK`: Paginated list of services.

---

### 2. Get Service Details

**Endpoint**: `GET {{baseUrl}}/services/<slug>`
**Description**: Get service details by slug.
**Responses**:

- `200 OK`: Service details with related samples.
- `404 Not Found`: Service not found.

## Samples Folders

### 1. List Samples

**Endpoint**: `GET {{baseUrl}}/samples`
**Description**: List all samples with filtering.
**Params**:

- `service_id`: Filter by service ID (Optional)
- `featured`: Filter by featured status (Optional: `true` or `false`)
- `q`: Search query (Optional)
- `sort`: Sort field (`created_at`, `word_count`, `title`. Default: `created_at`)
- `order`: Sort order (`asc`, `desc`. Default: `desc`)
- `page`: Page number (Optional)
- `per_page`: Items per page (Optional)

**Responses**:

- `200 OK`: Paginated list of samples.

---

### 2. Get Sample Details

**Endpoint**: `GET {{baseUrl}}/samples/<slug>`
**Description**: Get sample details by slug.
**Responses**:

- `200 OK`: Sample details with related samples.
- `404 Not Found`: Sample not found.

## Blogs Folders

### 1. List Blogs

**Endpoint**: `GET {{baseUrl}}/blogs`
**Description**: List published blog posts.
**Params**:

- `category_id`: Filter by category ID (Optional)
- `q`: Search query (Optional)
- `sort`: Sort field (`published_at`, `created_at`, `title`. Default: `published_at`)
- `order`: Sort order (`asc`, `desc`. Default: `desc`)
- `page`: Page number (Optional)
- `per_page`: Items per page (Optional)

**Responses**:

- `200 OK`: Paginated list of blog posts.

---

### 2. Get Blog Details

**Endpoint**: `GET {{baseUrl}}/blogs/<slug>`
**Description**: Get blog post details by slug.
**Responses**:

- `200 OK`: Blog post details with related posts.
- `404 Not Found`: Blog post not found.

---

### 3. Get Blog Comments

**Endpoint**: `GET {{baseUrl}}/blogs/<slug>/comments`
**Description**: Get approved comments for a blog post.
**Params**:

- `page`: Page number (Optional)
- `per_page`: Items per page (Optional)

**Responses**:

- `200 OK`: Paginated list of comments.
- `404 Not Found`: Blog post not found.

---

### 4. Add Blog Comment

**Endpoint**: `POST {{baseUrl}}/blogs/<slug>/comments`
**Description**: Add a comment to a blog post.
**Body (JSON)**:

```json
{
  "content": "This is a great post!",
  "name": "Guest User", // Required if not authenticated
  "email": "guest@example.com" // Required if not authenticated
}
```

_Note: If authenticated (Bearer Token), name and email are optional and comment is auto-approved. Otherwise, it requires approval._

**Responses**:

- `201 Created`: Comment added/submitted.
- `404 Not Found`: Blog post not found.
- `400 Bad Request`: Validation error.

---

### 5. React to Comment

**Endpoint**: `POST {{baseUrl}}/blogs/comments/<comment_id>/react`
**Description**: Like or dislike a comment.
**Body (JSON)**:

```json
{
  "reaction_type": "like" // or "dislike"
}
```

**Responses**:

- `200 OK`: Reaction added/updated/removed.
- `404 Not Found`: Comment not found.
