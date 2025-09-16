"""
狼人杀9人局"轻享版"积分计算器

积分规则：
1. 阵营分：胜利阵营每人+10分，失败阵营每人+0分
2. 贡献分：
   - 预言家：查验出狼人+5分
   - 女巫：救对人或毒死狼人+5分
   - 猎人：开枪带走狼人+5分
   - 狼人：击杀神民+5分（团队加分）
   - 村民：参与投票放逐狼人每次+3分
3. MVP加分：全场最佳+5分
"""

from typing import Dict, List, Any
from history import *


class PlayerScore:
    """玩家积分详情"""
    def __init__(self, player_index: int, role_type: str, is_winner: bool):
        self.player_index = player_index
        self.role_type = role_type
        self.is_winner = is_winner
        
        # 积分明细
        self.camp_score = 10 if is_winner else 0  # 阵营分
        self.contribution_score = 0  # 贡献分
        self.mvp_score = 0  # MVP分
        
        # 贡献详情
        self.contributions = []
        
    def add_contribution(self, description: str, score: int):
        """添加贡献分"""
        self.contributions.append(description)
        self.contribution_score += score
        
    def set_mvp(self):
        """设置为MVP"""
        self.mvp_score = 5
        
    def get_total_score(self) -> int:
        """获取总分"""
        return self.camp_score + self.contribution_score + self.mvp_score
        
    def get_score_detail(self) -> Dict[str, Any]:
        """获取积分详情"""
        return {
            "player_index": self.player_index,
            "role_type": self.role_type,
            "camp_score": self.camp_score,
            "contribution_score": self.contribution_score,
            "mvp_score": self.mvp_score,
            "total_score": self.get_total_score(),
            "contributions": self.contributions,
            "is_winner": self.is_winner
        }


