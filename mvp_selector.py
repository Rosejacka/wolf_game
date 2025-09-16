"""
基于大模型的 MVP 评选器
- 输入：game（包含玩家、历史事件）、可选的已有排名/胜负
- 输出：{"mvp_player_index": int, "reason": str, "model": str}

实现思路：
1) 从 config.json 读取用于评审的模型（优先使用 judge 字段），否则回退到第一个 models 配置
2) 汇总玩家身份、生存状态、贡献（用 ScoreCalculator 先算不含 MVP 的分，便于给大模型量化参考）
3) 提供完整事件历史（History.get_history(show_all=True)）作为上下文
4) 让大模型只输出 JSON，包含 mvp_player_index 和简明理由 reason（不超过120字）
5) 失败时回退为当前总分最高的玩家，并给出回退理由
"""
from typing import Dict, Any, List, Optional
import json
import os

from llm import BuildModel
from score_calculator import ScoreCalculator


class MvpSelector:
    def __init__(self):
        self.model_name = None
        self.api_key = None
        self.base_url = None
        self._load_model_from_config()
        # 创建模型实例（force_json=True 以鼓励输出JSON）
        self.model = BuildModel(self.model_name, self.api_key, force_json=True, base_url=self.base_url)

    def _load_model_from_config(self):
        cfg = {}
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}
        # 优先使用 judge 模型
        judge = (cfg or {}).get('judge') or {}
        if judge.get('model_name') and judge.get('api_key'):
            self.model_name = judge.get('model_name')
            self.api_key = judge.get('api_key')
            self.base_url = judge.get('base_url')
            return
        # 其次使用 models 列表第一个
        models = (cfg or {}).get('models') or []
        if models:
            self.model_name = models[0].get('model_name')
            self.api_key = models[0].get('api_key')
            self.base_url = models[0].get('base_url')
        else:
            # 最后回退：占位，调用时很可能失败，但保持字段存在
            self.model_name = 'gpt-4.1'
            self.api_key = ''
            self.base_url = None

    def select(self, game, winner: str, precomputed_ranking: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        # 1) 构造量化信息：不含 MVP 的基础积分/排名
        calculator = ScoreCalculator(game)
        base_scores = calculator.calculate_scores(winner, mvp_player_index=None)
        base_ranking = calculator.get_ranking()

        # 2) 玩家与身份、生存
        players_brief = []
        for p in game.players:
            players_brief.append({
                'player_index': p.player_index,
                'role_type': p.role_type,
                'is_alive': p.is_alive
            })

        # 3) 事件历史与“发言全文”
        history = []
        speeches_full = {}
        try:
            if game.history:
                history = game.history.get_history(show_all=True)
                # 结构化收集所有发言与遗言全文
                for round_obj in getattr(game.history, 'rounds', []):
                    # day_events 为白天事件
                    for ev in getattr(round_obj, 'day_events', []):
                        if getattr(ev, 'event_type', '') in ('speak', 'last_word'):
                            arr = speeches_full.setdefault(ev.player_idx, [])
                            arr.append({
                                'day': getattr(round_obj, 'day', getattr(round_obj, 'day_count', None)),
                                'phase': '白天',
                                'type': ev.event_type,
                                'text': getattr(ev, 'description', '')
                            })
                    # 夜晚事件一般没有发言，但也遍历保障
                    for ev in getattr(round_obj, 'night_events', []):
                        if getattr(ev, 'event_type', '') in ('speak', 'last_word'):
                            arr = speeches_full.setdefault(ev.player_idx, [])
                            arr.append({
                                'day': getattr(round_obj, 'day', getattr(round_obj, 'day_count', None)),
                                'phase': '夜晚',
                                'type': ev.event_type,
                                'text': getattr(ev, 'description', '')
                            })
        except Exception:
            history = []
            speeches_full = {}

        # 4) 组装提示词
        prompt = {
            'task': '在以下狼人杀对局中，评选出全场最佳 MVP。',
            'rules': [
                '只选择一名玩家作为 MVP，返回其座位编号 player_index（1-9）。',
                '综合考虑贡献分、关键操作、带队能力、信息准确度、生存时长与对胜负影响。',
                '避免奖励“误导队友、恶意捣乱”的行为。',
                '请仅输出 JSON：{"mvp_player_index": number, "reason": "不超过120字的中文理由"}'
            ],
            'winner': winner,
            'players': players_brief,
            'base_ranking_without_mvp': base_ranking,
            'events_history': history,
            'speeches_full': speeches_full  # 每位玩家的发言/遗言全文（结构化）
        }

        # 5) 调用大模型
        content, _reasoning = self.model.generate(json.dumps(prompt, ensure_ascii=False))

        # 6) 解析
        mvp_index = None
        reason = None
        try:
            data = json.loads(content) if isinstance(content, str) else content
            mvp_index = int(data.get('mvp_player_index')) if data and 'mvp_player_index' in data else None
            reason = data.get('reason') if data else None
        except Exception:
            pass

        # 合法性校验
        if not mvp_index or not (1 <= mvp_index <= 9):
            # 回退：选择当前总分第一名
            fallback_index = base_ranking[0]['player_index'] if base_ranking else 1
            fallback_role = ''
            try:
                fallback_role = next((x['role_type'] for x in base_ranking if x['player_index'] == fallback_index), '')
            except Exception:
                pass
            return {
                'mvp_player_index': fallback_index,
                'reason': reason or f"模型未返回有效结果，回退为总分最高的玩家（{fallback_index}号{fallback_role}）",
                'model': self.model_name,
                'auto': True
            }

        return {
            'mvp_player_index': mvp_index,
            'reason': (reason or '').strip() or '综合贡献与关键决策表现最佳',
            'model': self.model_name,
            'auto': True
        }

