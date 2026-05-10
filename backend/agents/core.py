import json
import uuid
import re
import os
from datetime import datetime
from typing import Optional

from models.schemas import (
    UserProfile, TripPlan, Checklist, Item,
    ConversationMessage, CrowdType, TripType, AgentState
)
from agents.prompts import (
    SYSTEM_PROMPT,
    INTENT_RECOGNITION_PROMPT,
    CHECKLIST_GENERATION_PROMPT
)
from agents.tools import create_tools, MemoryStore
from config import config


class DashScopeResponse:
    def __init__(self, response):
        self.response = response
        self.content = response.output['text'] if response.output else ""


class DashScopeLLM:
    def __init__(self, model_name: str = "qwen-plus"):
        import dashscope
        api_key = config.DASHSCOPE_API_KEY or os.getenv("DASHSCOPE_API_KEY", "")
        if api_key:
            dashscope.api_key = api_key
        self.model_name = model_name
        self.has_api_key = bool(api_key)

    async def ainvoke(self, prompt: str) -> DashScopeResponse:
        from dashscope import Generation
        try:
            response = Generation.call(
                model=self.model_name,
                prompt=prompt
            )
            return DashScopeResponse(response)
        except Exception as e:
            print(f"DashScope API error: {e}")
            return DashScopeResponse(None)


