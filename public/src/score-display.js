/**
 * 积分展示模块
 * 负责显示游戏结束后的积分统计和排名
 */

class ScoreDisplay {
    constructor() {
        this.scoreData = null;
        this.mvpVoted = false;
    }

    /**
     * 显示积分界面
     */
    async show(winner) {
        try {
            // 获取积分数据
            const response = await fetch('/get_game_scores');
            this.scoreData = await response.json();
            
            if (!this.scoreData.ranking) {
                console.log("积分数据不完整，跳过积分展示");
                return;
            }

            // 创建积分展示界面
            this.createScoreInterface();
            
        } catch (error) {
            console.error("获取积分数据失败:", error);
        }
    }

    /**
     * 创建积分展示界面
     */
    createScoreInterface() {
        // 创建遮罩层
        const overlay = document.createElement('div');
        overlay.id = 'score-overlay';
        overlay.className = 'score-overlay';
        
        // 创建积分面板
        const scorePanel = document.createElement('div');
        scorePanel.className = 'score-panel';
        
        // 标题
        const title = document.createElement('h2');
        title.textContent = `游戏结束 - ${this.scoreData.winner}`;
        title.className = 'score-title';
        scorePanel.appendChild(title);

        // 积分规则说明
        const rulesDiv = document.createElement('div');
        rulesDiv.className = 'score-rules';
        rulesDiv.innerHTML = `
            <h3>积分规则</h3>
            <ul>
                <li><strong>阵营分：</strong>胜利阵营 +10分，失败阵营 +0分</li>
                <li><strong>贡献分：</strong>
                    <ul>
                        <li>预言家查验出狼人 +5分</li>
                        <li>女巫救对人或毒死狼人 +5分</li>
                        <li>猎人开枪带走狼人 +5分</li>
                        <li>狼人击杀神民 +5分（团队加分）</li>
                        <li>村民投票放逐狼人 +3分/次</li>
                    </ul>
                </li>
                <li><strong>MVP加分：</strong>全场最佳 +5分（支持自动评选）</li>
            </ul>
        `;
        scorePanel.appendChild(rulesDiv);

        // 若有自动MVP结果，展示在顶部
        const auto = this.scoreData.auto_mvp;
        if (auto && auto.mvp_player_index) {
            const autoDiv = document.createElement('div');
            autoDiv.className = 'mvp-success';
            const p = this.scoreData.ranking.find(x => x.player_index === auto.mvp_player_index);
            const role = p ? p.role_type : '';
            const model = auto.model ? `（评审模型：${auto.model}）` : '';
            autoDiv.innerHTML = `
                <h3>🏆 自动评选 MVP</h3>
                <p>${auto.mvp_player_index}号玩家 (${role}) 获得MVP！${model}</p>
                <p>理由：${auto.reason || '综合表现最佳'}</p>
            `;
            scorePanel.appendChild(autoDiv);
            this.mvpVoted = true; // 有自动结果时不再显示投票区
        }

        // 排名表格
        const rankingTable = this.createRankingTable();
        scorePanel.appendChild(rankingTable);

        // MVP投票区域（仅在没有自动结果时显示）
        if (!this.mvpVoted) {
            const mvpSection = this.createMVPSection();
            scorePanel.appendChild(mvpSection);
        }

        // 关闭按钮
        const closeButton = document.createElement('button');
        closeButton.textContent = '关闭';
        closeButton.className = 'close-button';
        closeButton.onclick = () => this.hide();
        scorePanel.appendChild(closeButton);

        overlay.appendChild(scorePanel);
        document.body.appendChild(overlay);

        // 添加样式
        this.addStyles();
    }

    /**
     * 创建排名表格
     */
    createRankingTable() {
        const tableContainer = document.createElement('div');
        tableContainer.className = 'ranking-container';

        const table = document.createElement('table');
        table.className = 'ranking-table';

        // 表头
        const thead = document.createElement('thead');
        thead.innerHTML = `
            <tr>
                <th>排名</th>
                <th>玩家</th>
                <th>角色</th>
                <th>阵营分</th>
                <th>贡献分</th>
                <th>MVP分</th>
                <th>总分</th>
                <th>贡献详情</th>
            </tr>
        `;
        table.appendChild(thead);

        // 表体
        const tbody = document.createElement('tbody');
        this.scoreData.ranking.forEach((player, index) => {
            const row = document.createElement('tr');
            row.className = player.is_winner ? 'winner-row' : 'loser-row';
            
            const contributions = player.contributions.length > 0 
                ? player.contributions.join(', ') 
                : '无';

            row.innerHTML = `
                <td class="rank">${index + 1}</td>
                <td class="player">${player.player_index}号</td>
                <td class="role">${this.getRoleEmoji(player.role_type)} ${player.role_type}</td>
                <td class="camp-score">${player.camp_score}</td>
                <td class="contribution-score">${player.contribution_score}</td>
                <td class="mvp-score">${player.mvp_score > 0 ? '★' + player.mvp_score : player.mvp_score}</td>
                <td class="total-score"><strong>${player.total_score}</strong></td>
                <td class="contributions">${contributions}</td>
            `;
            tbody.appendChild(row);
        });
        table.appendChild(tbody);

        tableContainer.appendChild(table);
        return tableContainer;
    }

