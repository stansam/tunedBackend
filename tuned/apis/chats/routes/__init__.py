from tuned.apis.chats.routes.chats import (
    ListClientChatsView, CreateChatView, GetChatDetailsView, SendMessageView,
    MarkChatReadView, AdminListChatsView, AdminAssignView, AdminStatusView,
    AdminListAgentsView, EditMessageView, DeleteMessageView, UploadAttachmentView,
    GetChatMessagesView
)

CHAT_ROUTES = [
    {"url_rule": "", "view_func": ListClientChatsView.as_view("list_chats"), "methods": ["GET"]},
    {"url_rule": "", "view_func": CreateChatView.as_view("create_chat"), "methods": ["POST"]},
    {"url_rule": "/<string:chat_id>", "view_func": GetChatDetailsView.as_view("chat_details"), "methods": ["GET"]},
    {"url_rule": "/<string:chat_id>/messages", "view_func": SendMessageView.as_view("send_message"), "methods": ["POST"]},
    {"url_rule": "/<string:chat_id>/messages", "view_func": GetChatMessagesView.as_view("get_messages"), "methods": ["GET"]},
    {"url_rule": "/<string:chat_id>/read", "view_func": MarkChatReadView.as_view("mark_read"), "methods": ["POST"]},
    {"url_rule": "/admin", "view_func": AdminListChatsView.as_view("admin_list_chats"), "methods": ["GET"]},
    {"url_rule": "/admin/<string:chat_id>/assign", "view_func": AdminAssignView.as_view("admin_assign"), "methods": ["PATCH"]},
    {"url_rule": "/admin/<string:chat_id>/status", "view_func": AdminStatusView.as_view("admin_status"), "methods": ["PATCH"]},
    {"url_rule": "/admin/agents", "view_func": AdminListAgentsView.as_view("admin_list_agents"), "methods": ["GET"]},
    {"url_rule": "/<string:chat_id>/messages/<string:message_id>", "view_func": EditMessageView.as_view("edit_message"), "methods": ["PATCH"]},
    {"url_rule": "/<string:chat_id>/messages/<string:message_id>", "view_func": DeleteMessageView.as_view("delete_message"), "methods": ["DELETE"]},
    {"url_rule": "/<string:chat_id>/attachments", "view_func": UploadAttachmentView.as_view("upload_attachment"), "methods": ["POST"]}
]
