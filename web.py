from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from game import WerewolfGame
from tts_service import tts_service
import json
import sys
import copy


class PlayerAction(BaseModel):
    player_idx:int

class SpeakAction(BaseModel):
    player_idx: int
    content: str = None

class VoteAction(BaseModel):
    player_idx: int
    vote_id: int = -100
class DecideVoteAction(BaseModel):
    player_idx: int


class LastWordsAction(BaseModel):
    player_idx: int
    speak: str = None
    death_reason: str

class AttackAction(BaseModel):
    player_idx: int
    target_idx: int

class DecideKillAction(BaseModel):
    player_idx: int
    kill_id: int = -100
    is_second_vote: bool

class DecideCureOrPoisonAction(BaseModel):
    player_idx: int

class TTSAction(BaseModel):
    text: str
    voice: Optional[str] = None
    model: str = "tts-1"
    use_cache: bool = True

class PoisonAction(BaseModel):
    player_idx: int

class RevengeAction(BaseModel):
    player_idx: int
    death_reason: str

class ManualPositionAction(BaseModel):
    position_mapping: dict  # {position: player_data} 格式，例如 {1: {"role": "狼人", "model_name": "gpt-4"}}

class SwapPositionAction(BaseModel):
    position1: int
    position2: int


class Recorder():
    def __init__(self, game):
        self.log = []
        self.is_loaded = False
        self.index  = 0

    def record(self, response):
        self.log.append(
            {
                "response": copy.deepcopy(response)
            }
        )

        with open(f"logs/replay_{game.start_time}.json", 'w') as f:
            json.dump(self.log, f)

    def load(self, filename):
        print("加载日志文件")
        with open(filename, 'r') as f:
            self.log = json.load(f)
            self.is_loaded = True

    def fetch(self):
        result = self.log[self.index]
        self.index += 1
        return result["response"]


game = WerewolfGame()
recorder = Recorder(game)

app = FastAPI()
# 设置静态文件目录
app.mount("/static", StaticFiles(directory="public"), name="public")

@app.get("/")
def default():
    return RedirectResponse(url="/static/index.html")

@app.get("/start")
def start_game():
    if recorder.is_loaded:
        display_config = recorder.fetch()
        display_config["auto_play"] = False
        display_config["display_role"] = True
        display_config["display_thinking"] = True
        display_config["display_vote_action"] = True
        display_config["display_divine_action"] = True
        display_config["display_witch_action"] = True
        display_config["display_wolf_action"] = True
        display_config["display_hunter_action"] = True
        display_config["display_model"] = True
        return display_config

    display_config = game.start()
    recorder.record(display_config)
    return display_config

@app.get("/status")
def get_status():
    if recorder.is_loaded:
        return recorder.fetch()
    players = game.get_players()
    recorder.record(players)
    return players

@app.post("/divine")
def divine(action: PlayerAction):
    if recorder.is_loaded:
        return recorder.fetch()
    result = game.divine(action.player_idx)
    recorder.record(result)
    return result


@app.post("/reset_wolf_want_kill")
def reset_wolf_want_kill():
    if recorder.is_loaded:
        return recorder.fetch()
    game.reset_wolf_want_kill()
    recorder.record({"message": "狼人想杀的目标已重置"})
    return {"message": "狼人想杀的目标已重置"}

@app.get("/get_wolf_want_kill")
def get_wolf_want_kill():
    if recorder.is_loaded:
        return recorder.fetch()
    result = game.get_wolf_want_kill()
    wolf_want_kill = {"wolf_want_kill": result}
    recorder.record(wolf_want_kill)
    return wolf_want_kill


@app.post("/decide_kill")
def decide_kill(action: DecideKillAction):
    if recorder.is_loaded:
        return recorder.fetch()
    result = game.decide_kill(action.player_idx, action.kill_id, action.is_second_vote)
    recorder.record(result)
    return result

@app.post("/kill")
def kill(action: PlayerAction):
    if recorder.is_loaded:
        return recorder.fetch()
    game.kill(action.player_idx)
    recorder.record({"message": f"玩家 {action.player_idx} 被杀死"})
    return {"message": f"玩家 {action.player_idx} 被杀死"}

@app.get("/current_time")
def get_current_time():
    if recorder.is_loaded:
        return recorder.fetch()

    current_time = {
        "current_day": game.get_day(),
        "current_phase": game.current_phase
    }
    recorder.record(current_time)
    return current_time


@app.post("/last_words")
def last_words(action: LastWordsAction):
    if recorder.is_loaded:
        return recorder.fetch()
    result = game.last_words(action.player_idx, action.speak, action.death_reason)
    recorder.record(result)
    return result


