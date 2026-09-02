"""Push notification provider abstraction (mock).

Real push delivery (FCM/APNs) would implement the same interface.
Every push is also persisted via ``NotificationService`` so the mobile
app always has an in-app notification feed even if a push is missed.
"""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("saveup.push")


class PushProvider(ABC):
    @abstractmethod
    def send(self, user_id: str, title: str, body: str) -> bool:
        ...


class MockPushProvider(PushProvider):
    def send(self, user_id: str, title: str, body: str) -> bool:
        logger.info("[MOCK PUSH] user=%s title=%s body=%s", user_id, title, body)
        return True


push_provider: PushProvider = MockPushProvider()