class ScoreCalculator:
    """积分计算器"""
    
    def __init__(self, game):
        self.game = game
        self.player_scores = {}
        
    def calculate_scores(self, winner: str, mvp_player_index: int = None) -> Dict[int, PlayerScore]:
        """
        计算所有玩家的积分
        
        Args:
            winner: 胜利阵营 ("狼人胜利" 或 "村民胜利")
            mvp_player_index: MVP玩家编号
            
        Returns:
            Dict[int, PlayerScore]: 玩家编号到积分对象的映射
        """
        # 初始化玩家积分
        self._initialize_player_scores(winner)
        
        # 计算贡献分
        self._calculate_contribution_scores()
        
        # 设置MVP
        if mvp_player_index and mvp_player_index in self.player_scores:
            self.player_scores[mvp_player_index].set_mvp()
            
        return self.player_scores
        
    def _initialize_player_scores(self, winner: str):
        """初始化玩家积分"""
        self.player_scores = {}
        
        for player in self.game.players:
            is_winner = self._is_player_winner(player, winner)
            self.player_scores[player.player_index] = PlayerScore(
                player.player_index, 
                player.role_type, 
                is_winner
            )
            
    def _is_player_winner(self, player, winner: str) -> bool:
        """判断玩家是否属于胜利阵营"""
        if winner == "狼人胜利":
            return player.role_type == "狼人"
        elif winner == "村民胜利":
            return player.role_type != "狼人"
        return False
        
    def _calculate_contribution_scores(self):
        """计算贡献分"""
        history = self.game.history.get_history(show_all=True)
        
        # 分析历史事件，计算各种贡献
        self._calculate_seer_contributions(history)
        self._calculate_witch_contributions(history)
        self._calculate_hunter_contributions(history)
        self._calculate_wolf_contributions(history)
        self._calculate_villager_contributions(history)
        
    def _calculate_seer_contributions(self, history: List[Dict]):
        """计算预言家贡献分"""
        for player in self.game.players:
            if player.role_type == "预言家" and hasattr(player, 'divine_result'):
                # 检查是否查验出狼人
                wolf_found = False
                for result in player.divine_result:
                    if "狼人" in result:
                        wolf_found = True
                        break
                        
                if wolf_found:
                    self.player_scores[player.player_index].add_contribution(
                        "查验出狼人", 5
                    )
                    
    def _calculate_witch_contributions(self, history: List[Dict]):
        """计算女巫贡献分"""
        witch_player = self._find_witch_player()
        if not witch_player:
            return

        witch_cured = False
        witch_poisoned_wolf = False
        god_roles = ["预言家", "女巫", "猎人"]

        for round_data in history:
            night_events = round_data.get("夜晚事件", [])

            for event in night_events:
                # 检查救人（只加一次分）
                if "被女巫救治" in event and not witch_cured:
                    import re
                    match = re.search(r'【(\d+)号玩家】被女巫救治', event)
                    if match:
                        cured_player_idx = int(match.group(1))
                        cured_player = self.game.players[cured_player_idx - 1]
                        if cured_player.role_type in god_roles:
                            self.player_scores[witch_player.player_index].add_contribution(
                                f"成功救活神民（{cured_player.role_type}）", 5
                            )
                            witch_cured = True

                # 检查毒杀狼人（只加一次分）
                if "被投毒" in event and not witch_poisoned_wolf:
                    # 提取被毒玩家编号
                    import re
                    match = re.search(r'【(\d+)号玩家】被投毒', event)
                    if match:
                        poisoned_player_idx = int(match.group(1))
                        poisoned_player = self.game.players[poisoned_player_idx - 1]
                        if poisoned_player.role_type == "狼人":
                            self.player_scores[witch_player.player_index].add_contribution(
                                "毒杀狼人", 5
                            )
                            witch_poisoned_wolf = True
                                
    def _calculate_hunter_contributions(self, history: List[Dict]):
        """计算猎人贡献分"""
        hunter_player = self._find_hunter_player()
        if not hunter_player:
            return

        hunter_killed_wolf = False

        for round_data in history:
            day_events = round_data.get("白天事件", [])
            night_events = round_data.get("夜晚事件", [])

            all_events = day_events + night_events
            for event in all_events:
                if "被猎人反击杀死" in event and not hunter_killed_wolf:
                    # 提取被反击玩家编号
                    import re
                    match = re.search(r'【(\d+)号玩家】被猎人反击杀死', event)
                    if match:
                        attacked_player_idx = int(match.group(1))
                        attacked_player = self.game.players[attacked_player_idx - 1]
                        if attacked_player.role_type == "狼人":
                            self.player_scores[hunter_player.player_index].add_contribution(
                                "开枪带走狼人", 5
                            )
                            hunter_killed_wolf = True
                                
    def _calculate_wolf_contributions(self, history: List[Dict]):
        """计算狼人贡献分"""
        god_roles = ["预言家", "女巫", "猎人"]
        wolf_team_bonus_given = False
        
        for round_data in history:
            night_events = round_data.get("夜晚事件", [])
            
            for event in night_events:
                if "被杀死" in event and not wolf_team_bonus_given:
                    # 提取被杀玩家编号
                    import re
                    match = re.search(r'【(\d+)号玩家】被杀死', event)
                    if match:
                        killed_player_idx = int(match.group(1))
                        killed_player = self.game.players[killed_player_idx - 1]
                        if killed_player.role_type in god_roles:
                            # 给所有狼人加分
                            for player in self.game.players:
                                if player.role_type == "狼人":
                                    self.player_scores[player.player_index].add_contribution(
                                        "击杀神民", 5
                                    )
                            wolf_team_bonus_given = True
                            break
                            
    def _calculate_villager_contributions(self, history: List[Dict]):
        """计算村民贡献分"""
        for round_data in history:
            day_events = round_data.get("白天事件", [])
            
            for event in day_events:
                if "被处决" in event:
                    # 解析投票结果和被处决玩家
                    self._analyze_execution_event(event)
                    
    def _analyze_execution_event(self, event: str):
        """分析处决事件，给投票放逐狼人的村民加分"""
        import re
        
        # 提取被处决玩家编号
        executed_match = re.search(r'【(\d+)号玩家】被处决', event)
        if not executed_match:
            return
            
        executed_player_idx = int(executed_match.group(1))
        executed_player = self.game.players[executed_player_idx - 1]
        
        # 只有被处决的是狼人才给村民加分
        if executed_player.role_type != "狼人":
            return
            
        # 提取投票信息
        vote_matches = re.findall(r'【(\d+)号玩家】 投票给 (\d+)号玩家', event)
        
        for voter_idx_str, target_idx_str in vote_matches:
            voter_idx = int(voter_idx_str)
            target_idx = int(target_idx_str)
            
            # 如果投票目标是被处决的狼人
            if target_idx == executed_player_idx:
                voter = self.game.players[voter_idx - 1]
                # 只给村民加分
                if voter.role_type == "村民":
                    self.player_scores[voter_idx].add_contribution(
                        "投票放逐狼人", 3
                    )
                    
    def _find_witch_player(self):
        """找到女巫玩家"""
        for player in self.game.players:
            if player.role_type == "女巫":
                return player
        return None
        
    def _find_hunter_player(self):
        """找到猎人玩家"""
        for player in self.game.players:
            if player.role_type == "猎人":
                return player
        return None
        
    def get_ranking(self) -> List[Dict[str, Any]]:
        """获取积分排名"""
        ranking = []
        for player_score in self.player_scores.values():
            ranking.append(player_score.get_score_detail())
            
        # 按总分降序排列
        ranking.sort(key=lambda x: x["total_score"], reverse=True)
        
        return ranking
