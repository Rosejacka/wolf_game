from llm import BuildModel
import yaml
import json
import os



class Judge:
    def __init__(self, game, model_name, api_key, base_url=None):
        self.game = game
        self.model = BuildModel(model_name, api_key, force_json=True, base_url=base_url)
    
    '''
    根据当前的游戏状态，判断胜负，返回三种情况：
    村民胜利
    狼人胜利
    胜负未分
    '''
    def decide(self)->str:
        '''
            判断胜负需要知道以下信息:
            0. 游戏规则
            1. 每个玩家的身份
            2. 每个玩家的存活状态
            3. 当前是第几天
            4. 当前是白天还是黑夜
            5. 事件列表
        '''
        md_path = 'prompts/prompt_judge.md'
        yaml_path = 'prompts/prompt_judge.yaml'
        prompt_template = None
        if os.path.exists(md_path):
            # 解析md为dict
            def parse_prompt_md(md_path):
                result = {}
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
            prompt_template = parse_prompt_md(md_path)
        else:
            with open(yaml_path, 'r', encoding='utf-8') as file:
                prompt_template = yaml.safe_load(file)
        # 获取玩家信息并填充模板
        players = self.game.get_players()
        prompt_template['player_state'] = [
            {
                '玩家': p['name'],
                '角色': p['role_type'],
                '存活': '存活' if p['is_alive'] else '死亡'
            }
            for p in players.values()
        ]
        # 更新当前天数阶段
        prompt_template['day'] = f"当前是第{self.game.current_day}{self.game.current_phase}"
        # 更新事件
        prompt_template['curr_state'] = self.game.history.get_history(show_all=True)
        prompt_str = json.dumps(prompt_template, ensure_ascii=False)
        print(prompt_str)
        resp, _ = self.model.get_response(prompt_str)
        if resp:
            reason = resp['reason']
            print(reason)
            result = resp['result']
            return result
        #请求失败
        #TODO 需要重试，或者在llm类里面统一重试           
        return None