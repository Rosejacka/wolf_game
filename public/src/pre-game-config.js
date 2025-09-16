/**
 * 游戏前配置界面
 * 允许用户在游戏开始前设置位置和角色配置
 */

class PreGameConfig {
    constructor() {
        this.isVisible = false;
        this.currentPositions = {};
        this.availableRoles = ['狼人', '村民', '预言家', '女巫', '猎人'];
        this.availableModels = [
            'gpt-4.1', 'deepseek-chat', 'qwen-max-2025-01-25',
            'glm-4-plus', 'Baichuan4', 'moonshot-v1-32k', 'hunyuan-large'
        ];
        this.onGameStart = null; // 游戏开始回调函数
        this.createUI();
    }

    createUI() {
        // 创建主容器
        this.container = document.createElement('div');
        this.container.id = 'pre-game-config';
        this.container.className = 'pre-game-config';
        
        // 创建内容
        this.container.innerHTML = `
            <div class="config-overlay">
                <div class="config-panel">
                    <div class="config-header">
                        <h1>🎮 狼人杀游戏配置</h1>
                        <p>请设置玩家位置和角色，然后开始游戏</p>
                    </div>
                    
                    <div class="config-content">
                        <div class="config-section">
                            <h3>快速配置</h3>
                            <div class="quick-config-buttons">
                                <button id="load-default" class="config-btn btn-primary">使用默认配置</button>
                                <button id="randomize-all" class="config-btn btn-secondary">随机化所有位置</button>
                                <button id="load-current" class="config-btn btn-info">加载当前配置</button>
                            </div>
                        </div>
                        
                        <div class="config-section">
                            <h3>位置配置</h3>
                            <div class="positions-grid" id="pre-positions-grid">
                                <!-- 位置网格将在这里动态生成 -->
                            </div>
                        </div>
                        
                        <div class="config-section">
                            <h3>游戏设置</h3>
                            <div class="game-settings">
                                <label class="setting-item">
                                    <input type="checkbox" id="display-roles" checked>
                                    <span>显示角色信息</span>
                                </label>
                                <label class="setting-item">
                                    <input type="checkbox" id="display-thinking" checked>
                                    <span>显示思考过程</span>
                                </label>
                                <label class="setting-item">
                                    <input type="checkbox" id="auto-play">
                                    <span>自动播放</span>
                                </label>
                            </div>
                        </div>
                    </div>
                    
                    <div class="config-footer">
                        <div class="role-summary" id="role-summary">
                            <!-- 角色统计将在这里显示 -->
                        </div>
                        <div class="config-actions">
                            <button id="save-config" class="config-btn btn-success">保存配置</button>
                            <button id="start-game" class="config-btn btn-primary">开始游戏</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(this.container);
        this.bindEvents();
    }

    bindEvents() {
        // 快速配置按钮
        document.getElementById('load-default').addEventListener('click', () => {
            this.loadDefaultConfig();
        });
        
        document.getElementById('randomize-all').addEventListener('click', () => {
            this.randomizeAllPositions();
        });
        
        document.getElementById('load-current').addEventListener('click', () => {
            this.loadCurrentConfig();
        });
        
        // 保存配置
        document.getElementById('save-config').addEventListener('click', () => {
            this.saveConfig();
        });
        
        // 开始游戏
        document.getElementById('start-game').addEventListener('click', () => {
            this.startGame();
        });
        
        // ESC键关闭（但在游戏开始前不允许关闭）
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isVisible) {
                // 可以添加确认对话框
                const shouldClose = confirm('确定要退出配置吗？这将使用默认配置开始游戏。');
                if (shouldClose) {
                    this.startGame();
                }
            }
        });
    }

    async show() {
        this.isVisible = true;
        this.container.style.display = 'block';
        await this.loadCurrentConfig();
    }

    hide() {
        this.isVisible = false;
        this.container.style.display = 'none';
    }

    async loadCurrentConfig() {
        try {
            const response = await fetch('/get_position_info');
            const data = await response.json();
            
            if (data.success) {
                this.currentPositions = data.positions;
                this.renderPositionsGrid();
                this.updateRoleSummary();
            } else {
                console.error('获取当前配置失败:', data.message);
                this.loadDefaultConfig();
            }
        } catch (error) {
            console.error('加载当前配置时出错:', error);
            this.loadDefaultConfig();
        }
    }

    loadDefaultConfig() {
        // 默认配置：3狼人、1预言家、1女巫、1猎人、3村民
        const defaultConfig = {
            1: { role: '狼人', model_name: 'gpt-4.1' },
            2: { role: '狼人', model_name: 'gpt-4.1' },
            3: { role: '狼人', model_name: 'gpt-4.1' },
            4: { role: '预言家', model_name: 'gpt-4.1' },
            5: { role: '女巫', model_name: 'gpt-4.1' },
            6: { role: '猎人', model_name: 'gpt-4.1' },
            7: { role: '村民', model_name: 'gpt-4.1' },
            8: { role: '村民', model_name: 'gpt-4.1' },
            9: { role: '村民', model_name: 'gpt-4.1' }
        };
        
        this.currentPositions = {};
        for (let i = 1; i <= 9; i++) {
            this.currentPositions[i] = {
                position: i,
                role: defaultConfig[i].role,
                model_name: defaultConfig[i].model_name,
                is_alive: true
            };
        }
        
        this.renderPositionsGrid();
        this.updateRoleSummary();
    }

    randomizeAllPositions() {
        // 获取当前所有角色
        const roles = Object.values(this.currentPositions).map(p => p.role);
        
        // 随机打乱角色
        for (let i = roles.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [roles[i], roles[j]] = [roles[j], roles[i]];
        }
        
        // 更新位置配置
        for (let i = 1; i <= 9; i++) {
            this.currentPositions[i].role = roles[i-1];
        }
        
        this.renderPositionsGrid();
        this.updateRoleSummary();
    }

    renderPositionsGrid() {
        const grid = document.getElementById('pre-positions-grid');
        grid.innerHTML = '';
        
        for (let i = 1; i <= 9; i++) {
            const positionData = this.currentPositions[i];
            if (!positionData) continue;
            
            const positionCard = document.createElement('div');
            positionCard.className = 'pre-position-card';
            positionCard.innerHTML = `
                <div class="position-header">
                    <span class="position-number">位置${i}</span>
                </div>
                <div class="position-controls">
                    <label>角色:</label>
                    <select class="role-select" data-position="${i}">
                        ${this.availableRoles.map(role => 
                            `<option value="${role}" ${role === positionData.role ? 'selected' : ''}>${role}</option>`
                        ).join('')}
                    </select>
                    
                    <label>模型:</label>
                    <select class="model-select" data-position="${i}">
                        ${this.availableModels.map(model => 
                            `<option value="${model}" ${model === positionData.model_name ? 'selected' : ''}>${model}</option>`
                        ).join('')}
                    </select>
                </div>
            `;
            
            grid.appendChild(positionCard);
        }
        
        // 绑定变更事件
        grid.addEventListener('change', () => {
            this.updateCurrentPositions();
            this.updateRoleSummary();
        });
    }

    updateCurrentPositions() {
        for (let i = 1; i <= 9; i++) {
            const roleSelect = document.querySelector(`.role-select[data-position="${i}"]`);
            const modelSelect = document.querySelector(`.model-select[data-position="${i}"]`);
            
            if (roleSelect && modelSelect && this.currentPositions[i]) {
                this.currentPositions[i].role = roleSelect.value;
                this.currentPositions[i].model_name = modelSelect.value;
            }
        }
    }

    updateRoleSummary() {
        const summary = document.getElementById('role-summary');
        const roleCounts = {};
        
        // 统计角色数量
        Object.values(this.currentPositions).forEach(player => {
            roleCounts[player.role] = (roleCounts[player.role] || 0) + 1;
        });
        
        // 生成统计显示
        const summaryItems = Object.entries(roleCounts).map(([role, count]) => {
            const emoji = this.getRoleEmoji(role);
            return `<span class="role-count">${emoji} ${role}: ${count}</span>`;
        });
        
        summary.innerHTML = `
            <h4>角色统计</h4>
            <div class="role-counts">${summaryItems.join('')}</div>
        `;
    }

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

    async saveConfig() {
        try {
            this.updateCurrentPositions();
            
            const positionMapping = {};
            for (let i = 1; i <= 9; i++) {
                const positionData = this.currentPositions[i];
                positionMapping[i] = {
                    role: positionData.role,
                    model_name: positionData.model_name
                };
            }
            
            const response = await fetch('/manual_position', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    position_mapping: positionMapping
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert('配置保存成功！');
            } else {
                alert('保存配置失败: ' + data.message);
            }
        } catch (error) {
            console.error('保存配置时出错:', error);
            alert('保存配置时出错: ' + error.message);
        }
    }

    async startGame() {
        try {
            // 先保存配置
            await this.saveConfig();
            
            // 隐藏配置界面
            this.hide();
            
            // 调用游戏开始回调
            if (this.onGameStart && typeof this.onGameStart === 'function') {
                this.onGameStart();
            }
        } catch (error) {
            console.error('开始游戏时出错:', error);
            alert('开始游戏时出错: ' + error.message);
        }
    }

    setGameStartCallback(callback) {
        this.onGameStart = callback;
    }
}

export default PreGameConfig;
