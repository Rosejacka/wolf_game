from role import *
from history import *

from score_calculator import ScoreCalculator
from mvp_selector import MvpSelector
import random
import json
import os
from datetime import datetime

#WerewolfGame负责保存游戏状态，游戏逻辑由前端脚本负责
class WerewolfGame:
    def __init__(self):
        self.players = []
        self.history = None # 存储游戏的历史记录
        self.current_day = 1
        self.current_phase = "夜晚"
        self.vote_result = []
        self.wolf_want_kill = {}
        self.start_time = datetime.now().strftime("%Y%m%d%H%M")

        # 创建logs目录（如果不存在）
        if not os.path.exists('logs'):
            os.makedirs('logs')

    def dump_history(self):
        self.history.dump()

    def start(self):
        self.history = History()
        self.vote_result = []
        self.wolf_want_kill = {}
        self.current_day = 1  # 游戏开始时,设置为第1天
        self.current_phase = "夜晚"  # 初始化当前阶段为夜晚
        self.start_time = datetime.now().strftime("%Y%m%d%H%M")
        self.initialize_roles()
        display_config = {
            "display_role": True,
            "display_thinking": True,
            "display_witch_action": True,
            "display_wolf_action": True,
            "display_hunter_action": True,
            "display_divine_action": True,
            "display_vote_action": True,
            "display_model": True,
            "auto_play": True
        }
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            if "display_role" in config:
                display_config["display_role"] = config["display_role"]
            if "display_thinking" in config:
                display_config["display_thinking"] = config["display_thinking"]
            if "display_witch_action" in config:
                display_config["display_witch_action"] = config["display_witch_action"]
            if "display_wolf_action" in config:
                display_config["display_wolf_action"] = config["display_wolf_action"]
            if "display_hunter_action" in config:
                display_config["display_hunter_action"] = config["display_hunter_action"]
            if "display_divine_action" in config:
                display_config["display_divine_action"] = config["display_divine_action"]
            if "display_vote_action" in config:
                display_config["display_vote_action"] = config["display_vote_action"]
            if "auto_play" in config:
                display_config["auto_play"] = config["auto_play"]
            if "display_model" in config:
                display_config["display_model"] = config["display_model"]

        return display_config


    def initialize_roles(self):
        roles = [Wolf, Wolf, Wolf, Seer, Witch, Hunter, Villager, Villager, Villager]

        # 角色类映射
        role_classes = {
            '狼人': Wolf,
            '村民': Villager,
            '预言家': Seer,
            '女巫': Witch,
            '猎人': Hunter
        }

        # 读取配置文件决定每个玩家使用的模型
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 新增：模型分配逻辑
        if config.get("random_model") and config.get("models"):
            models = config["models"]
            n_models = len(models)
            n_players = len(config["players"])
            # 先确保每个模型至少分配一次
            assigned = [i for i in range(n_models)]
            # 多余玩家随机分配
            if n_players > n_models:
                assigned += random.choices(range(n_models), k=n_players - n_models)
            random.shuffle(assigned)
            assign_idx = 0
            for idx, player in enumerate(config["players"]):
                # 如果原本配置的是human则不分配模型
                if str(player.get("model_name", "")).lower() == "human":
                    player["model_name"] = "human"
                    player["api_key"] = ""
                else:
                    model = models[assigned[assign_idx]]
                    player["model_name"] = model["model_name"]
                    player["api_key"] = model["api_key"]
                    if "base_url" in model:
                        player["base_url"] = model["base_url"]
                    assign_idx += 1

        if config["randomize_roles"]:
            random.shuffle(roles)
        else:
            for i in range(len(roles)):
                role_str = config["players"][i].get("role")
                if not role_str:
                    raise ValueError(f"玩家 {i} 没有设置角色")
                role_class = role_classes.get(role_str.lower())
                if not role_class:
                    raise ValueError(f"无效的角色 '{role_str}' 对玩家 {i}")
                roles[i] = role_class

        # 使用配置文件中的模型、API key和base_url
        self.players = [
            role(i + 1, config["players"][i]["model_name"], config["players"][i]["api_key"], self,
                 config["players"][i].get("base_url"))
            for i, role in enumerate(roles)
        ]

        if config["randomize_position"]:
            print("随机排序玩家")
            random.shuffle(self.players)
            for i, player in enumerate(self.players):
                player.player_index = i + 1

        with open(f'logs/result_{self.start_time}.txt', 'a', encoding='utf-8') as log_file:
            for player in self.players:
                log_file.write(f"{player.player_index}号玩家的角色是{player.role_type}, 模型使用{player.model.model_name}\n")
                print(f"{player.player_index}号玩家的角色是{player.role_type}, 模型使用{player.model.model_name}")


    def toggle_day_night(self):
        self.history.toggle_day_night()
        if self.current_phase == "白天":
            self.current_phase = "夜晚"
        else:
            self.current_phase = "白天"
            self.current_day += 1  # 每当从夜晚切换到白天时,天数加1

    def get_players(self):
        players = {}
        for player in self.players:
            players[player.player_index] = {
                "index": player.player_index,
                "name": f"{player.player_index}号玩家",
                "role_type": player.role_type,
                "is_alive": player.is_alive,
                "model": player.model.model_name,
                "is_human": True if player.model.model_name == "human" else False
            }
        return players

    def get_wolves(self):
        wolfs = []
        for player in self.players:
            if player.role_type == "狼人":
                wolfs.append({
                    "player_index": player.player_index,
                    "is_alive": player.is_alive
                })
        return wolfs

    def divine(self, player_idx):
        # 预言家揭示身份逻辑
        resp = self.players[player_idx-1].divine()
        return resp

    def decide_kill(self, player_idx, kill_id, is_second_vote=False):
        # 决定杀谁
        if is_second_vote:
            # 将字典转换为对象列表
            kill_list = [{"player_index": idx, "kill": info["kill"], "reason": info["reason"]}
                        for idx, info in self.wolf_want_kill.items()]
            result = self.players[player_idx-1].decide_kill(kill_id, kill_list)
        else:
            result = self.players[player_idx-1].decide_kill(kill_id)

        self.wolf_want_kill[player_idx] = {
            "kill": result["kill"],
            "reason": result["reason"]
        }

        return result

    def get_wolf_want_kill(self):
        # 统计每个玩家获得的票数
        vote_count = {}
        for player_idx, info in self.wolf_want_kill.items():
            target = info.get('kill')  # 获取投票目标
            if target is not None:  # 确保有效投票
                if target in vote_count:
                    vote_count[target] += 1
                else:
                    vote_count[target] = 1

        if not vote_count:  # 如果没有有效投票
            print("没有有效投票")
            return -1

        # 找出最高票数
        max_votes = max(vote_count.values())

        # 找出获得最高票数的玩家
        candidates = [player for player, votes in vote_count.items() if votes == max_votes]

        # 如果只有一个人得票最高，处决该玩家
        if len(candidates) == 1:
            return candidates[0]

        print("多人投票一致")
        print(candidates)
        return -1

    def kill(self, player_idx):
        if player_idx == -1:
            raise ValueError("player_idx == -1")
        # 狼人杀人
        self.players[player_idx-1].be_killed()

    def decide_cure_or_poison(self, player_idx):
        someone_will_be_killed = self.get_wolf_want_kill()
        result = self.players[player_idx-1].decide_cure_or_poison(someone_will_be_killed)
        return result

    def poison(self, player_idx):
        self.players[player_idx-1].be_poisoned()

    def cure(self, player_idx):
        self.players[player_idx-1].be_cured()

    def decide_vote(self, player_idx) -> dict:
        """仅做投票决策，不落库，供前端预取"""
        # 若投票者已死亡，直接返回弃票
        if not self.players[player_idx - 1].is_alive:
            return {'vote': -1, 'thinking': '已出局，无法投票'}
        # 触发一次决策，注意不记录历史
        result = self.players[player_idx - 1].decide_vote()
        # 仅返回 vote/ thinking
        if not result or 'vote' not in result:
            return {'vote': -1, 'thinking': result.get('thinking', '') if isinstance(result, dict) else ''}
        return result

    def speak(self, player_idx, content=None):
        resp = self.players[player_idx-1].speak(content)
        return resp

    def vote(self, player_idx, vote_id) -> int:
        # 安全检查：若投票者已死亡，直接返回弃票
        if not self.players[player_idx - 1].is_alive:
            safe_result = {'vote': -1, 'thinking': '已出局，无法投票'}
            self.vote_result.append({
                "player_idx": player_idx,
                "vote_id": -1
            })
            return safe_result

        # 发起投票（AI或人类）
        result = self.players[player_idx - 1].vote(vote_id)
        chosen = result.get("vote", -1)

        def is_valid_target(idx: int) -> bool:
            return isinstance(idx, int) and 1 <= idx <= len(self.players) and self.players[idx - 1].is_alive

        # 若首次选择非法或已死亡，尝试重算一次
        if not is_valid_target(chosen) and chosen != -1:
            # 给模型更多上下文信息，提示上个目标无效以及可投目标
            alive_list = [p.player_index for p in self.players if p.is_alive and p.player_index != player_idx]
            extra = {
                "上次投票无效": f"目标{chosen}号已出局或无效，请在{alive_list}中重新选择；若无把握可弃票(-1)",
                "存活玩家": alive_list,
            }
            # 仅决策，不落库
            re_decision = self.players[player_idx - 1].decide_vote(extra)
            re_vote = re_decision.get("vote", -1) if isinstance(re_decision, dict) else -1
            chosen = re_vote if is_valid_target(re_vote) or re_vote == -1 else -1

        # 规范化与兜底
        if chosen != -1 and not is_valid_target(chosen):
            chosen = -1
        result["vote"] = chosen

        # 记录投票结果
        self.vote_result.append({
            "player_idx": player_idx,
            "vote_id": chosen
        })

        return result


    def reset_vote_result(self):
        self.vote_result = []

    def get_vote_result(self):
        return self.vote_result

    def last_words(self, player_idx, speak, death_reason):
        # 最后发言
        resp = self.players[player_idx-1].last_words(speak, death_reason)
        return resp

    def revenge(self, player_idx, death_reason):
        resp = self.players[player_idx-1].revenge(death_reason)
        return resp

    def execute(self, player_idx, vote_result):
        # 处决玩家
        self.players[player_idx-1].be_executed(vote_result)

    def reset_wolf_want_kill(self):
        self.wolf_want_kill = {}


    def attack(self, player_idx):
        # 猎人攻击
        self.players[player_idx-1].be_attacked()

    def get_day(self):
        return self.current_day


    def check_winner(self) -> str:
        # 按照新规则统计：
        # 狼人胜利：杀光所有村民 或 杀光所有神职（预言家、女巫、猎人）
        # 好人胜利：所有狼人出局
        alive_wolves = sum(1 for p in self.players if p.role_type == '狼人' and p.is_alive)
        alive_villagers = sum(1 for p in self.players if p.role_type == '村民' and p.is_alive)
        alive_specials = sum(1 for p in self.players if p.role_type in ['预言家', '女巫', '猎人'] and p.is_alive)

        print("--- 检查胜负 ----")
        print(f"存活 - 狼人:{alive_wolves} 村民:{alive_villagers} 神职:{alive_specials}")

        if alive_wolves == 0:
            winner = '村民胜利'
            with open(f'logs/result_{self.start_time}.txt', 'a', encoding='utf-8') as log_file:
                log_file.write(f"【{self.current_day} {self.current_phase}】 村民胜利\n")
        elif alive_villagers == 0 or alive_specials == 0:
            winner = '狼人胜利'
            with open(f'logs/result_{self.start_time}.txt', 'a', encoding='utf-8') as log_file:
                log_file.write(f"【{self.current_day} {self.current_phase}】 狼人胜利\n")
        else:
            winner = '胜负未分'

        # 如果游戏结束，计算积分
        if winner != '胜负未分':
            self.calculate_and_save_scores(winner)

        return winner

    def calculate_and_save_scores(self, winner: str):
        """计算并保存积分"""
        try:
            # 创建积分计算器，先计算不含 MVP 的基础分
            score_calculator = ScoreCalculator(self)
            player_scores = score_calculator.calculate_scores(winner)
            ranking = score_calculator.get_ranking()

            # 自动评选 MVP（使用评审模型）
            auto_mvp = None
            try:
                selector = MvpSelector()
                auto_mvp = selector.select(self, winner, precomputed_ranking=ranking)
                # 若返回了有效的 mvp_player_index，则基于该 MVP 重算积分与排名
                if auto_mvp and isinstance(auto_mvp.get('mvp_player_index'), int):
                    score_calculator = ScoreCalculator(self)
                    player_scores = score_calculator.calculate_scores(winner, mvp_player_index=auto_mvp['mvp_player_index'])
                    ranking = score_calculator.get_ranking()
            except Exception as _e:
                # 自动评选失败不影响结算
                auto_mvp = None

            # 保存积分到日志文件
            with open(f'logs/result_{self.start_time}.txt', 'a', encoding='utf-8') as log_file:
                log_file.write(f"\n=== 积分统计 ===\n")
                log_file.write(f"游戏结果：{winner}\n\n")

                for i, player_data in enumerate(ranking, 1):
                    log_file.write(f"第{i}名：{player_data['player_index']}号玩家 ({player_data['role_type']})\n")
                    log_file.write(f"  总分：{player_data['total_score']}分\n")
                    log_file.write(f"  阵营分：{player_data['camp_score']}分\n")
                    log_file.write(f"  贡献分：{player_data['contribution_score']}分\n")
                    log_file.write(f"  MVP分：{player_data['mvp_score']}分\n")
                    if player_data['contributions']:
                        log_file.write(f"  贡献详情：{', '.join(player_data['contributions'])}\n")
                    log_file.write("\n")

            # 保存积分数据供前端使用
            self.game_scores = {
                'winner': winner,
                'ranking': ranking,
                'player_scores': {str(k): v.get_score_detail() for k, v in player_scores.items()},
                'auto_mvp': auto_mvp  # 形如 {mvp_player_index, reason, model, auto}
            }

            print("=== 积分计算完成 ===")
            for i, player_data in enumerate(ranking, 1):
                print(f"第{i}名：{player_data['player_index']}号 {player_data['role_type']} - {player_data['total_score']}分")
            if auto_mvp and isinstance(auto_mvp.get('mvp_player_index'), int):
                print(f"自动MVP：{auto_mvp['mvp_player_index']}号，理由：{auto_mvp.get('reason','')}")

        except Exception as e:
            print(f"积分计算出错：{e}")
            with open(f'logs/result_{self.start_time}.txt', 'a', encoding='utf-8') as log_file:
                log_file.write(f"\n积分计算出错：{e}\n")

    def get_game_scores(self):
        """获取游戏积分数据"""
        return getattr(self, 'game_scores', None)

    def set_mvp(self, mvp_player_index: int):
        """设置MVP玩家"""
        if hasattr(self, 'game_scores') and self.game_scores:
            # 重新计算积分，这次包含MVP
            score_calculator = ScoreCalculator(self)
            player_scores = score_calculator.calculate_scores(
                self.game_scores['winner'],
                mvp_player_index
            )

            # 更新积分数据
            ranking = score_calculator.get_ranking()
            self.game_scores['ranking'] = ranking
            self.game_scores['player_scores'] = {str(k): v.get_score_detail() for k, v in player_scores.items()}

            # 更新日志
            with open(f'logs/result_{self.start_time}.txt', 'a', encoding='utf-8') as log_file:
                log_file.write(f"\n=== MVP更新 ===\n")
                log_file.write(f"MVP玩家：{mvp_player_index}号玩家\n\n")

                for i, player_data in enumerate(ranking, 1):
                    log_file.write(f"第{i}名：{player_data['player_index']}号玩家 ({player_data['role_type']})\n")
                    log_file.write(f"  总分：{player_data['total_score']}分\n")
                    if player_data['mvp_score'] > 0:
                        log_file.write(f"  ★ MVP加分：{player_data['mvp_score']}分\n")
                    log_file.write("\n")

            return True
        return False

    def set_manual_position(self, position_mapping):
        """手动设置玩家位置和角色分配

        Args:
            position_mapping: dict, 格式为 {position: {"role": "角色名", "model_name": "模型名", "api_key": "密钥"}}

        Returns:
            dict: 操作结果
        """
        try:
            # 角色类映射
            role_classes = {
                '狼人': Wolf,
                '村民': Villager,
                '预言家': Seer,
                '女巫': Witch,
                '猎人': Hunter
            }

            # 读取配置文件获取默认API密钥
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 验证位置映射的有效性
            if not isinstance(position_mapping, dict):
                raise ValueError("位置映射必须是字典格式")

            # 转换字符串键为整数键
            int_position_mapping = {}
            for pos, data in position_mapping.items():
                int_pos = int(pos) if isinstance(pos, str) else pos
                int_position_mapping[int_pos] = data
            position_mapping = int_position_mapping

            positions = list(position_mapping.keys())
            if not all(isinstance(pos, int) and 1 <= pos <= 9 for pos in positions):
                raise ValueError("位置必须是1-9之间的整数")

            # 验证角色分配
            roles_in_mapping = [data.get("role") for data in position_mapping.values()]
            for role in roles_in_mapping:
                if role not in role_classes:
                    raise ValueError(f"无效的角色: {role}")

            # 创建新的玩家列表
            new_players = [None] * 9

            for position, player_data in position_mapping.items():
                role_name = player_data.get("role")
                model_name = player_data.get("model_name", config["players"][position-1]["model_name"])
                api_key = player_data.get("api_key", config["players"][position-1]["api_key"])
                base_url = player_data.get("base_url", config["players"][position-1].get("base_url"))

                role_class = role_classes[role_name]
                new_players[position-1] = role_class(position, model_name, api_key, self, base_url)

            # 填充未指定的位置（保持原有配置）
            for i in range(9):
                if new_players[i] is None:
                    # 使用原有配置
                    original_config = config["players"][i]
                    role_name = original_config.get("role", "村民")
                    role_class = role_classes[role_name]
                    new_players[i] = role_class(
                        i + 1,
                        original_config["model_name"],
                        original_config["api_key"],
                        self
                    )

            # 更新玩家列表
            self.players = new_players

            # 更新配置文件以持久化更改
            self.update_config_file(position_mapping)

            # 记录日志
            with open(f'logs/result_{self.start_time}.txt', 'a', encoding='utf-8') as log_file:
                log_file.write("\n=== 手动位置调整 ===\n")
                for player in self.players:
                    log_file.write(f"{player.player_index}号玩家的角色是{player.role_type}, 模型使用{player.model.model_name}\n")

            return {
                "success": True,
                "message": "位置设置成功，配置已保存",
                "players": self.get_players()
            }

        except Exception as e:
            return {"success": False, "message": str(e)}

    def update_config_file(self, position_mapping):
        """更新配置文件以持久化位置更改

        Args:
            position_mapping: dict, 位置映射
        """
        try:
            # 读取当前配置
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 更新玩家配置
            for position_str, player_data in position_mapping.items():
                position = int(position_str)
                if 1 <= position <= 9:
                    config["players"][position-1]["role"] = player_data["role"]
                    if "model_name" in player_data:
                        config["players"][position-1]["model_name"] = player_data["model_name"]
                    if "api_key" in player_data:
                        config["players"][position-1]["api_key"] = player_data["api_key"]

            # 禁用随机化，确保使用手动设置的位置
            config["randomize_position"] = False
            config["randomize_roles"] = False

            # 保存配置文件
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            print("配置文件已更新，禁用了位置随机化")

        except Exception as e:
            print(f"更新配置文件时出错: {e}")

    def update_config_after_swap(self, position1, position2):
        """交换位置后更新配置文件

        Args:
            position1: int, 第一个位置
            position2: int, 第二个位置
        """
        try:
            # 读取当前配置
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 交换配置中的角色
            player1_config = config["players"][position1-1].copy()
            player2_config = config["players"][position2-1].copy()

            config["players"][position1-1]["role"] = player2_config["role"]
            config["players"][position2-1]["role"] = player1_config["role"]

            # 禁用随机化
            config["randomize_position"] = False
            config["randomize_roles"] = False

            # 保存配置文件
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            print(f"配置文件已更新，交换了位置{position1}和{position2}")

        except Exception as e:
            print(f"交换后更新配置文件时出错: {e}")

    def swap_players_position(self, position1, position2):
        """交换两个位置的玩家

        Args:
            position1: int, 第一个位置 (1-9)
            position2: int, 第二个位置 (1-9)

        Returns:
            dict: 操作结果
        """
        try:
            if not (1 <= position1 <= 9 and 1 <= position2 <= 9):
                raise ValueError("位置必须在1-9之间")

            if position1 == position2:
                return {"success": True, "message": "相同位置无需交换"}

            # 交换玩家
            player1 = self.players[position1-1]
            player2 = self.players[position2-1]

            # 更新玩家索引
            player1.player_index = position2
            player2.player_index = position1

            # 交换在数组中的位置
            self.players[position1-1] = player2
            self.players[position2-1] = player1

            # 更新配置文件
            self.update_config_after_swap(position1, position2)

            # 记录日志
            with open(f'logs/result_{self.start_time}.txt', 'a', encoding='utf-8') as log_file:
                log_file.write(f"\n=== 位置交换 ===\n")
                log_file.write(f"交换 {position1}号位置({player2.role_type}) 和 {position2}号位置({player1.role_type})\n")

            return {
                "success": True,
                "message": f"成功交换{position1}号和{position2}号位置，配置已保存",
                "players": self.get_players()
            }

        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_position_info(self):
        """获取当前位置和角色信息

        Returns:
            dict: 位置信息
        """
        try:
            position_info = {}
            for i, player in enumerate(self.players):
                position_info[i+1] = {
                    "position": player.player_index,
                    "role": player.role_type,
                    "model_name": player.model.model_name,
                    "is_alive": player.is_alive
                }

            return {
                "success": True,
                "positions": position_info,
                "total_players": len(self.players)
            }

        except Exception as e:
            return {"success": False, "message": str(e)}