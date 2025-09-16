from llm import BuildModel
from history import *
from log import *
import yaml
import json
import time
import os
from datetime import datetime
import random

class BaseRole:
    def __init__(self, player_index, role_type, model_name, api_key, game, base_url=None):
        self.player_index = player_index
        self.role_type = role_type
        self.is_alive = True
        self.game = game
        self.model = BuildModel(model_name, api_key, force_json=True, base_url=base_url)


    def __str__(self):
        return f"你的玩家编号: {self.player_index}, 角色类型: {self.role_type}"

    def error(self, e, resp):
        print("\033[91m发生错误:\033[0m")
        print("\033[91m{}\033[0m".format(e))
        print("\033[91m{}\033[0m".format(resp))

    def get_players_state(self):
        state = []
        for player in self.game.players:
            state.append(f"{player.player_index}号玩家: {'存活' if player.is_alive else '死亡'}")
        return state

    def get_player_prompt_file(self, prompt_type):
        """根据玩家编号获取专属提示词文件路径，优先md格式，其次yaml格式"""
        player_prompt_md = f'prompts/players/player{self.player_index}/prompt_{prompt_type}.md'
        player_prompt_yaml = f'prompts/players/player{self.player_index}/prompt_{prompt_type}.yaml'
        if os.path.exists(player_prompt_md):
            return player_prompt_md
        elif os.path.exists(player_prompt_yaml):
            return player_prompt_yaml
        else:
            # 通用提示词
            common_md = f'prompts/prompt_{prompt_type}.md'
            common_yaml = f'prompts/prompt_{prompt_type}.yaml'
            if os.path.exists(common_md):
                return common_md
            else:
                return common_yaml

    def parse_prompt_md(self, md_path):
        """解析md格式的提示词为dict"""
        result = {}
        if not os.path.exists(md_path):
            return result
        with open(md_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        key = None
        value_lines = []
        for line in lines:
            if line.startswith('## '):
                if key:
                    result[key] = ''.join(value_lines).strip()
                key = line[3:].strip()
                value_lines = []
            else:
                value_lines.append(line)
        if key:
            result[key] = ''.join(value_lines).strip()
        # 列表字段特殊处理
        for k, v in result.items():
            if v.startswith('- '):
                result[k] = [item[2:].strip() for item in v.split('\n') if item.strip().startswith('- ')]
        return result

    def prompt_preprocess(self, prompt_template):
        # 兼容md和yaml两种格式
        replacements = {
            '角色': f"你是一名{self.role_type}",
            '第几天': f'当前是第{self.game.current_day}天',
            '你的玩家编号': f"你是{self.player_index}号玩家",
            '事件': self.game.history.get_history(),
            '玩家状态': self.get_players_state(),
            '随机数种子': int(time.time() * 1000) + random.randint(1, 1000)
        }
        for k, v in replacements.items():
            if k in prompt_template:
                prompt_template[k] = v
        return prompt_template

    def handle_action(self, prompt_file, extra_data=None, retry_count=0):
        if prompt_file.endswith('.md'):
            prompt_template = self.parse_prompt_md(prompt_file)
        else:
            with open(prompt_file, 'r', encoding='utf-8') as file:
                prompt_template = yaml.safe_load(file)
        prompt_dict = self.prompt_preprocess(prompt_template)
        # 获取公共规则（保留yaml）
        with open('prompts/prompt_game_rule.yaml', 'r', encoding='utf-8') as rule_file:
            prompt_gamerule = yaml.safe_load(rule_file)
            prompt_dict.update(prompt_gamerule)
        # 策略规则部分略
        if extra_data:
            prompt_dict.update(extra_data)
        prompt_str = json.dumps(prompt_dict, ensure_ascii=False)
        resp, reason = self.model.get_response(prompt_str)
        if resp is None:
            self.error("请求失败", prompt_str)
            if retry_count < 10:
                print_red("重新发起请求")
                time.sleep(10)
                return self.handle_action(prompt_file, extra_data, retry_count+1)
            return None
        required_fields = prompt_template.get('required_fields', [])
        if isinstance(required_fields, str):
            required_fields = [x.strip() for x in required_fields.split(',')]
        if required_fields:
            missing_fields = [field for field in required_fields if field not in resp]
            if missing_fields:
                self.error(f"响应缺少必要字段: {missing_fields}", resp)
                if retry_count < 10:
                    print_red("重新发起请求")
                    time.sleep(10)
                    return self.handle_action(prompt_file, extra_data, retry_count+1)
                return None
        # 日志部分保留
        with open(f'logs/llm_{self.game.start_time}.txt', 'a', encoding='utf-8') as log_file:
            log_file.write(f"--- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            log_file.write(f"--- {self.player_index}号玩家 ({self.role_type}) ---\n")
            log_file.write(f"---输入---:\n{prompt_str}\n")
            log_file.write(f"---输出---:\n{json.dumps(resp, ensure_ascii=False)}\n")
            if reason:
                log_file.write(f"---推理过程---:\n{reason}\n")
        return resp

    def speak(self, content, extra_data=None):
        if not content:
            if extra_data is None:
                extra_data={}
            prompt_file = self.get_player_prompt_file('speak')
            resp_dict = self.handle_action(prompt_file, extra_data)
            if resp_dict:
                self.game.history.add_event(SpeakEvent(self.player_index, resp_dict['speak']))
                return resp_dict
        else:
            self.game.history.add_event(SpeakEvent(self.player_index, content))
            return {'thinking':'', 'speak': content}

    def vote(self, vote_id, extra_data=None):
        if vote_id == -100:
            if extra_data is None:
                extra_data={}
            prompt_file = self.get_player_prompt_file('vote')
            resp_dict = self.handle_action(prompt_file, extra_data)
            if resp_dict:
                vote_id = resp_dict['vote']
                self.game.history.add_event(VoteEvent(self.player_index, vote_id))
                return resp_dict
        else:
            self.game.history.add_event(VoteEvent(self.player_index, vote_id))
            return {
                'vote': vote_id,
                'thinking': ''
            }
    def decide_vote(self, extra_data=None):
        """仅做投票决策，不记录历史、不落库，用于前端预取"""
        if extra_data is None:
            extra_data = {}
        prompt_file = self.get_player_prompt_file('vote')
        resp_dict = self.handle_action(prompt_file, extra_data)
        return resp_dict



    def last_words(self, speak, death_reason, extra_data=None):
        """发表遗言(死后)"""
        resp_dict = {}
        if extra_data is None:
            extra_data={}
        extra_data['reason'] = death_reason

        if not speak:
            prompt_file = self.get_player_prompt_file('lastword')
            resp_dict = self.handle_action(prompt_file, extra_data)
        else:
            resp_dict['speak'] = speak
            resp_dict['thinking'] = ''
        if resp_dict:
            self.game.history.add_event(LastWordEvent(self.player_index, resp_dict['speak']))

        return resp_dict

    def be_executed(self, vote_result):
        '''被放逐'''
        self.is_alive = False
        self.game.history.add_event(ExecuteEvent(self.player_index, vote_result))
        with open(f'logs/result_{self.game.start_time}.txt', 'a', encoding='utf-8') as log_file:
            log_file.write(f"【{self.game.current_day} {self.game.current_phase}】 【{self.player_index}】号【{self.role_type}】被处决\n")

    def be_attacked(self):
        '''被攻击'''
        self.is_alive = False
        self.game.history.add_event(AttackEvent(self.player_index))
        with open(f'logs/result_{self.game.start_time}.txt', 'a', encoding='utf-8') as log_file:
            log_file.write(f"【{self.game.current_day} {self.game.current_phase}】 【{self.player_index}】号【{self.role_type}】被猎人反击杀死\n")

    def be_killed(self):
        '''被杀'''
        self.is_alive = False
        self.game.history.add_event(KillEvent(self.player_index))
        with open(f'logs/result_{self.game.start_time}.txt', 'a', encoding='utf-8') as log_file:
            log_file.write(f"【{self.game.current_day} {self.game.current_phase}】 【{self.player_index}】号【{self.role_type}】被狼人杀死\n")

    def be_poisoned(self):
        '''被毒杀'''
        self.is_alive = False
        self.game.history.add_event(PoisonEvent(self.player_index))
        self.game.history.add_event(KillEvent(self.player_index))
        with open(f'logs/result_{self.game.start_time}.txt', 'a', encoding='utf-8') as log_file:
            log_file.write(f"【{self.game.current_day} {self.game.current_phase}】 【{self.player_index}】号【{self.role_type}】被女巫毒死\n")

    def be_cured(self):
        '''被治愈'''
        self.is_alive = True
        self.game.history.add_event(CureEvent(self.player_index))


class Villager(BaseRole):
    def __init__(self, player_index, model_name, api_key,  game, base_url=None):
        super().__init__(player_index, "村民", model_name, api_key, game, base_url)

class Hunter(BaseRole):
    def __init__(self, player_index, model_name, api_key,  game, base_url=None):
        super().__init__(player_index, "猎人", model_name, api_key,  game, base_url)

    def make_extra_data(self):
        extra_data = {
            "猎人技能": "当猎人被狼人杀死或者被投票出局时，猎人可以选择发动反击技能带走一名玩家"
        }
        return extra_data

    def last_words(self, speak, death_reason):
        extra_data = self.make_extra_data()
        return super().last_words(speak, death_reason, extra_data)

    def revenge(self, death_reason):
        extra_data = {
            "出局的原因": death_reason
        }
        prompt_file = self.get_player_prompt_file('hunter_revenge')
        resp_dict = self.handle_action(prompt_file, extra_data)
        if resp_dict and resp_dict.get('attack', -1) != -1:
            # 记录猎人反击事件
            hunter_event = HunterRevengeEvent(self.player_index, resp_dict['attack'])
            self.game.history.add_event(hunter_event)
        return resp_dict


class Seer(BaseRole):
    def __init__(self, player_index, model_name, api_key, game, base_url=None):
        super().__init__(player_index, "预言家", model_name, api_key, game, base_url)
        self.divine_result = []

    def make_extra_data(self):
        extra_data = None
        if len(self.divine_result) > 0:
            extra_data = {'你已经掌握的信息': self.divine_result}
        return extra_data

    def last_words(self, speak, death_reason):
        """发表遗言(死后)"""
        extra_data = self.make_extra_data()
        return super().last_words(speak, death_reason, extra_data)

    def speak(self, content):
        extra_data = self.make_extra_data()
        return super().speak(content, extra_data)

    def vote(self, vote_id):
        extra_data = self.make_extra_data()
        return super().vote(vote_id, extra_data)

    def divine(self):
        """决定查看谁的身份"""
        extra_data = self.make_extra_data()
        prompt_file = self.get_player_prompt_file('divine')
        resp_dict = self.handle_action(prompt_file, extra_data)
        if resp_dict:
            divine_id = resp_dict['divine']
            is_good_man = "好人" if self.game.players[divine_id-1].role_type != "狼人" else "狼人"
            self.divine_result.append(
                f"【{divine_id}号玩家】是 {is_good_man}."
            )

            # 记录预言家查验事件
            divine_event = DivineEvent(self.player_index, divine_id, is_good_man)
            self.game.history.add_event(divine_event)

            return resp_dict


class Wolf(BaseRole):
    def __init__(self, player_index, model_name, api_key,  game, base_url=None):
        super().__init__(player_index, "狼人", model_name, api_key,  game, base_url)


    def make_extra_data(self):
        wolves  = self.game.get_wolves()
        wolves_list = []
        for wolf in wolves:
            if wolf["player_index"] == self.player_index:
                continue
            is_alive = "存活" if wolf["is_alive"] else "已死亡"
            wolves_list.append(f"{wolf['player_index']}号玩家是狼人, 目前{is_alive}")
        extra_data = {
            "你的狼人队友": wolves_list
        }
        return extra_data

    def last_words(self, speak, death_reason):
        """发表遗言(死后)"""
        extra_data = self.make_extra_data()
        return super().last_words(speak, death_reason, extra_data)

    def vote(self, vote_id):
        extra_data = self.make_extra_data()
        return super().vote(vote_id, extra_data)

    def speak(self, content):
        extra_data = self.make_extra_data()
        return super().speak(content, extra_data)

    def decide_vote(self, extra_data=None):
        """仅做投票决策时也提供狼人队友信息"""
        my_extra = self.make_extra_data()
        if extra_data:
            # 合并额外上下文（如存活列表、上次投票无效提示等）
            my_extra.update(extra_data)
        return super().decide_vote(my_extra)



    def decide_kill(self, kill_id, want_kill=None):
        extra_data = self.make_extra_data()
        if want_kill:
            extra_data['第几轮投票'] = 2
            extra_data['第一轮投票结果'] = want_kill
        else:
            extra_data['第几轮投票'] = 1
        resp_dict = {}
        if kill_id == -100:
            prompt_file = self.get_player_prompt_file('kill')
            resp_dict = self.handle_action(prompt_file, extra_data)
        else:
            resp_dict['kill'] = kill_id
            resp_dict['reason'] = ''
        if resp_dict:
            return resp_dict



class Witch(BaseRole):
    def __init__(self, player_index, model_name, api_key,  game, base_url=None):
        super().__init__(player_index, "女巫", model_name, api_key,  game, base_url)
        self.cured_someone = 0
        self.poisoned_someone = -1

    def make_extra_data(self):
        extra_data = {
            'cured_someone': f'已经使用解药救过{self.cured_someone}号玩家，不允许再次使用解药技能' if self.cured_someone != 0 else "还没使用过救治技能",
            'poisoned_someone': f'已经使用毒药杀了{self.poisoned_someone}号玩家，不允许再次使用毒药技能' if self.poisoned_someone != -1 else "还没使用过毒杀技能"
        }
        return extra_data

    def last_words(self, speak, death_reason):
        """发表遗言(死后)"""
        extra_data = self.make_extra_data()
        return super().last_words(speak, death_reason, extra_data)

    def vote(self, vote_id):
        extra_data = self.make_extra_data()
        return super().vote(vote_id, extra_data)

    def speak(self, content):
        extra_data = self.make_extra_data()
        return super().speak(content, extra_data)

    def decide_cure_or_poison(self, someone_will_be_killed):
        """决定是否要治疗或毒杀"""
        extra_data = self.make_extra_data()
        if someone_will_be_killed != -1:
            extra_data['今晚发生了什么'] = f'{someone_will_be_killed}号玩家将被杀害'
        else:
            extra_data['今晚发生了什么'] = "没有人将被杀害"
        prompt_file = self.get_player_prompt_file('cure_or_poison')
        resp_dict = self.handle_action(prompt_file, extra_data)
        if resp_dict:
            # 记录女巫行动事件
            if resp_dict['cure'] == 1 and someone_will_be_killed != -1:
                witch_event = WitchActionEvent(self.player_index, "cure", someone_will_be_killed)
                self.game.history.add_event(witch_event)
                # 仅在首次使用时记录已使用解药的目标，之后不再被后续夜晚覆盖为未使用
                if self.cured_someone == 0:
                    self.cured_someone = someone_will_be_killed

            if resp_dict['poison'] != -1:
                witch_event = WitchActionEvent(self.player_index, "poison", resp_dict['poison'])
                self.game.history.add_event(witch_event)
                self.poisoned_someone = resp_dict['poison']

            return resp_dict