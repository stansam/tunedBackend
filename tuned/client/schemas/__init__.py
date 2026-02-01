"""
Client validation schemas package.

This module exports all validation schemas used in the client blueprint
for easy import and usage throughout the application.
"""

# Order schemas
from tuned.client.schemas.order import (
    CreateOrderSchema,
    OrderFilterSchema,
    OrderCommentSchema,
    UpdateOrderCommentSchema,
    ExtendDeadlineSchema,
    RequestRevisionSchema,
    SupportTicketSchema,
    AcceptDeliverySchema,
    FileUploadSchema
)

# Payment schemas
from tuned.client.schemas.payment_schemas import (
    PaymentFilterSchema,
    PaymentConfirmationSchema,
    InvoiceRequestSchema,
    PayPalPaymentSchema,
    BraintreePaymentSchema,
    InvoiceDownloadSchema,
    PaymentReceiptSchema,
    RefundRequestSchema,
    DiscountCodeSchema,
    PaymentMethodSchema,
    TransactionFilterSchema
)

# Referral schemas
from tuned.client.schemas.referral import (
    ReferralCodeSchema,
    ApplyReferralCodeSchema,
    RedeemRewardSchema,
    ReferralFilterSchema,
    ReferralEarningsSchema,
    WithdrawReferralEarningsSchema,
    ReferralShareSchema,
    RewardPointsTransferSchema,
    ReferralStatsFilterSchema
)

# Settings - Profile schemas
from tuned.client.schemas.settings.profile import (
    UpdateProfileSchema,
    UpdateProfilePictureSchema,
    DeleteProfilePictureSchema,
    NotificationPreferencesSchema,
    PrivacySettingsSchema,
    LanguagePreferenceSchema,
    EmailPreferencesSchema
)

# Settings - Newsletter schemas
from tuned.client.schemas.settings.newsletter import (
    NewsletterSubscribeSchema,
    NewsletterUnsubscribeSchema,
    NewsletterPreferencesSchema,
    NewsletterTokenSchema
)

# Settings - Existing schemas (for backwards compatibility)
try:
    from tuned.client.schemas.settings.profile.change_password import ChangePasswordSchema
    from tuned.client.schemas.settings.profile.change_email import ChangeEmailSchema
except ImportError:
    ChangePasswordSchema = None
    ChangeEmailSchema = None


__all__ = [
    # Order schemas
    'CreateOrderSchema',
    'OrderFilterSchema',
    'OrderCommentSchema',
    'UpdateOrderCommentSchema',
    'ExtendDeadlineSchema',
    'RequestRevisionSchema',
    'SupportTicketSchema',
    'AcceptDeliverySchema',
    'FileUploadSchema',
    
    # Payment schemas
    'PaymentFilterSchema',
    'ManualPaymentConfirmationSchema',
    'PayPalPaymentSchema',
    'BraintreePaymentSchema',
    'InvoiceDownloadSchema',
    'PaymentReceiptSchema',
    'RefundRequestSchema',
    'DiscountCodeSchema',
    'PaymentMethodSchema',
    'TransactionFilterSchema',
    
    # Referral schemas
    'ReferralCodeSchema',
    'ApplyReferralCodeSchema',
    'RedeemRewardSchema',
    'ReferralFilterSchema',
    'ReferralEarningsSchema',
    'WithdrawReferralEarningsSchema',
    'ReferralShareSchema',
    'RewardPointsTransferSchema',
    'ReferralStatsFilterSchema',
    
    # Settings schemas
    'UpdateProfileSchema',
    'UpdateProfilePictureSchema',
    'DeleteProfilePictureSchema',
    'NotificationPreferencesSchema',
    'PrivacySettingsSchema',
    'LanguagePreferenceSchema',
    'EmailPreferencesSchema',
    'NewsletterSubscribeSchema',
    'NewsletterUnsubscribeSchema',
    'NewsletterPreferencesSchema',
    'NewsletterTokenSchema',
    'ChangePasswordSchema',
    'ChangeEmailSchema',
]

# Revision request schemas
from tuned.client.schemas.revision_request import (
    CreateRevisionRequestSchema,
    UpdateRevisionRequestSchema,
    RevisionRequestFilterSchema
)
