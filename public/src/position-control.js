/**
 * 位置控制组件
 * 用于手动调整玩家位置和角色分配
 */

class PositionControl {
    constructor() {
        this.isVisible = false;
        this.currentPositions = {};
        this.availableRoles = ['狼人', '村民', '预言家', '女巫', '猎人'];
        this.availableModels = [
            'gpt-4.1', 'deepseek-chat', 'qwen-max-2025-01-25',
            'glm-4-plus', 'Baichuan4', 'moonshot-v1-32k', 'hunyuan-large'
        ];
        this.createUI();
    }

    createUI() {
        // 创建主容器
        this.container = document.createElement('div');
        this.container.id = 'position-control-panel';
        this.container.className = 'position-control-panel hidden';
        
        // 创建标题栏
        const header = document.createElement('div');
        header.className = 'panel-header';
        header.innerHTML = `
            <h3>位置控制面板</h3>
            <button id="close-position-panel" class="close-btn">×</button>
        `;
        
        // 创建内容区域
        const content = document.createElement('div');
        content.className = 'panel-content';
        content.innerHTML = `
            <div class="control-buttons">
                <button id="refresh-positions" class="btn btn-primary">刷新位置信息</button>
                <button id="randomize-positions" class="btn btn-secondary">随机化位置</button>
                <button id="apply-positions" class="btn btn-success">应用更改</button>
                <button id="restart-game" class="btn btn-warning">重新开始游戏</button>
            </div>
            <div class="positions-grid" id="positions-grid">
                <!-- 位置网格将在这里动态生成 -->
            </div>
            <div class="swap-controls">
                <h4>快速交换位置</h4>
                <div class="swap-inputs">
                    <select id="swap-pos1" class="position-select">
                        <option value="">选择位置1</option>
                    </select>
                    <span>⇄</span>
                    <select id="swap-pos2" class="position-select">
                        <option value="">选择位置2</option>
                    </select>
                    <button id="swap-positions" class="btn btn-warning">交换</button>
                </div>
            </div>
        `;
        
        this.container.appendChild(header);
        this.container.appendChild(content);
        document.body.appendChild(this.container);
        
        this.bindEvents();
        this.populateSwapSelects();
    }

