import GameData from "./data.js";
import {
    DivineAction,
    EndDayAction,
    EndNightAction,
    ExecuteAction,
    SpeakAction,
    VoteAction,
    WolfAction,
    WitchAction,
    CheckWinnerAction
} from "./action.js";

class Game {
    constructor(ui) {
        this.gameData = new GameData();
        this.players = {}
        this.ui = ui;
        this.current_action_index  = 0;
        this.deaths = []; //死亡名单
        this.display_role = true;
        this.display_thinking = true;
        this.display_witch_action = true;
        this.display_wolf_action = true;
        this.display_hunter_action = true;
        this.display_divine_action = true;
        this.display_vote_action = true;
        this.display_model = true;
        this.auto_play = true;
    }
    clear_deaths() {
        this.deaths = [];
    }

    async someone_die(player_idx, death_reason) {
        console.log(`被杀死的玩家是：${player_idx}`);
        this.deaths.push(player_idx);

        await this.ui.killPlayer(player_idx);
        const result = await this.gameData.getCurrentTime();
        console.log(result);
        if (1 == result.current_day || (result.current_phase == "白天" && death_reason=="被投票处决")) {
            let speak_content = "";
            if (this.players[player_idx - 1].is_human) {
                speak_content = await this.ui.showHumanInput(`请输入你的遗言`);
            }

            //如果是第一夜，允许发表遗言
            const result = await this.gameData.lastWords({ player_idx: player_idx, speak: speak_content,  death_reason: death_reason });
            console.log(result);

            await this.ui.showPlayer(player_idx);
            const role = this.display_role ? this.players[player_idx - 1].role_type : "玩家";
            if (this.display_thinking) {
                await this.ui.speak(`${player_idx}号 ${role} 思考中：`, this.auto_play,result.thinking, true);
            }
            await this.ui.speak(`${player_idx}号 ${role} 发表遗言：`, this.auto_play,result.speak);
            await this.ui.hidePlayer();
        }
        //如果是猎人，并且不是被毒杀，允许反击
        const  hunter = this.get_hunter();
        if (hunter.index == player_idx && death_reason != "被女巫毒杀") {
            const result = await this.gameData.revenge({ player_idx: player_idx, death_reason: death_reason });
            console.log(result);
            if (result.attack !== -1) {
                await this.gameData.attack({ player_idx: player_idx, target_idx: result.attack });
                await this.someone_die(result.attack, "被猎人杀死");
                console.log(`猎人发动反击，杀死了：${result.attack}号玩家`);
            } else {
                console.log(`猎人决定不反击`);
            }
        }
    }

    async start() {
        console.log("== Start Game ==");
        const result = await this.gameData.startGame();
        console.log(result);
        this.display_role = result.display_role;
        this.display_thinking = result.display_thinking;
        this.display_witch_action = result.display_witch_action;
        this.display_wolf_action = result.display_wolf_action;
        this.display_hunter_action = result.display_hunter_action;
        this.display_divine_action = result.display_divine_action;
        this.display_vote_action = result.display_vote_action;
        this.display_model = result.display_model;
        this.auto_play = result.auto_play;


        ///获取玩家列表
        const playersData = await this.gameData.getStatus();
        this.players = Object.values(playersData);
        console.log(this.players);

        ///设置模型logo
        const model_name = {
            "o3-mini": "gpt",
            "o3-mini-2025-01-31": "gpt",
            "deepseek-ai/DeepSeek-R1": "deepseek",
            "Pro/deepseek-ai/DeepSeek-R1": "deepseek",
            "gemini-2.0-flash-thinking-exp-01-21": "gemini",
            "qwen-max-2025-01-25":"qwen",
            "moonshot-v1-32k":"kimi",
            "glm-4-plus":"glm",
            "Baichuan4":"baichuan",
            "ep-20250216231709-2qcrf":"deepseek",
            "ep-20250216184924-4n4b2":"doubao",
            "hunyuan-large":"hunyuan"
        };
        for (const player of this.players) {
            if (player.model in model_name && this.display_model) {
                this.ui.showModelLogo(player.index, model_name[player.model]);
            }
            if (this.display_role || (this.display_wolf_action && player.role_type == "狼人")) {
                this.ui.showRoleText(player.index, player.role_type);
            }
        }

        ///按顺序设置行动类
        this.actions = []
        this.actions.push(new DivineAction(this));
        this.actions.push(new WolfAction(this));
        this.actions.push(new WitchAction(this));
        this.actions.push(new CheckWinnerAction(this));//检查胜利
        this.actions.push(new EndNightAction(this));
        for (const player of this.players) {
            this.actions.push(new SpeakAction(this, player.index));
        }
        for (const player of this.players) {
            this.actions.push(new VoteAction(this, player.index));
        }

        ///白天最后一个环节是处决投票
        this.actions.push(new ExecuteAction(this));
        this.actions.push(new CheckWinnerAction(this));//检查胜利
        this.actions.push(new EndDayAction(this));
    }

