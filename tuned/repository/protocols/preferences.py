from typing import Protocol, TYPE_CHECKING, runtime_checkable

if TYPE_CHECKING:
    from tuned.dtos import AllPreferencesResponseDTO, PreferenceUpdateDTO, PreferenceResponseDTO

@runtime_checkable
class PreferenceRepositoryProtocol(Protocol):
    def get_all_preferences(self, user_id: str) -> "AllPreferencesResponseDTO": ...
    def update_category(
        self,
        category: str,
        user_id: str,
        data: "PreferenceUpdateDTO",
    ) -> "PreferenceResponseDTO": ...
    def save(self) -> None: ...
    def rollback(self) -> None: ...
