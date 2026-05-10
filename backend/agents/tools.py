import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from models.schemas import (
    UserProfile, TripPlan, Checklist, Item,
    ConversationMessage, CrowdType, TripType
)
from agents.prompts import (
    CHECKLIST_GENERATION_PROMPT,
    SCENE_RECOGNITION_PROMPT,
    COMPLETENESS_CHECK_PROMPT
)
from config import config


class MemoryStore:
    def __init__(self):
        self.user_profile: Optional[UserProfile] = None
        self.trip_history: list[TripPlan] = []
        self.current_trip: Optional[TripPlan] = None

    def load_user_profile(self, user_id: str = "default") -> UserProfile:
        if config.USER_PROFILES_PATH.exists():
            with open(config.USER_PROFILES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if user_id in data:
                    self.user_profile = UserProfile(**data[user_id])
                    return self.user_profile

        self.user_profile = UserProfile(user_id=user_id, name="用户")
        return self.user_profile

    def save_user_profile(self):
        if not self.user_profile:
            return

        data = {}
        if config.USER_PROFILES_PATH.exists():
            with open(config.USER_PROFILES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)

        data[self.user_profile.user_id] = self.user_profile.model_dump()
        with open(config.USER_PROFILES_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_trip_history(self) -> list[TripPlan]:
        if config.TRIP_HISTORY_PATH.exists():
            with open(config.TRIP_HISTORY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.trip_history = [TripPlan(**trip) for trip in data]
        return self.trip_history

    def save_trip_to_history(self, trip: TripPlan):
        self.trip_history.append(trip)
        data = [t.model_dump() for t in self.trip_history]
        with open(config.TRIP_HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_current_trip(self, trip: TripPlan):
        self.current_trip = trip
        data = trip.model_dump() if trip else None
        with open(config.CURRENT_TRIP_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_current_trip(self) -> Optional[TripPlan]:
        if config.CURRENT_TRIP_PATH.exists():
            with open(config.CURRENT_TRIP_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data:
                    self.current_trip = TripPlan(**data)
                    return self.current_trip
        return None


class ChecklistGenerator:
    def __init__(self, llm):
        self.llm = llm

    async def generate(
        self,
        destination: str,
        season: str,
        duration: int,
        crowd_type: str,
        trip_type: str,
        special_needs: list[str],
        user_profile: Optional[UserProfile] = None
    ) -> Checklist:
        if self.llm:
            forgotten_items = user_profile.get_forgotten_items() if user_profile else []
            health_info = user_profile.health_info if user_profile else []

            prompt = CHECKLIST_GENERATION_PROMPT.format(
                destination=destination,
                season=season,
                duration=duration,
                crowd_type=crowd_type,
                trip_type=trip_type,
                special_needs=", ".join(special_needs) if special_needs else "无",
                forgotten_items=", ".join(forgotten_items) if forgotten_items else "无",
                health_info=", ".join(health_info) if health_info else "无"
            )

            response = await self.llm.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)

            try:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                if json_start != -1 and json_end != 0:
                    json_str = content[json_start:json_end]
                    data = json.loads(json_str)
                    checklist = Checklist(**data)
                    return checklist
            except json.JSONDecodeError:
                pass

        return self._generate_scene_checklist(destination, season, duration, crowd_type, trip_type)

    def _generate_scene_checklist(self, destination: str, season: str, duration: int, crowd_type: str, trip_type: str) -> Checklist:
        items = []
        categories = ["证件", "衣物", "电子", "医药", "洗漱", "日用"]

        base_items = [
            Item(id=str(uuid.uuid4()), name="身份证", category="证件", reason="必备证件"),
            Item(id=str(uuid.uuid4()), name="手机", category="电子", reason="通讯工具"),
            Item(id=str(uuid.uuid4()), name="充电宝", category="电子", reason="续航保障"),
            Item(id=str(uuid.uuid4()), name="充电器", category="电子", reason="充电必备"),
            Item(id=str(uuid.uuid4()), name="换洗衣物", category="衣物", quantity=duration + 2, reason="每天换洗"),
            Item(id=str(uuid.uuid4()), name="内衣裤", category="衣物", quantity=duration + 1, reason="贴身衣物"),
            Item(id=str(uuid.uuid4()), name="袜子", category="衣物", quantity=duration + 1),
            Item(id=str(uuid.uuid4()), name="牙刷", category="洗漱", reason="个人卫生"),
            Item(id=str(uuid.uuid4()), name="牙膏", category="洗漱"),
            Item(id=str(uuid.uuid4()), name="毛巾", category="洗漱"),
            Item(id=str(uuid.uuid4()), name="护肤品", category="洗漱"),
            Item(id=str(uuid.uuid4()), name="常用药品", category="医药", reason="应急准备"),
            Item(id=str(uuid.uuid4()), name="创可贴", category="医药", reason="小伤口处理"),
            Item(id=str(uuid.uuid4()), name="口罩", category="日用"),
            Item(id=str(uuid.uuid4()), name="水杯", category="日用", reason="饮水必备"),
        ]

        items.extend(base_items)

        if "海" in destination or "岛" in destination or trip_type == "海岛度假":
            items.extend([
                Item(id=str(uuid.uuid4()), name="防晒霜SPF50+", category="洗漱", reason=f"{destination}紫外线强"),
                Item(id=str(uuid.uuid4()), name="泳衣", category="衣物", reason="海边必备"),
                Item(id=str(uuid.uuid4()), name="太阳镜", category="日用", reason="防晒护眼"),
                Item(id=str(uuid.uuid4()), name="遮阳帽", category="日用"),
                Item(id=str(uuid.uuid4()), name="防水手机袋", category="电子", reason="防水保护"),
                Item(id=str(uuid.uuid4()), name="沙滩鞋", category="衣物"),
            ])
            categories.append("海滩用品")

        if "山" in destination or "徒步" in destination or trip_type == "徒步登山":
            items.extend([
                Item(id=str(uuid.uuid4()), name="登山鞋", category="衣物", reason=f"{destination}徒步必备"),
                Item(id=str(uuid.uuid4()), name="冲锋衣", category="衣物", reason="防风防雨"),
                Item(id=str(uuid.uuid4()), name="登山杖", category="日用", reason="辅助登山"),
                Item(id=str(uuid.uuid4()), name="保温水壶", category="日用", reason="保温保冷"),
                Item(id=str(uuid.uuid4()), name="手套", category="衣物", reason="保护手部"),
            ])
            categories.append("户外装备")

        if season == "冬季" or "雪" in destination:
            items.extend([
                Item(id=str(uuid.uuid4()), name="羽绒服", category="衣物", reason=f"{destination}冬季保暖"),
                Item(id=str(uuid.uuid4()), name="保暖内衣", category="衣物", quantity=2),
                Item(id=str(uuid.uuid4()), name="围巾", category="衣物"),
                Item(id=str(uuid.uuid4()), name="手套", category="衣物"),
                Item(id=str(uuid.uuid4()), name="暖宝宝", category="日用", reason="保暖必备"),
            ])

        if season == "夏季":
            items.extend([
                Item(id=str(uuid.uuid4()), name="防晒霜", category="洗漱", reason="夏季防晒"),
                Item(id=str(uuid.uuid4()), name="遮阳伞", category="日用", reason="防晒防雨"),
                Item(id=str(uuid.uuid4()), name="清凉喷雾", category="日用"),
            ])

        if crowd_type == "家庭" or "孩子" in crowd_type:
            items.extend([
                Item(id=str(uuid.uuid4()), name="儿童防晒", category="洗漱", reason="儿童专用"),
                Item(id=str(uuid.uuid4()), name="儿童衣物", category="衣物", quantity=duration + 2),
                Item(id=str(uuid.uuid4()), name="玩具", category="日用", reason="孩子娱乐"),
                Item(id=str(uuid.uuid4()), name="零食", category="日用", reason="孩子加餐"),
            ])

        if crowd_type == "商务":
            items.extend([
                Item(id=str(uuid.uuid4()), name="正装", category="衣物", reason="商务场合"),
                Item(id=str(uuid.uuid4()), name="名片", category="日用", reason="商务交流"),
                Item(id=str(uuid.uuid4()), name="笔记本", category="电子", reason="会议记录"),
            ])

        return Checklist(
            checklist_id=str(uuid.uuid4()),
            trip_id="",
            items=items,
            categories=list(set(categories)),
            total_count=len(items)
        )

    def _generate_fallback_checklist(self, destination: str, duration: int) -> Checklist:
        items = [
            Item(id=str(uuid.uuid4()), name="身份证", category="证件", reason="必备证件"),
            Item(id=str(uuid.uuid4()), name="护照", category="证件", reason="出境必备"),
            Item(id=str(uuid.uuid4()), name="手机", category="电子", reason="通讯工具"),
            Item(id=str(uuid.uuid4()), name="充电宝", category="电子", reason="续航保障"),
            Item(id=str(uuid.uuid4()), name="换洗衣物", category="衣物", quantity=duration + 2, reason="每天换洗"),
            Item(id=str(uuid.uuid4()), name="洗漱用品", category="洗漱"),
            Item(id=str(uuid.uuid4()), name="常用药品", category="医药", reason="应急准备"),
        ]

        return Checklist(
            checklist_id=str(uuid.uuid4()),
            trip_id="",
            items=items,
            categories=["证件", "衣物", "电子", "医药", "洗漱"],
            total_count=len(items)
        )


class SceneRecognizer:
    def __init__(self, llm):
        self.llm = llm

    async def recognize(self, destination: str, season: str) -> dict:
        if self.llm:
            prompt = SCENE_RECOGNITION_PROMPT.format(
                destination=destination,
                season=season
            )

            response = await self.llm.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)

            try:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                if json_start != -1 and json_end != 0:
                    json_str = content[json_start:json_end]
                    return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        return self._fallback_recognition(destination)

    def _fallback_recognition(self, destination: str) -> dict:
        geo_features = []
        special_equipment = []

        beach_keywords = ["海", "岛", "滩", "滨", "马尔代夫", "普吉", "巴厘岛", "三亚"]
        mountain_keywords = ["山", "峰", "岭", "西藏", "登山", "徒步", "黄山"]

        for keyword in beach_keywords:
            if keyword in destination:
                geo_features.append("海岛")
                special_equipment.extend(["防晒霜", "泳衣", "防水袋"])
                break

        for keyword in mountain_keywords:
            if keyword in destination:
                geo_features.append("山地")
                special_equipment.extend(["登山鞋", "冲锋衣", "保温水壶"])
                break

        if not geo_features:
            geo_features.append("城市")

        return {
            "geo_features": geo_features,
            "climate_type": "温带",
            "travel_themes": ["观光"],
            "special_equipment": special_equipment,
            "tips": [f"祝你在{destination}旅途愉快！"]
        }


class CompletenessChecker:
    def __init__(self, llm):
        self.llm = llm

    async def check(
        self,
        checklist: Checklist,
        destination: str,
        season: str,
        duration: int,
        crowd_type: str,
        trip_type: str,
        user_profile: Optional[UserProfile] = None
    ) -> dict:
        if self.llm:
            forgotten_items = user_profile.get_forgotten_items() if user_profile else []
            health_info = user_profile.health_info if user_profile else []

            prompt = COMPLETENESS_CHECK_PROMPT.format(
                current_checklist=json.dumps(checklist.model_dump(), ensure_ascii=False),
                destination=destination,
                season=season,
                duration=duration,
                crowd_type=crowd_type,
                trip_type=trip_type,
                forgotten_items=", ".join(forgotten_items) if forgotten_items else "无",
                health_info=", ".join(health_info) if health_info else "无"
            )

            response = await self.llm.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)

            try:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                if json_start != -1 and json_end != 0:
                    json_str = content[json_start:json_end]
                    return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        return self._fallback_check(checklist, destination, season, crowd_type)

    def _fallback_check(self, checklist: Checklist, destination: str, season: str, crowd_type: str) -> dict:
        suggested_items = []
        existing_items = [item.name for item in checklist.items]

        if "海" in destination or "岛" in destination:
            beach_items = ["防晒霜", "泳衣", "太阳镜"]
            for item in beach_items:
                if item not in existing_items:
                    suggested_items.append({
                        "name": item,
                        "category": "洗漱" if item == "防晒霜" else "衣物" if item == "泳衣" else "日用",
                        "reason": f"{destination}海边必备",
                        "priority": "high"
                    })

        if "山" in destination or "徒步" in destination:
            hiking_items = ["登山鞋", "冲锋衣", "登山杖"]
            for item in hiking_items:
                if item not in existing_items:
                    suggested_items.append({
                        "name": item,
                        "category": "衣物" if item in ["登山鞋", "冲锋衣"] else "日用",
                        "reason": f"{destination}徒步必备",
                        "priority": "high"
                    })

        if season == "冬季":
            winter_items = ["羽绒服", "保暖内衣", "手套"]
            for item in winter_items:
                if item not in existing_items:
                    suggested_items.append({
                        "name": item,
                        "category": "衣物",
                        "reason": f"{destination}冬季保暖",
                        "priority": "high"
                    })

        if season == "夏季":
            summer_items = ["防晒霜", "遮阳伞"]
            for item in summer_items:
                if item not in existing_items:
                    suggested_items.append({
                        "name": item,
                        "category": "洗漱" if item == "防晒霜" else "日用",
                        "reason": f"{destination}夏季防晒",
                        "priority": "medium"
                    })

        if crowd_type == "家庭":
            family_items = ["儿童防晒", "玩具", "零食"]
            for item in family_items:
                if item not in existing_items:
                    suggested_items.append({
                        "name": item,
                        "category": "洗漱" if item == "儿童防晒" else "日用",
                        "reason": "家庭出游必备",
                        "priority": "medium"
                    })

        completeness_score = min(1.0, 0.7 + len(suggested_items) * 0.05)

        return {
            "missing_categories": [],
            "suggested_items": suggested_items[:5],
            "warnings": ["检查完成"],
            "completeness_score": round(completeness_score, 2)
        }


def create_tools(llm):
    memory_store = MemoryStore()
    checklist_generator = ChecklistGenerator(llm)
    scene_recognizer = SceneRecognizer(llm)
    completeness_checker = CompletenessChecker(llm)

    return {
        "memory_store": memory_store,
        "checklist_generator": checklist_generator,
        "scene_recognizer": scene_recognizer,
        "completeness_checker": completeness_checker
    }
