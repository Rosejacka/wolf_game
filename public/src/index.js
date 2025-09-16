console.log('=== index.js 开始加载 ===');

import Game from "./game.js";
import Ui from "./ui.js";
import PositionControl from "./position-control.js";
import PreGameConfig from "./pre-game-config.js";
import HistoryPanel from "./history-panel.js";
import AudioManager from "./audio-manager.js";
import { sleep } from "./utils.js";

// Asynchronous IIFE
(async () => {
    const ui = new Ui();
    await ui.setup();
    await ui.preload();
    await ui.loadSprites();

    // 创建游戏前配置界面
    const preGameConfig = new PreGameConfig();

    // 创建位置控制组件
    let positionControl = null;
    try {
        positionControl = new PositionControl();
        console.log('位置控制组件创建成功');
    } catch (error) {
        console.error('创建位置控制组件失败:', error);
    }

    // 创建历史记录面板
    let historyPanel = null;
    try {
        console.log('开始创建历史记录面板...');
        historyPanel = new HistoryPanel();
        window.historyPanel = historyPanel;
        console.log('历史记录面板创建成功:', historyPanel);
        console.log('window.historyPanel:', window.historyPanel);
    } catch (error) {
        console.error('创建历史记录面板失败:', error);
        console.error('错误详情:', error.stack);
    }

    // 创建音频管理器
    let audioManager = null;
    try {
        console.log('开始创建音频管理器...');
        audioManager = new AudioManager();
        window.audioManager = audioManager;
        console.log('音频管理器创建成功:', audioManager);
    } catch (error) {
        console.error('创建音频管理器失败:', error);
        console.error('错误详情:', error.stack);
    }

    // 定义游戏开始函数
    const startGameFlow = async () => {
        // 添加位置控制按钮
        const positionControlBtn = document.createElement('button');
        positionControlBtn.className = 'position-control-btn';
        positionControlBtn.textContent = '位置控制';
        positionControlBtn.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            background: linear-gradient(135deg, #e74c3c, #c0392b);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
            z-index: 9999;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(231, 76, 60, 0.3);
            pointer-events: auto;
        `;
        positionControlBtn.addEventListener('click', () => {
            console.log('位置控制按钮被点击');
            if (positionControl) {
                positionControl.show();
            } else {
                alert('位置控制组件未正确初始化');
            }
        });
        document.body.appendChild(positionControlBtn);
        console.log('位置控制按钮已添加到页面');

        // 添加键盘快捷键支持
        document.addEventListener('keydown', (e) => {
            if (e.key === 'p' || e.key === 'P') {
                console.log('按下P键，显示位置控制面板');
                if (positionControl) {
                    positionControl.show();
                }
            }
        });

        // 监听位置更改事件
        window.addEventListener('positionChanged', (event) => {
            console.log('收到位置更改通知:', event.detail);
            // 这里可以添加刷新游戏界面的逻辑
            if (window.game && typeof window.game.refreshPlayerStatus === 'function') {
                window.game.refreshPlayerStatus();
            }
        });

        await ui.showBigText("游戏开始", 1000);
        await ui.showBigText("配置已设置完成", 1500);
        await ui.showBigText("天黑了，请闭眼", 2000);

        //如果不想显示角色名称，可以传 false
        const game = new Game(ui);

        // 将游戏对象设为全局可访问，以便位置控制功能使用
        window.game = game;
        
        // 确保历史记录面板可用
        if (!window.historyPanel) {
            try {
                historyPanel = new HistoryPanel();
                window.historyPanel = historyPanel;
                console.log('历史记录面板重新创建成功');
            } catch (error) {
                console.error('创建历史记录面板失败:', error);
            }
        }

        await game.start();

        let is_end = false;
        while (!is_end) {
            is_end = await game.run();
        }
    };

    // 设置游戏开始回调
    preGameConfig.setGameStartCallback(startGameFlow);

    // 显示游戏前配置界面
    await preGameConfig.show();
})();

// 历史记录功能已由 HistoryPanel 类统一管理
