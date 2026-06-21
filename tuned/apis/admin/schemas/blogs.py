from marshmallow import Schema, fields, validate, post_load


class AdminBlogPostListRequestSchema(Schema):
    """Admin blog post list filter / pagination – mirrors BlogPostListRequestDTO."""
    q            = fields.Str(load_default=None, allow_none=True)
    category_id  = fields.Str(load_default=None, allow_none=True)
    is_published = fields.Bool(load_default=None, allow_none=True)
    page         = fields.Int(load_default=1, validate=validate.Range(min=1))
    per_page     = fields.Int(load_default=10, validate=validate.Range(min=1, max=100))
    sort         = fields.Str(load_default=None, allow_none=True)
    order        = fields.Str(load_default=None, allow_none=True,
                               validate=validate.OneOf(["asc", "desc"]))


class AdminCreateBlogPostSchema(Schema):
    """Validates the body for POST /admin/blogs/posts."""
    title             = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    content           = fields.Str(required=True, validate=validate.Length(min=1))
    author            = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    category_id       = fields.Str(required=True)
    excerpt           = fields.Str(load_default="")
    featured_image_id = fields.Str(load_default=None, allow_none=True)
    meta_description  = fields.Str(load_default="", validate=validate.Length(max=220))
    is_published      = fields.Bool(load_default=False)
    is_featured       = fields.Bool(load_default=False)
    tags              = fields.List(fields.Str(), load_default=list)


class AdminUpdateBlogPostSchema(Schema):
    """Validates the body for PATCH /admin/blogs/posts/<post_id> – all fields optional."""
    title             = fields.Str(validate=validate.Length(min=1, max=200))
    content           = fields.Str(validate=validate.Length(min=1))
    author            = fields.Str(validate=validate.Length(min=1, max=100))
    category_id       = fields.Str()
    excerpt           = fields.Str(validate=validate.Length(max=300))
    featured_image_id = fields.Str(allow_none=True)
    meta_description  = fields.Str(validate=validate.Length(max=220))
    is_published      = fields.Bool()
    is_featured       = fields.Bool()
    tags              = fields.List(fields.Str())


class AdminTogglePublishSchema(Schema):
    """Validates PATCH /admin/blogs/posts/<post_id>/publish."""
    is_published = fields.Bool(required=True)


class AdminToggleFeaturedSchema(Schema):
    """Validates PATCH /admin/blogs/posts/<post_id>/feature."""
    is_featured = fields.Bool(required=True)


class AdminCreateBlogCategorySchema(Schema):
    """Validates POST /admin/blogs/categories."""
    name        = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(load_default="")


class AdminUpdateBlogCategorySchema(Schema):
    """Validates PATCH /admin/blogs/categories/<category_id> – all fields optional."""
    name        = fields.Str(validate=validate.Length(min=1, max=100))
    description = fields.Str()


class AdminApproveCommentSchema(Schema):
    """Validates PATCH /admin/blogs/comments/<comment_id>/approve."""
    approved = fields.Bool(required=True)
