# Tuned — Database Management CLI Reference

This document describes all Flask CLI commands available under the `manage/` blueprint for seeding data, inspecting the database, and managing table contents.

---

## Quick Start

```bash
# Export your Flask app entry point (adjust to match your setup)
export FLASK_APP=run:app

# Full database seed (all models, in dependency order)
flask seed-db

# Create a superuser admin account (interactive prompts)
flask createsuperuser
```

---

## Seed Commands

All seed commands are **idempotent**: existing records are skipped rather than duplicated.

### Dependency Order

The commands have the following dependency chain. Running them out of order will produce "not found" warnings for FK references.

```
Users → Content → Prices → Services → Samples → Testimonials → FAQs → Blogs
```

---

### `flask createsuperuser`

Interactively creates an admin user account.

```bash
flask createsuperuser
# Prompts for: --username, --first-name, --last-name, --email, --password
```

---

### `flask create-users`

Seeds sample client accounts from `manage/data/users.py`.

```bash
flask create-users
```

**Seed data:** 2 sample users (johndoe, janedoe) with verified emails.

---

### `flask create-content`

Seeds **academic levels** and **deadlines** from `manage/data/content.py`.

```bash
flask create-content
```

**Seed data:**

- 6 academic levels: High School → Professional
- 10 deadlines: 3 Hours → 20 Days

---

### `flask create-prices`

Seeds **pricing categories** and the full **price rate matrix** from `manage/data/price.py`.

Requires: `create-content` must have been run first.

```bash
flask create-prices
```

**Seed data:**

- 4 pricing categories: Writing, Proofreading & Editing, Technical & Calculations, Humanizing AI
- 240 price rates (4 categories × 10 deadlines × 6 academic levels)

---

### `flask create-services`

Seeds **service categories** and all **individual services** from `manage/data/services.py`.

Requires: `create-prices` must have been run first.

```bash
flask create-services
```

**Seed data:**

- 7 service categories
- 44+ individual services (Essays, SPSS, Business Plans, etc.)

---

### `flask create-samples`

Seeds writing **samples** with tags from `manage/data/samples.py`.

Requires: `create-services` must have been run first.

```bash
flask create-samples
```

**Seed data:** 6 samples across Essays, Copyediting, SPSS, Business Plans, Literature Review, and PowerPoint Presentations.

Tags are applied via `Tag.parse_tags()` (comma-separated string → many-to-many relationship).

---

### `flask create-testimonials`

Seeds approved client **testimonials** from `manage/data/testimonials.py`.

Requires: `create-users` and `create-services` must have been run first.

```bash
flask create-testimonials
```

**Seed data:** 6 approved testimonials across various services.

> **Note:** Testimonials are seeded without `order_id` (set to `None`) since no real orders exist in a freshly seeded database.

---

### `flask create-faqs`

Seeds **FAQ** entries from `manage/data/faqs.py`.

```bash
flask create-faqs
```

**Seed data:** 11 FAQs across 5 categories: Ordering, Pricing, Communication, Revisions, Quality & Safety.

---

### `flask create-blogs`

Seeds **blog categories**, **blog posts** (published + draft), and their tags from `manage/data/blogs.py`.

```bash
flask create-blogs
```

**Seed data:**

- 4 blog categories with Unsplash cover images
- 6 blog posts (5 published, 1 draft) with Unsplash featured images and tags

Tags are applied via `Tag.parse_tags()`.

---

### `flask seed-db`

Runs **all seed commands in the correct dependency order** in a single command.

```bash
flask seed-db
```

Steps run:

1. `create-users`
2. `create-content`
3. `create-prices`
4. `create-services`
5. `create-samples`
6. `create-testimonials`
7. `create-faqs`
8. `create-blogs`

If a step fails, the seeder logs the error and continues with remaining steps.

---

## Table Management

### `flask manage-tables`

Inspect and manage database table contents.

#### List all tables with row counts

```bash
flask manage-tables --list
```

#### Empty a single table

```bash
flask manage-tables --empty faq
# Prompts for confirmation unless --yes is passed
flask manage-tables --empty faq --yes
```

#### Empty all seed tables

Empties all seed-related tables in FK-safe order (association tables first, then models).

```bash
flask manage-tables --empty-all
# Prompts for confirmation unless --yes is passed
flask manage-tables --empty-all --yes
```

> **Warning:** `--empty-all` uses `DELETE` (not `TRUNCATE`) to respect foreign key constraints. It targets the following tables in order: `blog_post_tags`, `sample_tags`, `service_tags`, `blog_comment`, `comment_reaction`, `blog_post`, `blog_category`, `faq`, `testimonial`, `sample`, `service`, `service_category`, `price_rate`, `pricing_category`, `deadline`, `academic_level`, `users`, `tag`.

#### Options summary

| Option          | Description                          |
| --------------- | ------------------------------------ |
| `--list`        | Print all table names + row counts   |
| `--empty TABLE` | Delete all rows from `TABLE`         |
| `--empty-all`   | Delete all rows from all seed tables |
| `--yes` / `-y`  | Skip confirmation prompts            |

---

## Data Files

| File                          | Contents                                                  |
| ----------------------------- | --------------------------------------------------------- |
| `manage/data/users.py`        | Sample client user accounts                               |
| `manage/data/content.py`      | Academic levels + deadline options                        |
| `manage/data/price.py`        | Pricing categories + price rate matrix                    |
| `manage/data/services.py`     | Service categories, services, pricing category mappings   |
| `manage/data/samples.py`      | Writing samples with Unsplash images + tags               |
| `manage/data/testimonials.py` | Client testimonials (self-contained, no live object refs) |
| `manage/data/faqs.py`         | Frequently asked questions with categories                |
| `manage/data/blogs.py`        | Blog categories + posts with Unsplash images + tags       |

---

## Notes

- All seed commands use the **service layer** — no direct database operations.
- **Tags** are handled via `Tag.parse_tags(tag_string)` which calls `Tag.get_or_create()` for each tag name.
- All **image URLs** use [Unsplash](https://unsplash.com) source links with explicit size parameters (`?w=800&q=80`).
- Commands respect `AlreadyExists` exceptions to enable safe **re-runs** without duplicates.
