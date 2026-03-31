from .layout import LayoutBuilderMixin
from .auth import AuthBuilderMixin
from .tabs import TabsBuilderMixin
from .discord import DiscordBuilderMixin
from .discord_schedule import DiscordScheduleBuilderMixin
from .preview import PreviewBuilderMixin
from .interactions import InteractionsBuilderMixin

class UISetupMixin(
    LayoutBuilderMixin,
    AuthBuilderMixin,
    TabsBuilderMixin,
    DiscordBuilderMixin,
    DiscordScheduleBuilderMixin,
    PreviewBuilderMixin,
    InteractionsBuilderMixin
):
    """
    Combined mixin for building the application UI layout.
    Ensures that methods like _build_dj_roster_tab (from TabsBuilderMixin)
    are accessible to the main App class.
    """
    pass