    bindEvents() {
        // 关闭面板
        document.getElementById('close-position-panel').addEventListener('click', () => {
            this.hide();
        });
        
        // 刷新位置信息
        document.getElementById('refresh-positions').addEventListener('click', () => {
            this.refreshPositions();
        });
        
        // 随机化位置
        document.getElementById('randomize-positions').addEventListener('click', () => {
            this.randomizePositions();
        });
        
        // 应用更改
        document.getElementById('apply-positions').addEventListener('click', () => {
            this.applyChanges();
        });

        // 重新开始游戏
        document.getElementById('restart-game').addEventListener('click', () => {
            this.restartGame();
        });

        // 交换位置
        document.getElementById('swap-positions').addEventListener('click', () => {
            this.swapPositions();
        });
        
        // ESC键关闭面板
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isVisible) {
                this.hide();
            }
        });
    }

    populateSwapSelects() {
        const select1 = document.getElementById('swap-pos1');
        const select2 = document.getElementById('swap-pos2');
        
        for (let i = 1; i <= 9; i++) {
            const option1 = document.createElement('option');
            option1.value = i;
            option1.textContent = `位置${i}`;
            select1.appendChild(option1);
            
            const option2 = document.createElement('option');
            option2.value = i;
            option2.textContent = `位置${i}`;
            select2.appendChild(option2);
        }
    }

    async show() {
        this.isVisible = true;
        this.container.classList.remove('hidden');
        await this.refreshPositions();
    }

    hide() {
        this.isVisible = false;
        this.container.classList.add('hidden');
    }

    async refreshPositions() {
        try {
            const response = await fetch('/get_position_info');
            const data = await response.json();
            
            if (data.success) {
                this.currentPositions = data.positions;
                this.renderPositionsGrid();
            } else {
                console.error('获取位置信息失败:', data.message);
                alert('获取位置信息失败: ' + data.message);
            }
        } catch (error) {
            console.error('刷新位置信息时出错:', error);
            alert('刷新位置信息时出错: ' + error.message);
        }
    }

    renderPositionsGrid() {
        const grid = document.getElementById('positions-grid');
        grid.innerHTML = '';
        
        for (let i = 1; i <= 9; i++) {
            const positionData = this.currentPositions[i];
            if (!positionData) continue;
            
            const positionCard = document.createElement('div');
            positionCard.className = 'position-card';
            positionCard.innerHTML = `
                <div class="position-header">
                    <span class="position-number">位置${i}</span>
                    <span class="alive-status ${positionData.is_alive ? 'alive' : 'dead'}">
                        ${positionData.is_alive ? '存活' : '死亡'}
                    </span>
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
    }

    randomizePositions() {
        // 获取当前所有角色
        const roles = Object.values(this.currentPositions).map(p => p.role);
        
        // 随机打乱角色
        for (let i = roles.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [roles[i], roles[j]] = [roles[j], roles[i]];
        }
        
        // 更新UI中的角色选择
        const roleSelects = document.querySelectorAll('.role-select');
        roleSelects.forEach((select, index) => {
            select.value = roles[index];
        });
        
        alert('位置已随机化，请点击"应用更改"来保存');
    }

    async applyChanges() {
        try {
            const positionMapping = {};
            
            // 收集所有位置的更改
            for (let i = 1; i <= 9; i++) {
                const roleSelect = document.querySelector(`.role-select[data-position="${i}"]`);
                const modelSelect = document.querySelector(`.model-select[data-position="${i}"]`);
                
                if (roleSelect && modelSelect) {
                    positionMapping[i] = {
                        role: roleSelect.value,
                        model_name: modelSelect.value
                    };
                }
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
                const shouldRestart = confirm('位置更改已应用成功！\n\n✅ 配置文件已更新\n✅ 随机化已禁用\n\n现在重新开始游戏将使用您设置的位置配置。\n\n点击"确定"重新开始游戏，点击"取消"继续当前游戏。');

                if (shouldRestart) {
                    this.restartGame();
                } else {
                    await this.refreshPositions();
                    // 通知游戏界面刷新玩家状态
                    this.notifyGameRefresh();
                    alert('配置已保存！下次重新开始游戏时将使用新的位置设置。');
                }
            } else {
                alert('应用更改失败: ' + data.message);
            }
        } catch (error) {
            console.error('应用更改时出错:', error);
            alert('应用更改时出错: ' + error.message);
        }
    }

    async swapPositions() {
        const pos1 = document.getElementById('swap-pos1').value;
        const pos2 = document.getElementById('swap-pos2').value;
        
        if (!pos1 || !pos2) {
            alert('请选择要交换的两个位置');
            return;
        }
        
        if (pos1 === pos2) {
            alert('不能选择相同的位置');
            return;
        }
        
        try {
            const response = await fetch('/swap_position', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    position1: parseInt(pos1),
                    position2: parseInt(pos2)
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                const shouldRestart = confirm(`成功交换位置${pos1}和位置${pos2}！\n\n✅ 配置文件已更新\n✅ 随机化已禁用\n\n现在重新开始游戏将使用交换后的位置配置。\n\n点击"确定"重新开始游戏，点击"取消"继续当前游戏。`);

                if (shouldRestart) {
                    this.restartGame();
                } else {
                    await this.refreshPositions();
                    this.notifyGameRefresh();
                    alert('位置交换已保存！下次重新开始游戏时将使用新的位置设置。');
                }

                // 重置选择
                document.getElementById('swap-pos1').value = '';
                document.getElementById('swap-pos2').value = '';
            } else {
                alert('交换位置失败: ' + data.message);
            }
        } catch (error) {
            console.error('交换位置时出错:', error);
            alert('交换位置时出错: ' + error.message);
        }
    }

    notifyGameRefresh() {
        // 发送自定义事件通知游戏界面刷新
        const event = new CustomEvent('positionChanged', {
            detail: {
                message: '位置已更改，请刷新游戏状态'
            }
        });
        window.dispatchEvent(event);

        // 如果游戏对象存在，直接调用刷新方法
        if (window.game && typeof window.game.refreshPlayerStatus === 'function') {
            window.game.refreshPlayerStatus();
        }

        console.log('已通知游戏界面刷新位置信息');
    }

    restartGame() {
        /**
         * 重新开始游戏 - 刷新整个页面以确保新配置生效
         */
        const shouldRestart = confirm('确定要重新开始游戏吗？\n\n🎮 将使用您设置的位置配置\n⚠️ 当前游戏进度将丢失\n\n点击"确定"继续重新开始。');

        if (shouldRestart) {
            console.log('重新开始游戏，使用新的位置配置...');
            // 刷新整个页面
            window.location.reload();
        }
    }
}

export default PositionControl;
