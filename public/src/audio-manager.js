/**
 * 音频播放管理器
 * 负责TTS音频的加载、播放、暂停、速度控制等功能
 */

class AudioManager {
    constructor() {
        this.currentAudio = null;
        this.isPlaying = false;
        this.isPaused = false;
        this.playbackRate = 1.0;
        this.volume = 1.0;
        this.onEndedCallback = null;
        this.onProgressCallback = null;
        
        // 音频缓存
        this.audioCache = new Map();
        
        // 绑定事件处理器
        this.handleAudioEnded = this.handleAudioEnded.bind(this);
        this.handleTimeUpdate = this.handleTimeUpdate.bind(this);
        this.handleLoadedData = this.handleLoadedData.bind(this);
        this.handleError = this.handleError.bind(this);
        
        console.log('音频管理器初始化完成');
    }
    
    /**
     * 加载音频文件
     * @param {string} audioPath - 音频文件路径
     * @param {boolean} useCache - 是否使用缓存
     * @returns {Promise<HTMLAudioElement>} 音频元素
     */
    async loadAudio(audioPath, useCache = true) {
        if (!audioPath) {
            throw new Error('音频路径不能为空');
        }
        
        // 检查缓存
        if (useCache && this.audioCache.has(audioPath)) {
            console.log(`使用缓存的音频: ${audioPath}`);
            return this.audioCache.get(audioPath);
        }
        
        return new Promise((resolve, reject) => {
            const audio = new Audio();
            
            // 设置事件监听器
            audio.addEventListener('loadeddata', () => {
                console.log(`音频加载完成: ${audioPath}`);
                if (useCache) {
                    this.audioCache.set(audioPath, audio);
                }
                resolve(audio);
            });
            
            audio.addEventListener('error', (e) => {
                console.error(`音频加载失败: ${audioPath}`, e);
                reject(new Error(`音频加载失败: ${audioPath}`));
            });
            
            // 开始加载
            audio.src = audioPath;
            audio.preload = 'auto';
        });
    }
    
    /**
     * 播放音频
     * @param {string} audioPath - 音频文件路径
     * @param {Object} options - 播放选项
     * @returns {Promise<void>}
     */
    async playAudio(audioPath, options = {}) {
        try {
            // 停止当前播放的音频
            this.stopAudio();

            // 加载音频
            this.currentAudio = await this.loadAudio(audioPath, options.useCache !== false);

            // 设置播放参数
            const playbackRate = options.playbackRate || this.playbackRate;
            this.currentAudio.playbackRate = playbackRate;
            this.currentAudio.volume = options.volume || this.volume;

            // 更新内部播放速度
            this.playbackRate = playbackRate;

            // 绑定事件
            this.currentAudio.addEventListener('ended', this.handleAudioEnded);
            this.currentAudio.addEventListener('timeupdate', this.handleTimeUpdate);
            this.currentAudio.addEventListener('error', this.handleError);

            // 设置回调
            if (options.onEnded) {
                this.onEndedCallback = options.onEnded;
            }
            if (options.onProgress) {
                this.onProgressCallback = options.onProgress;
            }

            // 开始播放
            await this.currentAudio.play();
            this.isPlaying = true;
            this.isPaused = false;

            console.log(`开始播放音频: ${audioPath}, 播放速度: ${this.currentAudio.playbackRate}x`);

        } catch (error) {
            console.error('播放音频失败:', error);
            throw error;
        }
    }
    
    /**
     * 暂停音频播放
     */
    pauseAudio() {
        if (this.currentAudio && this.isPlaying && !this.isPaused) {
            this.currentAudio.pause();
            this.isPaused = true;
            console.log('音频播放已暂停');
        }
    }
    
    /**
     * 恢复音频播放
     */
    resumeAudio() {
        if (this.currentAudio && this.isPaused) {
            this.currentAudio.play();
            this.isPaused = false;
            console.log('音频播放已恢复');
        }
    }
    
    /**
     * 停止音频播放
     */
    stopAudio() {
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio.currentTime = 0;
            
            // 移除事件监听器
            this.currentAudio.removeEventListener('ended', this.handleAudioEnded);
            this.currentAudio.removeEventListener('timeupdate', this.handleTimeUpdate);
            this.currentAudio.removeEventListener('error', this.handleError);
            
            this.currentAudio = null;
            this.isPlaying = false;
            this.isPaused = false;
            this.onEndedCallback = null;
            this.onProgressCallback = null;
            
            console.log('音频播放已停止');
        }
    }
    
    /**
     * 设置播放速度
     * @param {number} rate - 播放速度倍率 (0.1 - 4.0)
     */
    setPlaybackRate(rate) {
        this.playbackRate = Math.max(0.1, Math.min(4.0, rate));
        if (this.currentAudio) {
            this.currentAudio.playbackRate = this.playbackRate;
            console.log(`音频播放速度设置为: ${this.playbackRate}x`);
        }
    }
    
    /**
     * 设置音量
     * @param {number} volume - 音量 (0.0 - 1.0)
     */
    setVolume(volume) {
        this.volume = Math.max(0.0, Math.min(1.0, volume));
        if (this.currentAudio) {
            this.currentAudio.volume = this.volume;
            console.log(`音频音量设置为: ${this.volume}`);
        }
    }
    
    /**
     * 获取当前播放进度
     * @returns {Object} 播放进度信息
     */
    getProgress() {
        if (!this.currentAudio) {
            return { currentTime: 0, duration: 0, progress: 0 };
        }
        
        const currentTime = this.currentAudio.currentTime;
        const duration = this.currentAudio.duration || 0;
        const progress = duration > 0 ? currentTime / duration : 0;
        
        return { currentTime, duration, progress };
    }
    
    /**
     * 检查是否正在播放
     * @returns {boolean}
     */
    isAudioPlaying() {
        return this.isPlaying && !this.isPaused;
    }
    
    /**
     * 清理音频缓存
     */
    clearCache() {
        this.audioCache.clear();
        console.log('音频缓存已清理');
    }
    
    /**
     * 音频播放结束事件处理器
     */
    handleAudioEnded() {
        console.log('音频播放结束');
        this.isPlaying = false;
        this.isPaused = false;
        
        if (this.onEndedCallback) {
            this.onEndedCallback();
        }
    }
    
    /**
     * 音频播放进度更新事件处理器
     */
    handleTimeUpdate() {
        if (this.onProgressCallback) {
            const progress = this.getProgress();
            this.onProgressCallback(progress);
        }
    }
    
    /**
     * 音频加载完成事件处理器
     */
    handleLoadedData() {
        console.log('音频数据加载完成');
    }
    
    /**
     * 音频错误事件处理器
     */
    handleError(error) {
        console.error('音频播放错误:', error);
        this.isPlaying = false;
        this.isPaused = false;
    }
    
    /**
     * 销毁音频管理器
     */
    destroy() {
        this.stopAudio();
        this.clearCache();
        console.log('音频管理器已销毁');
    }
}

export default AudioManager;