    /**
     * 创建MVP投票区域
     */
    createMVPSection() {
        const mvpSection = document.createElement('div');
        mvpSection.className = 'mvp-section';

        const mvpTitle = document.createElement('h3');
        mvpTitle.textContent = 'MVP投票';
        mvpSection.appendChild(mvpTitle);

        const mvpDescription = document.createElement('p');
        mvpDescription.textContent = '请选择本局游戏的最有价值玩家（MVP），获选者将额外获得5分：';
        mvpSection.appendChild(mvpDescription);

        const mvpButtons = document.createElement('div');
        mvpButtons.className = 'mvp-buttons';

        // 为每个玩家创建MVP投票按钮
        this.scoreData.ranking.forEach(player => {
            const button = document.createElement('button');
            button.textContent = `${player.player_index}号 ${player.role_type}`;
            button.className = 'mvp-button';
            button.onclick = () => this.voteMVP(player.player_index);
            mvpButtons.appendChild(button);
        });

        mvpSection.appendChild(mvpButtons);
        return mvpSection;
    }

    /**
     * 投票MVP
     */
    async voteMVP(playerIndex) {
        // 确认投票
        const playerData = this.scoreData.ranking.find(p => p.player_index === playerIndex);
        const confirmMessage = `确定要选择 ${playerIndex}号玩家 (${playerData.role_type}) 为MVP吗？\n\n获选者将额外获得5分，这将影响最终排名。`;

        if (!confirm(confirmMessage)) {
            return;
        }

        try {
            const response = await fetch('/set_mvp', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    mvp_player_index: playerIndex
                })
            });

            const result = await response.json();

            if (result.success) {
                this.mvpVoted = true;

                // 显示成功消息
                const successDiv = document.createElement('div');
                successDiv.className = 'mvp-success';
                successDiv.innerHTML = `
                    <h3>🏆 MVP已选出！</h3>
                    <p>${playerIndex}号玩家 (${playerData.role_type}) 被选为本局MVP，获得额外5分！</p>
                `;

                // 替换MVP投票区域
                const mvpSection = document.querySelector('.mvp-section');
                if (mvpSection) {
                    mvpSection.replaceWith(successDiv);
                }

                // 重新获取积分数据并刷新表格
                setTimeout(async () => {
                    try {
                        const response = await fetch('/get_game_scores');
                        this.scoreData = await response.json();

                        // 更新排名表格
                        const rankingContainer = document.querySelector('.ranking-container');
                        if (rankingContainer) {
                            const newTable = this.createRankingTable();
                            rankingContainer.replaceWith(newTable);
                        }
                    } catch (error) {
                        console.error("更新积分数据失败:", error);
                    }
                }, 1000);

            } else {
                alert(`设置MVP失败：${result.message}`);
            }
        } catch (error) {
            console.error("设置MVP失败:", error);
            alert("设置MVP失败，请重试");
        }
    }

    /**
     * 获取角色表情符号
     */
    getRoleEmoji(role) {
        const emojis = {
            '狼人': '🐺',
            '村民': '👨‍🌾',
            '预言家': '🔮',
            '女巫': '🧙‍♀️',
            '猎人': '🏹'
        };
        return emojis[role] || '❓';
    }

    /**
     * 隐藏积分界面
     */
    hide() {
        const overlay = document.getElementById('score-overlay');
        if (overlay) {
            overlay.remove();
        }
    }

    /**
     * 添加样式
     */
    addStyles() {
        if (document.getElementById('score-styles')) {
            return; // 样式已存在
        }

        const style = document.createElement('style');
        style.id = 'score-styles';
        style.textContent = `
            .score-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.8);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 10000;
            }

            .score-panel {
                background: white;
                border-radius: 10px;
                padding: 20px;
                max-width: 90%;
                max-height: 90%;
                overflow-y: auto;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            }

            .score-title {
                text-align: center;
                color: #333;
                margin-bottom: 20px;
                font-size: 24px;
            }

            .score-rules {
                background: #f5f5f5;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
                font-size: 14px;
            }

            .score-rules h3 {
                margin-top: 0;
                color: #666;
            }

            .score-rules ul {
                margin: 10px 0;
                padding-left: 20px;
            }

            .ranking-container {
                margin-bottom: 20px;
            }

            .ranking-table {
                width: 100%;
                border-collapse: collapse;
                font-size: 14px;
            }

            .ranking-table th,
            .ranking-table td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: center;
            }

            .ranking-table th {
                background-color: #f2f2f2;
                font-weight: bold;
            }

            .winner-row {
                background-color: #e8f5e8;
            }

            .loser-row {
                background-color: #ffeaea;
            }

            .rank {
                font-weight: bold;
                font-size: 16px;
            }

            .total-score {
                font-size: 16px;
                color: #d4af37;
            }

            .mvp-section {
                background: #f0f8ff;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
            }

            .mvp-section h3 {
                margin-top: 0;
                color: #4169e1;
            }

            .mvp-buttons {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin-top: 10px;
            }

            .mvp-button {
                padding: 8px 16px;
                background: #4169e1;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
            }

            .mvp-button:hover {
                background: #1e90ff;
            }

            .close-button {
                display: block;
                margin: 20px auto 0;
                padding: 10px 30px;
                background: #666;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }

            .close-button:hover {
                background: #555;
            }

            .mvp-success {
                background: #e8f5e8;
                border: 2px solid #4caf50;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                text-align: center;
            }

            .mvp-success h3 {
                color: #2e7d32;
                margin-top: 0;
                font-size: 20px;
            }

            .mvp-success p {
                color: #388e3c;
                font-size: 16px;
                margin-bottom: 0;
            }
        `;
        document.head.appendChild(style);
    }
}

export default ScoreDisplay;
