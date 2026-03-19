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
from tuned.client.schemas.payment import (
    PaymentFilterSchema,
    ManualPaymentConfirmationSchema,
    # InvoiceRequestSchema,
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
from tuned.client.schemas.settings import (
    UpdateProfileSchema,
    UpdateProfilePictureSchema,
    DeleteProfilePictureSchema,
    ChangeEmailSchema,
    ChangePasswordSchema,
    LanguagePreferenceSchema,
    DeleteProfilePictureSchema

    
)

# Settings - Newsletter schemas
from tuned.client.schemas.settings.newsletter import (
    NewsletterSubscribeSchema,
    NewsletterUnsubscribeSchema,
    NewsletterPreferencesSchema,
    NewsletterTokenSchema
)



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

# Deadline extension schemas
from tuned.client.schemas.deadline_extension import (
    CreateDeadlineExtensionRequestSchema,
    UpdateDeadlineExtensionRequestSchema,
    DeadlineExtensionFilterSchema
)
