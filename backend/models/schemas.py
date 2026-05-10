from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum

class CrowdType(str, Enum):
    SOLO = "独自"
    COUPLE = "情侣"
    FAMILY = "家庭"
    FRIENDS = "朋友"
    BUSINESS = "商务"
    GROUP = "团队"

class TripType(str, Enum):
    BEACH = "海岛度假"
    MOUNTAIN = "徒步登山"
    CITY = "城市观光"
    CULTURE = "文化体验"
    BUSINESS = "商务出差"
    ROAD_TRIP = "自驾游"
    CRUISE = "邮轮"
    THEME_PARK = "主题乐园"

class Season(str, Enum):
    SPRING = "春季"
    SUMMER = "夏季"
    AUTUMN = "秋季"
    WINTER = "冬季"

class Item(BaseModel):
    id: str
    name: str
    category: str
    quantity: int = 1
    packed: bool = False
    is_essential: bool = True
    reason: str = ""
    source: Literal["template", "habit", "ai_suggestion"] = "template"

class Checklist(BaseModel):
    checklist_id: str
    trip_id: str
    items: list[Item] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    total_count: int = 0
    packed_count: int = 0
    completeness_score: float = 0.0

class TripPlan(BaseModel):
    trip_id: str
    destination: str
    duration: int
    season: str
    crowd_type: CrowdType
    trip_type: TripType
    start_date: Optional[str] = None
    special_needs: list[str] = Field(default_factory=list)
    checklist: Optional[Checklist] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class UserProfile(BaseModel):
    user_id: str
    name: str = "用户"
    frequent_destinations: list[str] = Field(default_factory=list)
    preferred_season: str = "春季"
    travel_frequency: str = "偶尔"
    habits: dict = Field(default_factory=dict)
    health_info: list[str] = Field(default_factory=list)
    family_members: list[str] = Field(default_factory=list)
    pets: list[str] = Field(default_factory=list)
    feedback_history: list[dict] = Field(default_factory=list)
    food_preferences: list[str] = Field(default_factory=list)

    def get_forgotten_items(self) -> list[str]:
        return self.habits.get("always_forget", [])

    def add_forgotten_item(self, item: str):
        if "always_forget" not in self.habits:
            self.habits["always_forget"] = []
        if item not in self.habits["always_forget"]:
            self.habits["always_forget"].append(item)

class ConversationMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class AgentState(BaseModel):
    messages: list[ConversationMessage] = Field(default_factory=list)
    current_trip: Optional[TripPlan] = None
    user_profile: Optional[UserProfile] = None
    context: dict = Field(default_factory=dict)