    async run() {
        //更新玩家状态
        const playersData = await this.gameData.getStatus();
        this.players = Object.values(playersData);

        const action = this.actions[this.current_action_index++];
        this.current_action_index = this.current_action_index % this.actions.length;

        // 执行行动
        const result = await action.do();

        return result;
    }

    // 在当前行动开始播放时，异步预取下一有效行动（会跳过出局/人类/无效目标）
    prefetchNextAction() {
        try {
            const n = this.actions.length;
            if (!n) return;
            let i = this.current_action_index % n;
            // 最多向前查看一轮，找到第一个可预取的候选
            for (let step = 0; step < n; step++) {
                const nextAction = this.actions[i];
                if (!nextAction) break;

                // 预取下一个发言内容（仅AI、且存活）
                if (nextAction instanceof SpeakAction) {
                    const idx = nextAction.player_idx;
                    const player = this.players[idx - 1];
                    if (player && player.is_alive && !player.is_human) {
                        this.gameData.prefetchSpeak({ player_idx: idx, content: "" });
                        return;
                    }
                }

                // 预言家预取（仅预言家存活）
                if (nextAction instanceof DivineAction) {
                    const seer = this.get_diviner();
                    if (seer && seer.is_alive) {
                        this.gameData.prefetchDivine({ player_idx: seer.index });
                        return;
                    }
                }

                // 女巫决策依赖“所有狼人投票结果”，为避免使用未完整投票的中间态，这里不做预取
                // if (nextAction instanceof WitchAction) { ... }

                // 夜转白/白转夜后需要时间信息
                if (nextAction instanceof EndNightAction) {
                    this.gameData.prefetchCurrentTime();
                    return;
                }

                // 执行环节前，预取投票汇总
                if (nextAction instanceof ExecuteAction) {
                    this.gameData.prefetchGetVoteResult();
                    return;
                }

                // 胜负判断不做预取，避免状态变更（如猎人开枪）前缓存旧结果
                if (nextAction instanceof CheckWinnerAction) {
                    return;
                }

                // 不可预取则继续向后查看
                i = (i + 1) % n;
            }
        } catch (e) {
            console.warn('预取下一行动失败: ', e);
        }
    }


    get_diviner() {
        return this.players.find(player => player.role_type === "预言家");
    }

    get_wolves() {
        return this.players.filter(player => player.role_type === "狼人");
    }

    get_witch() {
        return this.players.find(player => player.role_type === "女巫");
    }

    get_hunter() {
        return this.players.find(player => player.role_type === "猎人");
    }

    async refreshPlayerStatus() {
        /**
         * 刷新玩家状态 - 当位置控制更改后调用
         */
        try {
            console.log('正在刷新玩家状态...');

            // 重新获取玩家数据
            const playersData = await this.gameData.getStatus();
            this.players = Object.values(playersData);

            // 更新UI显示
            await this.ui.updatePlayersDisplay(this.players);

            // 强制重新渲染游戏界面
            if (this.ui.app && this.ui.app.renderer) {
                this.ui.app.renderer.render(this.ui.app.stage);
            }

            console.log('玩家状态刷新完成');
            console.log('当前玩家配置:', this.players.map(p => ({
                index: p.player_index,
                role: p.role_type,
                model: p.model_name,
                alive: p.is_alive
            })));

            // 显示刷新成功的提示
            if (this.ui.showBigText) {
                await this.ui.showBigText("位置配置已更新", 1500);
            }

        } catch (error) {
            console.error('刷新玩家状态时出错:', error);
        }
    }
}

export default Game;