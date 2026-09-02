"""SMS provider abstraction.

``MockSMSProvider`` just logs the message -- swap in a real provider
(Twilio, MSG91, etc.) by implementing the same interface and wiring it
up in place of ``MockSMSProvider`` where it's constructed.
"""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("saveup.sms")


class SMSProvider(ABC):
    @abstractmethod
    def send(self, phone_number: str, message: str) -> bool:
        """Returns True if the message was accepted for delivery."""


class MockSMSProvider(SMSProvider):
    def send(self, phone_number: str, message: str) -> bool:
        logger.info("[MOCK SMS] to=%s message=%s", phone_number, message)
        return True


sms_provider: SMSProvider = MockSMSProvider()
