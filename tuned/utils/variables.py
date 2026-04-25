class Variables:
    USER_LOGIN_ACTION = "user_login"
    USER_REGISTER_ACTION = "user_register"
    USER_ENTITY_TYPE = "User"
    EMAIL_VERIFICATION_ACTION = "email_verification"
    USER_UPDATE_ACTION = "user_update"
    PASSWORD_CHANGE_ACTION = "password_change"
    AVATAR_UPDATE_ACTION = "avatar_upload"
    AVATAR_DELETE_ACTION = "avatar_delete"
    
    PAYMENT_CREATE_ACTION = "payment_create"
    PAYMENT_UPDATE_ACTION = "payment_update"
    INVOICE_CREATE_ACTION = "invoice_create"
    INVOICE_UPDATE_ACTION = "invoice_update"
    DISCOUNT_CREATE_ACTION = "discount_create"
    DISCOUNT_UPDATE_ACTION = "discount_update"
    DISCOUNT_APPLY_ACTION = "discount_apply"
    REFUND_CREATE_ACTION = "refund_create"
    REFUND_UPDATE_ACTION = "refund_update"
    TRANSACTION_CREATE_ACTION = "transaction_create"
    
    ACCEPTED_METHOD_CREATE_ACTION = "accepted_method_create"
    ACCEPTED_METHOD_UPDATE_ACTION = "accepted_method_update"
    
    PAYMENT_ENTITY_TYPE = "Payment"
    INVOICE_ENTITY_TYPE = "Invoice"
    DISCOUNT_ENTITY_TYPE = "Discount"
    REFUND_ENTITY_TYPE = "Refund"
    TRANSACTION_ENTITY_TYPE = "Transaction"

    ENTITY_TYPE_REFERRAL = "Referral"
    REFERRAL_SIGNUP_ACTION = "referral_signup"
    REFERRAL_POINTS_EARNED_ACTION = "referral_points_earned"

    OK = "ok"
    NOT_FOUND = "not_found"
    ALREADY_VERIFIED = "already_verified"

    PRODUCTION = "production"
    DEVELOPMENT = "development"
    # ALREADY_EXISTS = "already_exists"
    # INVALID = "invalid"
    # NO_TOKEN = "no_token"
    
    