@app.post("/attack")
def attack(action: AttackAction):
    if recorder.is_loaded:
        return recorder.fetch()
    attack_result = game.attack(action.target_idx)
    players = game.get_players()
    result = {
        "message": f"{players[action.player_idx]['name']} 攻击了 {players[action.target_idx]['name']}",
        "attacked_player": action.target_idx
    }
    recorder.record(result)
    return result

@app.post("/toggle_day_night")
def toggle_day_night():
    if recorder.is_loaded:
        return recorder.fetch()
    game.toggle_day_night()
    recorder.record({"message": "Day/Night toggled"})
    return {"message": "Day/Night toggled"}



@app.post("/decide_cure_or_poison")
def decide_cure_or_poison(action: DecideCureOrPoisonAction):
    if recorder.is_loaded:
        return recorder.fetch()
    result = game.decide_cure_or_poison(action.player_idx)
    recorder.record(result)
    return result


@app.post("/poison")
def poison(action: PoisonAction):
    if recorder.is_loaded:
        return recorder.fetch()
    game.poison(action.player_idx)
    recorder.record({"message": f"玩家 {action.player_idx} 被毒死"})
    return {"message": f"玩家 {action.player_idx} 被毒死"}

@app.post("/cure")
def cure(action: PlayerAction):
    if recorder.is_loaded:
        return recorder.fetch()
    game.cure(action.player_idx)
    recorder.record({"message": "治疗成功"})
@app.post("/decide_vote")
def decide_vote(action: DecideVoteAction):
    if recorder.is_loaded:
        return recorder.fetch()
    result = game.decide_vote(action.player_idx)
    recorder.record(result)
    return result

@app.post("/speak")
def speak(action: SpeakAction):
    if recorder.is_loaded:
        return recorder.fetch()

    # 先获取发言结果
    result = game.speak(action.player_idx, action.content)

    # 在白天阶段且存在可读发言内容时，尝试生成TTS并将音频路径附加到结果中
    try:
        if game.current_phase == "白天" and result and isinstance(result, dict):
            speak_text = result.get("speak", "") if hasattr(result, "get") else ""
            if isinstance(speak_text, str) and speak_text.strip():
                if tts_service.is_available():
                    audio_path = tts_service.generate_speech(
                        text=speak_text,
                        voice=None,      # 不指定音色，交由服务端随机选择
                        model="tts-1",
                        use_cache=True   # 允许缓存，预取多次也不会重复生成
                    )
                    if audio_path:
                        result["audio_path"] = audio_path
    except Exception as e:
        # 生成TTS失败不影响原始发言返回
        print(f"[WARN] 预生成TTS失败: {e}")

    recorder.record(result)
    return result


@app.post("/vote")
def vote(action: VoteAction):
    if recorder.is_loaded:
        return recorder.fetch()
    result = game.vote(action.player_idx, action.vote_id)
    recorder.record(result)
    return result

@app.post("/reset_vote_result")
def reset_vote_result():
    if recorder.is_loaded:
        return recorder.fetch()
    game.reset_vote_result()
    recorder.record({"message": "投票结果已重置"})
    return {"message": "投票结果已重置"}

@app.get("/get_vote_result")
def get_vote_result():
    if recorder.is_loaded:
        return recorder.fetch()
    result = game.get_vote_result()
    recorder.record({"vote_result": result})
    return {"vote_result": result}

@app.post("/revenge")
def revenge(action: RevengeAction):
    if recorder.is_loaded:
        return recorder.fetch()
    result = game.revenge(action.player_idx, action.death_reason)
    recorder.record(result)
    return result

@app.post("/execute")
def execute():
    if recorder.is_loaded:
        return recorder.fetch()
    players = game.get_players()
    vote_results = game.get_vote_result()

    if not vote_results:
        recorder.record({"message": "没有投票结果", "executed_player": -1})
        return {
            "message": "没有投票结果",
            "executed_player": -1
        }

    # 统计每个玩家获得的票数
    votes = {}
    for vote in vote_results:
        if vote["vote_id"] != -1:  # 排除弃票
            votes[vote["vote_id"]] = votes.get(vote["vote_id"], 0) + 1

    if not votes:  # 如果所有人都弃票
        return {
            "message": "所有人都弃票了",
            "executed_player": -1
        }

    max_votes = max(votes.values())
    voted_out = [player for player, count in votes.items() if count == max_votes]

    if len(voted_out) > 1:
        return {
            "message": "投票结果有多个，没人被处决",
            "executed_player": -1
        }
    else:
        voted_out_player = voted_out[0]
        game.execute(voted_out_player, vote_results)
        recorder.record({"message": f"{players[voted_out_player]['name']} 被处决!", "executed_player": voted_out_player})
        return {
            "message": f"{players[voted_out_player]['name']} 被处决!",
            "executed_player": voted_out_player
        }

@app.get("/check_winner")
def check_winner():
    if recorder.is_loaded:
        return recorder.fetch()
    result = game.check_winner()
    recorder.record({"winner": result})
    return {"winner": result}

