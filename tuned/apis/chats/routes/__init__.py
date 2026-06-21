from tuned.apis.chats.routes.chats import (
    ListClientChatsView, CreateChatView, GetChatDetailsView, SendMessageView,
    MarkChatReadView, AdminListChatsView, AdminAssignView, AdminStatusView
)

CHAT_ROUTES = [
    {"url_rule": "", "view_func": ListClientChatsView.as_view("list_chats"), "methods": ["GET"]},
    {"url_rule": "", "view_func": CreateChatView.as_view("create_chat"), "methods": ["POST"]},
    {"url_rule": "/<string:chat_id>", "view_func": GetChatDetailsView.as_view("chat_details"), "methods": ["GET"]},
    {"url_rule": "/<string:chat_id>/messages", "view_func": SendMessageView.as_view("send_message"), "methods": ["POST"]},
    {"url_rule": "/<string:chat_id>/read", "view_func": MarkChatReadView.as_view("mark_read"), "methods": ["POST"]},
    {"url_rule": "/admin", "view_func": AdminListChatsView.as_view("admin_list_chats"), "methods": ["GET"]},
    {"url_rule": "/admin/<string:chat_id>/assign", "view_func": AdminAssignView.as_view("admin_assign"), "methods": ["PATCH"]},
    {"url_rule": "/admin/<string:chat_id>/status", "view_func": AdminStatusView.as_view("admin_status"), "methods": ["PATCH"]}
]
