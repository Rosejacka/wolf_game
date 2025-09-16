class HistoryPanel {
    constructor() {
        this.isVisible = false;
        this.playerHistory = {}; // 存储每个玩家的历史记录
        this.panel = null;
        this.toggleBtn = null;
        this.init();
    }

    init() {
        this.createPanel();
        this.createToggleButton();
        this.bindEvents();
    }

    createPanel() {
        this.panel = document.createElement('div');
        this.panel.className = 'history-panel';
        this.panel.innerHTML = `
            <div class="history-header">
                <div class="history-title">玩家思考与发言记录</div>
                <button class="history-close-btn">&times;</button>
            </div>
            <div class="history-content">
                <div class="history-empty">暂无记录</div>
            </div>
        `;
        // document.body.appendChild(this.panel);
        const historyArea = document.getElementById('history-area');
        if (historyArea) {
            historyArea.appendChild(this.panel);
        } else {
            document.body.appendChild(this.panel);
        }
    }

    createToggleButton() {
        this.toggleBtn = document.createElement('button');
        this.toggleBtn.className = 'history-toggle-btn';
        this.toggleBtn.textContent = '发言记录';
        this.toggleBtn.style.display = 'block';
        // document.body.appendChild(this.toggleBtn);
        const historyArea = document.getElementById('history-area');
        if (historyArea) {
            historyArea.appendChild(this.toggleBtn);
        } else {
            document.body.appendChild(this.toggleBtn);
        }
        console.log('历史记录按钮已创建');
    }

    bindEvents() {
        // 切换按钮事件
        this.toggleBtn.addEventListener('click', () => {
            this.toggle();
        });

        // 关闭按钮事件
        const closeBtn = this.panel.querySelector('.history-close-btn');
        closeBtn.addEventListener('click', () => {
            this.hide();
        });

        // 键盘快捷键支持
        document.addEventListener('keydown', (e) => {
            if (e.key === 'h' || e.key === 'H') {
                this.toggle();
            }
        });
    }

    // 添加玩家思考记录
    addThinking(playerIndex, thinking, role = '玩家') {
        console.log('历史记录面板收到思考记录:', playerIndex, thinking, role);
        if (!this.playerHistory[playerIndex]) {
            this.playerHistory[playerIndex] = [];
        }
        
        this.playerHistory[playerIndex].push({
            type: 'thinking',
            content: thinking,
            role: role,
            timestamp: new Date().toLocaleTimeString()
        });
        
        console.log('当前历史记录:', this.playerHistory);
        this.renderHistory();
    }

    // 添加玩家发言记录
    addSpeak(playerIndex, speak, role = '玩家') {
        console.log('历史记录面板收到发言记录:', playerIndex, speak, role);
        if (!this.playerHistory[playerIndex]) {
            this.playerHistory[playerIndex] = [];
        }
        
        this.playerHistory[playerIndex].push({
            type: 'speak',
            content: speak,
            role: role,
            timestamp: new Date().toLocaleTimeString()
        });
        
        console.log('当前历史记录:', this.playerHistory);
        this.renderHistory();
    }

    // 添加玩家投票记录
    addVote(playerIndex, voteTarget, role = '玩家') {
        if (!this.playerHistory[playerIndex]) {
            this.playerHistory[playerIndex] = [];
        }
        
        const voteText = voteTarget === -1 ? '弃票' : `投票给${voteTarget}号玩家`;
        this.playerHistory[playerIndex].push({
            type: 'vote',
            content: voteText,
            role: role,
            timestamp: new Date().toLocaleTimeString()
        });
        
        this.renderHistory();
    }

    // 添加玩家行动记录（如预言家查验、女巫用药等）
    addAction(playerIndex, action, role = '玩家') {
        if (!this.playerHistory[playerIndex]) {
            this.playerHistory[playerIndex] = [];
        }
        
        this.playerHistory[playerIndex].push({
            type: 'action',
            content: action,
            role: role,
            timestamp: new Date().toLocaleTimeString()
        });
        
        this.renderHistory();
    }

    renderHistory() {
        const content = this.panel.querySelector('.history-content');

        if (Object.keys(this.playerHistory).length === 0) {
            content.innerHTML = '<div class="history-empty">暂无记录</div>';
            return;
        }

        // 收集所有玩家的最新记录
        const allLatestRecords = [];

        Object.keys(this.playerHistory).forEach(playerIndex => {
            const playerRecords = this.playerHistory[playerIndex];

            // 按类型分组，每种类型只保留最新的一条记录
            const recordsByType = {};
            playerRecords.forEach(record => {
                recordsByType[record.type] = record;
            });

            // 将每种类型的最新记录添加到总列表中，并标记玩家信息
            Object.values(recordsByType).forEach(record => {
                allLatestRecords.push({
                    ...record,
                    playerIndex: playerIndex,
                    playerRole: playerRecords[0]?.role || '玩家'
                });
            });
        });

        // 按时间戳排序所有记录
        allLatestRecords.sort((a, b) => {
            const timeA = new Date('1970/01/01 ' + a.timestamp);
            const timeB = new Date('1970/01/01 ' + b.timestamp);
            return timeA - timeB;
        });

        // 渲染所有记录
        let html = '';
        allLatestRecords.forEach(record => {
            const eventClass = this.getEventClass(record.type);
            const icon = this.getEventIcon(record.type);
            html += `
                <div class="history-event ${eventClass}">
                    <div class="event-header">
                        <span class="player-info">${record.playerIndex}号 ${record.playerRole}</span>
                        <span class="event-icon">${icon}</span>
                        <span class="event-type">${this.getEventTypeText(record.type)}</span>
                        <span class="event-time">${record.timestamp}</span>
                    </div>
                    <div class="event-content">${record.content}</div>
                </div>
            `;
        });

        content.innerHTML = html;

        // 自动滚动到底部显示最新记录
        this.scrollToBottom();
    }

    // 滚动到底部的方法
    scrollToBottom() {
        if (this.panel && this.isVisible) {
            // 使用 setTimeout 确保 DOM 更新完成后再滚动
            setTimeout(() => {
                this.panel.scrollTop = this.panel.scrollHeight;
            }, 50); // 增加延迟时间确保渲染完成
        }
    }

    renderPlayerHistory(playerIndex, records) {
        let html = `
            <div class="history-player">
                <div class="history-player-header">
                    <span class="player-number">${playerIndex}号玩家</span>
                    <span class="player-role">${records[0]?.role || '玩家'}</span>
                </div>
                <div class="history-player-content">
        `;

        // 按类型分组，每种类型只显示最新的一条记录，同时记录时间戳
        const recordsByType = {};
        records.forEach(record => {
            recordsByType[record.type] = record; // 后面的记录会覆盖前面的，保留最新的
        });

        // 获取所有存在的记录类型，按时间戳排序（最新的在底部）
        const existingRecords = Object.values(recordsByType);
        existingRecords.sort((a, b) => {
            // 将时间戳转换为可比较的格式进行排序
            const timeA = new Date('1970/01/01 ' + a.timestamp);
            const timeB = new Date('1970/01/01 ' + b.timestamp);
            return timeA - timeB;
        });

        existingRecords.forEach(record => {
            const eventClass = this.getEventClass(record.type);
            const icon = this.getEventIcon(record.type);
            html += `
                <div class="history-event ${eventClass}">
                    <div class="event-header">
                        <span class="event-icon">${icon}</span>
                        <span class="event-type">${this.getEventTypeText(record.type)}</span>
                        <span class="event-time">${record.timestamp}</span>
                    </div>
                    <div class="event-content">${record.content}</div>
                </div>
            `;
        });

        html += `
                </div>
            </div>
        `;

        return html;
    }

    getEventClass(type) {
        switch (type) {
            case 'thinking': return 'thinking';
            case 'speak': return 'speak';
            case 'vote': return 'vote';
            case 'action': return 'action';
            default: return '';
        }
    }

    getEventIcon(type) {
        switch (type) {
            case 'thinking': return '💭';
            case 'speak': return '💬';
            case 'vote': return '🗳️';
            case 'action': return '⚡';
            default: return '📝';
        }
    }

    getEventTypeText(type) {
        switch (type) {
            case 'thinking': return '思考过程';
            case 'speak': return '发言内容';
            case 'vote': return '投票选择';
            case 'action': return '行动记录';
            default: return '其他';
        }
    }

    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }

    show() {
        this.isVisible = true;
        this.panel.classList.add('show');
        this.toggleBtn.style.display = 'none';
        this.renderHistory();
        // 显示面板时也滚动到底部，等待动画完成
        setTimeout(() => {
            this.scrollToBottom();
        }, 350); // 等待面板显示动画完成（CSS transition 是 0.3s）
    }

    hide() {
        this.isVisible = false;
        this.panel.classList.remove('show');
        this.toggleBtn.style.display = 'block';
    }

    // 清空所有记录
    clear() {
        this.playerHistory = {};
        this.renderHistory();
    }

    // 销毁面板
    destroy() {
        if (this.panel) {
            document.body.removeChild(this.panel);
        }
        if (this.toggleBtn) {
            document.body.removeChild(this.toggleBtn);
        }
    }
}

export default HistoryPanel; 