@app.post("/manual_position")
def set_manual_position(action: ManualPositionAction):
    """手动设置玩家位置和角色分配"""
    if recorder.is_loaded:
        return recorder.fetch()

    try:
        result = game.set_manual_position(action.position_mapping)
        recorder.record(result)
        return result
    except Exception as e:
        error_result = {"success": False, "message": f"设置位置失败: {str(e)}"}
        recorder.record(error_result)
        return error_result

@app.post("/swap_position")
def swap_position(action: SwapPositionAction):
    """交换两个位置的玩家"""
    if recorder.is_loaded:
        return recorder.fetch()

    try:
        result = game.swap_players_position(action.position1, action.position2)
        recorder.record(result)
        return result
    except Exception as e:
        error_result = {"success": False, "message": f"交换位置失败: {str(e)}"}
        recorder.record(error_result)
        return error_result

@app.get("/get_position_info")
def get_position_info():
    """获取当前位置和角色信息"""
    if recorder.is_loaded:
        return recorder.fetch()

    result = game.get_position_info()
    recorder.record(result)
    return result

@app.get("/get_history")
def get_history():
    """获取游戏历史记录"""
    if recorder.is_loaded:
        return recorder.fetch()

    if game.history:
        result = game.history.get_history(show_all=True)
        recorder.record(result)
        return result
    else:
        result = []
        recorder.record(result)
        return result




@app.get("/get_game_scores")
def get_game_scores():
    """获取游戏积分数据"""
    if recorder.is_loaded:
        return recorder.fetch()

    scores = game.get_game_scores()
    if scores:
        recorder.record(scores)
        return scores
    else:
        result = {"message": "游戏尚未结束或积分未计算"}
        recorder.record(result)
        return result

@app.post("/set_mvp")
def set_mvp(action: dict):
    """设置MVP玩家"""
    if recorder.is_loaded:
        return recorder.fetch()

    try:
        mvp_player_index = action.get("mvp_player_index")
        if not mvp_player_index or not (1 <= mvp_player_index <= 9):
            result = {"success": False, "message": "无效的MVP玩家编号"}
            recorder.record(result)
            return result

        success = game.set_mvp(mvp_player_index)
        if success:
            result = {"success": True, "message": f"{mvp_player_index}号玩家被设为MVP"}
            recorder.record(result)
            return result
        else:
            result = {"success": False, "message": "设置MVP失败，游戏可能尚未结束"}
            recorder.record(result)
            return result
    except Exception as e:
        result = {"success": False, "message": f"设置MVP出错: {str(e)}"}
        recorder.record(result)
        return result

@app.post("/generate_tts")
def generate_tts(action: TTSAction):
    """生成TTS语音文件"""
    if recorder.is_loaded:
        return recorder.fetch()

    try:
        # 检查TTS服务是否可用
        if not tts_service.is_available():
            result = {"success": False, "message": "TTS服务不可用，请检查OpenAI API配置"}
            recorder.record(result)
            return result

        # 生成语音文件
        audio_path = tts_service.generate_speech(
            text=action.text,
            voice=action.voice,
            model=action.model,
            use_cache=action.use_cache
        )

        if audio_path:
            result = {
                "success": True,
                "audio_path": audio_path,
                "message": "TTS语音生成成功"
            }
            recorder.record(result)
            return result
        else:
            result = {"success": False, "message": "TTS语音生成失败"}
            recorder.record(result)
            return result

    except Exception as e:
        result = {"success": False, "message": f"TTS生成出错: {str(e)}"}
        recorder.record(result)
        return result

@app.get("/tts_status")
def get_tts_status():
    """获取TTS服务状态"""
    if recorder.is_loaded:
        return recorder.fetch()

    try:
        is_available = tts_service.is_available()
        result = {
            "available": is_available,
            "message": "TTS服务可用" if is_available else "TTS服务不可用"
        }
        recorder.record(result)
        return result
    except Exception as e:
        result = {"available": False, "message": f"检查TTS状态出错: {str(e)}"}
        recorder.record(result)
        return result

@app.post("/clear_tts_cache")
def clear_tts_cache():
    """清理TTS缓存"""
    if recorder.is_loaded:
        return recorder.fetch()

    try:
        deleted_count = tts_service.clear_cache()
        result = {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"已清理 {deleted_count} 个缓存文件"
        }
        recorder.record(result)
        return result
    except Exception as e:
        result = {"success": False, "message": f"清理缓存出错: {str(e)}"}
        recorder.record(result)
        return result

if __name__ == "__main__":
    import uvicorn
    if len(sys.argv) > 1:
        log_path = sys.argv[1]
        recorder.load(log_path)

    uvicorn.run(app, host="127.0.0.1", port=8000, timeout_keep_alive=1800)