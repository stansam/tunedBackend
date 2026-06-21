from marshmallow import Schema, fields, validate, post_load
from tuned.dtos.communication import CreateChatDTO, ChatMessageCreateDTO

class CreateChatSchema(Schema):
    subject = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    order_id = fields.UUID(required=False, allow_none=True)

    @post_load
    def make_dto(self, data, **kwargs):
        return CreateChatDTO(
            user_id="",
            subject=data.get("subject"),
            order_id=str(data.get("order_id")) if data.get("order_id") else None
        )

class SendMessageSchema(Schema):
    content = fields.String(required=True, validate=validate.Length(min=1, max=5000))

    @post_load
    def make_dto(self, data, **kwargs):
        return ChatMessageCreateDTO(
            chat_id="",
            user_id="",
            content=data["content"]
        )

class AssignAdminSchema(Schema):
    admin_id = fields.UUID(required=True)

class ChangeStatusSchema(Schema):
    status = fields.String(required=True, validate=validate.OneOf(["active", "closed"]))