class TravelAgent:
    def __init__(self, use_mock=False):
        self.use_mock = use_mock or config.LLM_PROVIDER == "mock"
        if config.LLM_PROVIDER == "mock":
            self.use_mock = True

        self.llm = None
        if not self.use_mock:
            if config.LLM_PROVIDER == "dashscope":
                self.llm = DashScopeLLM(model_name=config.MODEL_NAME)
                if not self.llm.has_api_key:
                    print("Warning: No DashScope API Key configured, falling back to mock mode")
                    self.use_mock = True
                    self.llm = None
            else:
                raise ValueError(f"Unsupported LLM provider: {config.LLM_PROVIDER}")

        self.tools = create_tools(self.llm if self.llm else None)
        self.memory_store: MemoryStore = self.tools["memory_store"]
        self.checklist_generator = self.tools["checklist_generator"]
        self.scene_recognizer = self.tools["scene_recognizer"]
        self.completeness_checker = self.tools["completeness_checker"]
        self.conversation_history: list[ConversationMessage] = []

    async def initialize(self, user_id: str = "default"):
        self.memory_store.load_user_profile(user_id)
        self.memory_store.load_trip_history()
        self.memory_store.load_current_trip()

        self.conversation_history.append(
            ConversationMessage(role="assistant", content="你好！我是旅睿，你的私人旅行管家 🤗\n\n我可以帮你：\n• 根据目的地、季节自动生成清单\n• 记住你的习惯，持续优化\n• 主动提醒遗漏物品\n\n有什么旅行计划吗？告诉我目的地和时间吧！")
        )

        return self.conversation_history

    async def process_message(self, user_message: str) -> dict:
        self.conversation_history.append(
            ConversationMessage(role="user", content=user_message)
        )

        intent_result = await self._recognize_intent(user_message)

        response_content = ""
        trip_data = None
        checklist_data = None

        if intent_result["intent"] == "CREATE_TRIP":
            response_content, trip_data = await self._handle_create_trip(intent_result)
        elif intent_result["intent"] == "ADD_ITEM":
            response_content, checklist_data = await self._handle_add_item(intent_result)
        elif intent_result["intent"] == "CHECK_COMPLETENESS":
            response_content, checklist_data = await self._handle_check_completeness(intent_result)
        elif intent_result["intent"] == "RECOMMEND_DESTINATION":
            response_content = await self._handle_recommend_destination(intent_result)
        else:
            response_content = await self._handle_general_chat(user_message)

        self.conversation_history.append(
            ConversationMessage(role="assistant", content=response_content)
        )

        return {
            "response": response_content,
            "intent": intent_result["intent"],
            "trip": trip_data.model_dump() if trip_data else None,
            "checklist": checklist_data.model_dump() if checklist_data else None,
            "history": [msg.model_dump() for msg in self.conversation_history]
        }

    async def _recognize_intent(self, user_message: str) -> dict:
        if self.use_mock or not self.llm:
            return self._fallback_intent_recognition(user_message)

        prompt = INTENT_RECOGNITION_PROMPT.format(user_message=user_message)

        try:
            response = await self.llm.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)

            if not content:
                return self._fallback_intent_recognition(user_message)

            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start != -1 and json_end != 0:
                json_str = content[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            print(f"Intent recognition error: {e}")

        return self._fallback_intent_recognition(user_message)

    FOOD_PREFERENCE_KEYWORDS = {
        "辣": ["辣", "吃辣", "爱吃辣", "喜欢辣", "能吃辣", "无辣不欢", "麻辣", "香辣"],
        "甜": ["甜", "爱吃甜", "喜欢甜", "甜食"],
        "酸": ["酸", "爱吃酸", "喜欢酸"],
        "清淡": ["清淡", "不辣", "不吃辣", "少油", "健康"],
        "海鲜": ["海鲜", "鱼", "虾", "蟹"],
        "面食": ["面", "面食", "拉面", "面条"],
        "火锅": ["火锅", "涮肉"],
        "烧烤": ["烧烤", "烤肉"],
        "小吃": ["小吃", "特色小吃", "美食"]
    }

    DESTINATION_BY_FOOD = {
        "辣": [
            {"name": "成都", "reason": "川菜发源地，麻辣火锅、串串香、担担面应有尽有"},
            {"name": "重庆", "reason": "山城火锅之都，小面、酸辣粉让人欲罢不能"},
            {"name": "长沙", "reason": "湘菜重镇，剁椒鱼头、臭豆腐、口味虾超够味"},
            {"name": "贵阳", "reason": "酸汤鱼、丝娃娃，酸辣口味独特"},
            {"name": "柳州", "reason": "螺蛳粉的故乡，又臭又辣让人上瘾"}
        ],
        "甜": [
            {"name": "苏州", "reason": "苏式糕点闻名天下，松鼠鳜鱼、糖粥清甜可口"},
            {"name": "杭州", "reason": "西湖醋鱼、龙井虾仁，清淡中带鲜甜"},
            {"name": "无锡", "reason": "酱排骨、小笼包，甜而不腻"},
            {"name": "广州", "reason": "早茶点心精致，甜品糖水种类繁多"},
            {"name": "澳门", "reason": "葡式蛋挞、猪扒包，中西合璧的甜蜜"}
        ],
        "酸": [
            {"name": "贵阳", "reason": "酸汤鱼、酸汤牛肉，酸香开胃"},
            {"name": "云南", "reason": "酸木瓜鸡、傣味酸笋，酸爽过瘾"},
            {"name": "山西", "reason": "陈醋文化，酸汤面、糖醋丸子"},
            {"name": "南宁", "reason": "老友粉，酸笋豆豉香气浓郁"}
        ],
        "清淡": [
            {"name": "扬州", "reason": "淮扬菜讲究刀工，清鲜平和"},
            {"name": "上海", "reason": "本帮菜浓油赤酱但不重口"},
            {"name": "宁波", "reason": "海鲜鲜美，原汁原味"},
            {"name": "福州", "reason": "佛跳墙、鱼丸，清淡滋补"}
        ],
        "海鲜": [
            {"name": "青岛", "reason": "啤酒配海鲜，蛤蜊、大虾新鲜肥美"},
            {"name": "大连", "reason": "渤海湾海鲜，海参、鲍鱼有名"},
            {"name": "厦门", "reason": "沙茶面配海鲜，鲜味十足"},
            {"name": "三亚", "reason": "热带海鲜，龙虾、芒果贝应有尽有"},
            {"name": "舟山", "reason": "东海渔场，带鱼、鲳鱼新鲜"}
        ],
        "面食": [
            {"name": "西安", "reason": "肉夹馍、凉皮、油泼面，面食天堂"},
            {"name": "兰州", "reason": "正宗牛肉拉面，一清二白三红四绿"},
            {"name": "山西", "reason": "刀削面、剔尖、揪片，面食花样多"},
            {"name": "郑州", "reason": "烩面发源地，汤鲜味美"}
        ],
        "火锅": [
            {"name": "重庆", "reason": "正宗牛油火锅，麻辣鲜香"},
            {"name": "成都", "reason": "清油火锅，菜品丰富"},
            {"name": "潮汕", "reason": "牛肉火锅，鲜切牛肉绝绝子"},
            {"name": "北京", "reason": "铜锅涮肉，老北京风味"}
        ],
        "烧烤": [
            {"name": "淄博", "reason": "烧烤之都，小饼卷一切"},
            {"name": "锦州", "reason": "东北烧烤代表，烤串种类多"},
            {"name": "延吉", "reason": "朝鲜族风味，烤五花肉、辣白菜"},
            {"name": "新疆", "reason": "红柳烤肉、馕坑肉，异域风味"}
        ],
        "小吃": [
            {"name": "西安", "reason": "回民街小吃琳琅满目"},
            {"name": "成都", "reason": "宽窄巷子、锦里小吃云集"},
            {"name": "武汉", "reason": "热干面、豆皮、鸭脖，过早文化"},
            {"name": "长沙", "reason": "坡子街、太平街小吃遍地"}
        ]
    }

    def _fallback_intent_recognition(self, user_message: str) -> dict:
        entities = {
            "destination": None,
            "duration": None,
            "season": None,
            "crowd_type": None,
            "trip_type": None,
            "items": [],
            "food_preferences": []
        }

        recommend_keywords = ["推荐", "哪里", "什么地方", "好去处", "好玩", "好吃"]
        has_recommend = any(keyword in user_message for keyword in recommend_keywords)

        for food_type, keywords in self.FOOD_PREFERENCE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in user_message:
                    entities["food_preferences"].append(food_type)
                    break

        patterns = [
            r'去(.+?)(?:旅|游|玩|出差|爬山|徒步|逛|看|吃|$)',
            r'到(.+?)(?:旅|游|玩|出差|爬山|徒步|逛|看|吃|$)',
            r'(?:去|到)(.+?)(?:的旅行|旅行|游玩)',
            r'(?:计划|准备)(?:去|到)?(.+?)(?:旅行|旅游)'
        ]

        for pattern in patterns:
            destination_match = re.search(pattern, user_message)
            if destination_match:
                entities["destination"] = destination_match.group(1).strip()
                break

        if not entities["destination"]:
            mountain_match = re.search(r'(爬山|登山|徒步)(?:去(.+?))?', user_message)
            if mountain_match:
                entities["destination"] = mountain_match.group(2) if mountain_match.group(2) else "山区"
                entities["trip_type"] = "徒步登山"

        duration_match = re.search(r'(\d+)天', user_message)
        if duration_match:
            entities["duration"] = int(duration_match.group(1))

        season_keywords = {"春天": "春季", "夏天": "夏季", "秋天": "秋季", "冬天": "冬季"}
        for keyword, season in season_keywords.items():
            if keyword in user_message:
                entities["season"] = season
                break

        if "春节" in user_message or "端午" in user_message or "中秋" in user_message:
            entities["season"] = "春季" if "春节" in user_message else "夏季" if "端午" in user_message else "秋季"

        if "家庭" in user_message or "带孩子" in user_message or "带娃" in user_message:
            entities["crowd_type"] = "家庭"
        elif "情侣" in user_message or "夫妻" in user_message:
            entities["crowd_type"] = "情侣"
        elif "商务" in user_message or "出差" in user_message:
            entities["crowd_type"] = "商务"

        if "海" in user_message or "岛" in user_message or "沙滩" in user_message:
            entities["trip_type"] = "海岛度假"
        elif "山" in user_message or "徒步" in user_message:
            entities["trip_type"] = "徒步登山"
        elif "出差" in user_message or "商务" in user_message:
            entities["trip_type"] = "商务出差"

        item_patterns = [
            "防晒", "泳衣", "相机", "护照", "签证", "药品",
            "雨伞", "充电宝", "转换插头", "牙刷", "毛巾",
            "帽子", "墨镜", "围巾", "手套", "防晒霜", "护肤品"
        ]
        for item in item_patterns:
            if item in user_message:
                entities["items"].append(item)

        add_item_match = re.search(r'(添加|加)(.+?)(?:。|$)', user_message)
        if add_item_match:
            entities["items"].append(add_item_match.group(2).strip())

        intent = "CREATE_TRIP" if entities["destination"] else "GENERAL_CHAT"
        
        if "遗漏" in user_message or "检查" in user_message and ("完整" in user_message or "漏" in user_message):
            intent = "CHECK_COMPLETENESS"
        elif intent == "GENERAL_CHAT" and entities["items"]:
            intent = "ADD_ITEM"
        elif intent == "GENERAL_CHAT" and entities["food_preferences"] and has_recommend:
            intent = "RECOMMEND_DESTINATION"

        return {
            "intent": intent,
            "entities": entities,
            "response": ""
        }

    async def _handle_create_trip(self, intent_result: dict) -> tuple[str, Optional[TripPlan]]:
        entities = intent_result["entities"]

        destination = entities.get("destination") or "日本"
        duration = entities.get("duration") or 7
        season = entities.get("season") or self._infer_season()
        crowd_type = entities.get("crowd_type") or "独自"
        trip_type = entities.get("trip_type") or "城市观光"

        trip_id = str(uuid.uuid4())
        checklist = await self.checklist_generator.generate(
            destination=destination,
            season=season,
            duration=duration,
            crowd_type=crowd_type,
            trip_type=trip_type,
            special_needs=[],
            user_profile=self.memory_store.user_profile
        )
        checklist.trip_id = trip_id

        trip = TripPlan(
            trip_id=trip_id,
            destination=destination,
            duration=duration,
            season=season,
            crowd_type=CrowdType(crowd_type),
            trip_type=TripType(trip_type),
            checklist=checklist
        )

        self.memory_store.save_current_trip(trip)

        scene_info = await self.scene_recognizer.recognize(destination, season)

        response = f"✈️ 已为你生成【{destination}{duration}日游】清单！\n\n"
        response += f"📦 共{checklist.total_count}件物品，分为{len(checklist.categories)}大类\n"
        response += f"🏷️ 分类：{'、'.join(checklist.categories)}\n\n"

        if scene_info.get("special_equipment"):
            response += f"✨ 已根据{scene_info['geo_features'][0] if scene_info.get('geo_features') else '目的地'}自动添加特殊装备\n"

        if scene_info.get("tips"):
            response += f"💡 {scene_info['tips'][0]}\n"

        response += f"\n🗂️ 清单概览：\n"
        for category in checklist.categories[:5]:
            cat_items = [item for item in checklist.items if item.category == category]
            response += f"• {category}：{len(cat_items)}件\n"

        response += f"\n你可以：\n"
        response += f"• 说「检查一下有没有遗漏」查看完整性\n"
        response += f"• 说「帮我添加XXX」添加物品\n"
        response += f"• 说「删除XXX」移除物品"

        return response, trip

    async def _handle_add_item(self, intent_result: dict) -> tuple[str, Optional[Checklist]]:
        items = intent_result["entities"].get("items", [])
        current_trip = self.memory_store.current_trip

        if not current_trip or not current_trip.checklist:
            return "📝 我还没创建清单呢！告诉我你要去哪里旅行，我来帮你生成清单。", None

        added_items = []
        for item_name in items:
            new_item = Item(
                id=str(uuid.uuid4()),
                name=item_name,
                category="日用",
                is_essential=False,
                reason="用户主动添加",
                source="habit"
            )
            current_trip.checklist.items.append(new_item)
            current_trip.checklist.total_count += 1
            added_items.append(item_name)

        self.memory_store.save_current_trip(current_trip)

        response = f"✅ 已添加【{'、'.join(added_items)}】到清单\n"
        response += f"📊 当前清单共有{current_trip.checklist.total_count}件物品"

        return response, current_trip.checklist

    async def _handle_check_completeness(self, intent_result: dict) -> tuple[str, Optional[Checklist]]:
        current_trip = self.memory_store.current_trip

        if not current_trip or not current_trip.checklist:
            return "📝 我还没创建清单呢！告诉我你要去哪里旅行，我来帮你生成清单。", None

        check_result = await self.completeness_checker.check(
            checklist=current_trip.checklist,
            destination=current_trip.destination,
            season=current_trip.season,
            duration=current_trip.duration,
            crowd_type=current_trip.crowd_type.value,
            trip_type=current_trip.trip_type.value,
            user_profile=self.memory_store.user_profile
        )

        response = "🔍 清单完整性检查完成！\n\n"

        if check_result.get("missing_categories"):
            response += f"⚠️ 缺失分类：{'、'.join(check_result['missing_categories'])}\n"

        if check_result.get("suggested_items"):
            response += "\n💡 建议添加：\n"
            for item in check_result["suggested_items"][:5]:
                priority_icon = "🔴" if item["priority"] == "high" else "🟡"
                response += f"{priority_icon} 【{item['name']}】- {item['reason']}\n"

        score = check_result.get("completeness_score", 0.9)
        response += f"\n📊 完整度：{score * 100:.0f}%"
        if score >= 0.9:
            response += " ✨ 非常好！"
        elif score >= 0.7:
            response += " ✅ 不错，但还有些小物品可以补充"

        return response, current_trip.checklist

    async def _handle_recommend_destination(self, intent_result: dict) -> str:
        food_preferences = intent_result["entities"].get("food_preferences", [])
        
        if not food_preferences:
            return "🍽️ 请告诉我你的饮食偏好，比如喜欢吃辣、喜欢海鲜等，我来为你推荐合适的旅游地点！"

        response = f"🌶️ 根据你喜欢{'、'.join(food_preferences)}的口味，为你推荐以下旅游目的地：\n\n"
        
        for food_type in food_preferences:
            destinations = self.DESTINATION_BY_FOOD.get(food_type, [])
            if destinations:
                response += f"✨ 喜欢{food_type}的话，可以去：\n"
                for i, dest in enumerate(destinations[:3], 1):
                    response += f"{i}. 【{dest['name']}】- {dest['reason']}\n"
                response += "\n"
        
        if self.memory_store.user_profile:
            for pref in food_preferences:
                if pref not in self.memory_store.user_profile.food_preferences:
                    self.memory_store.user_profile.food_preferences.append(pref)
            self.memory_store.save_user_profile()
        
        response += "💡 想了解哪个目的地的详细旅行清单？告诉我，我来帮你生成！\n"
        response += "示例：我要去成都旅游，3天"

        return response

    async def _handle_general_chat(self, user_message: str) -> str:
        if self.use_mock or not self.llm:
            return self._mock_general_response(user_message)

        user_profile = self.memory_store.user_profile

        context_prompt = f"""
用户：{user_message}

用户信息：
- 常用目的地：{', '.join(user_profile.frequent_destinations) if user_profile.frequent_destinations else '暂无'}
- 总是忘带：{', '.join(user_profile.get_forgotten_items()) if user_profile.get_forgotten_items() else '暂无记录'}
- 健康信息：{', '.join(user_profile.health_info) if user_profile.health_info else '无'}

当前行程：{self.memory_store.current_trip.destination if self.memory_store.current_trip else '暂无'}

请用友好的方式回复用户，作为旅行管家提供帮助。
"""

        try:
            response = await self.llm.ainvoke([
                ("system", SYSTEM_PROMPT),
                ("user", context_prompt)
            ])
            content = response.content if hasattr(response, 'content') else str(response)
            if not content:
                return self._mock_general_response(user_message)
            return content
        except Exception as e:
            print(f"General chat error: {e}")
            return self._mock_general_response(user_message)

    def _mock_general_response(self, user_message: str) -> str:
        greetings = ["你好", "您好", "嗨", "hello", "hi"]
        if any(g in user_message.lower() for g in greetings):
            return "你好！我是旅睿，你的私人旅行管家 🤗\n\n我可以帮你：\n• 根据目的地、季节自动生成清单\n• 记住你的习惯，持续优化\n• 主动提醒遗漏物品\n\n有什么旅行计划吗？告诉我目的地和时间吧！"

        if self.memory_store.current_trip:
            return f"我已经为你创建了【{self.memory_store.current_trip.destination}{self.memory_store.current_trip.duration}日游】的清单。你可以：\n• 说「检查一下有没有遗漏」查看完整性\n• 说「帮我添加XXX」添加物品\n• 说「删除XXX」移除物品"

        return "告诉我你要去哪里旅行，我来帮你生成完美的旅行清单！\n\n示例：\n• 我要去海南三亚旅游，5天\n• 端午节去厦门3天\n• 带家人去北京玩4天"


    def _infer_season(self) -> str:
        month = datetime.now().month
        if month in [3, 4, 5]:
            return "春季"
        elif month in [6, 7, 8]:
            return "夏季"
        elif month in [9, 10, 11]:
            return "秋季"
        else:
            return "冬季"

    async def update_user_profile(self, key: str, value):
        if not self.memory_store.user_profile:
            return

        if key == "destination":
            destinations = self.memory_store.user_profile.frequent_destinations
            if value not in destinations:
                destinations.append(value)
        elif key == "health":
            health_list = self.memory_store.user_profile.health_info
            if value not in health_list:
                health_list.append(value)
        elif key == "habit":
            self.memory_store.user_profile.add_forgotten_item(value)

        self.memory_store.save_user_profile()
