from tuned.models.enums import MethodCategory
from typing import TypedDict

class AcceptedMethodData(TypedDict):
    name: str
    category: MethodCategory
    details: str
    is_active: bool
    
accepted_methods_list: list[AcceptedMethodData] = [
    {
        "name": "Card Payment (Pesapal)",
        "category": MethodCategory.CREDIT_CARD,
        "details": "Pay securely using your Credit/Debit Card or Mobile Money via Pesapal.",
        "is_active": True,
    },
    {
        "name": "Direct Bank Transfer",
        "category": MethodCategory.BANK_TRANSFER,
        "details": "Please transfer the total amount to the following bank account:\nBank: Tuned Bank\nAccount Name: Tuned Essays Ltd\nAccount Number: 1234-5678-9012\nRouting Number/BIC: TUNEDUS33\nReference: Use your Order Number (e.g. ORD-202605-00001)",
        "is_active": True,
    },
    {
        "name": "M-Pesa / Mobile Wallet",
        "category": MethodCategory.DIGITAL_WALLET,
        "details": "Please send payment to our Paybill number:\nBusiness Number: 555666\nAccount Number: [Your Order Number]",
        "is_active": True,
    },
]
