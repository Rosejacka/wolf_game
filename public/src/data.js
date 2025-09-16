class GameData {
    constructor() {
        // 简单的基于请求签名的预取缓存
        this._prefetchCache = new Map();
    }

    _getCacheKey(url, options = {}) {
        const method = (options.method || 'GET').toUpperCase();
        const body = options.body || '';
        return `${method} ${url} ${body}`;
    }

    async fetchData(url, options = {}) {
        const timeout = 1000 * 1800; // 30秒超时（原注释）
        const timeoutPromise = new Promise((_, reject) => {
            setTimeout(() => reject(new Error('请求超时')), timeout);
        });

        const fetchPromise = fetch(url, options);
        const response = await Promise.race([fetchPromise, timeoutPromise]);
        return response.json();
    }

    async _fetchWithCache(url, options = {}) {
        const key = this._getCacheKey(url, options);
        if (this._prefetchCache.has(key)) {
            const p = this._prefetchCache.get(key);
            this._prefetchCache.delete(key);
            return await p;
        }
        return this.fetchData(url, options);
    }

    // 供外部触发的预取方法（只对无副作用接口使用）
    prefetch(url, options = {}) {
        const key = this._getCacheKey(url, options);
        if (!this._prefetchCache.has(key)) {
            this._prefetchCache.set(key, this.fetchData(url, options));
        }
    }

    // 针对具体接口的便捷预取包装（与正式请求签名保持一致）
    prefetchSpeak(action) {
        // 为 /speak 预取增加 TTS 音频的预加载：
        // 1. 预取 /speak 接口（可能在服务端同步生成 TTS 并返回 audio_path）
        // 2. 如果返回包含 audio_path，则在前端用 audioManager 预加载音频至内存缓存
        const url = '/speak';
        const options = {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(action)
        };
        const key = this._getCacheKey(url, options);
        if (!this._prefetchCache.has(key)) {
            const p = this.fetchData(url, options).then(resp => {
                try {
                    if (resp && resp.audio_path && window.audioManager) {
                        // 预先将音频加载进 AudioManager 的缓存
                        return window.audioManager.loadAudio(resp.audio_path).then(() => resp).catch(() => resp);
                    }
                } catch (e) {
                    console.warn('预加载TTS音频失败（忽略）：', e);
                }
                return resp;
            });
            this._prefetchCache.set(key, p);
        }
    }

    prefetchDivine(action) {
        this.prefetch('/divine', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(action)
        });
    }

    prefetchDecideCureOrPoison(action) {
        this.prefetch('/decide_cure_or_poison', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(action)
        });
    }

    prefetchDecideKill(action) {
        this.prefetch('/decide_kill', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(action)
        });
    }

    prefetchCheckWinner() {
        this.prefetch('/check_winner');
    }

    prefetchCurrentTime() {
        this.prefetch('/current_time');
    }

    async startGame() {
        return this.fetchData('/start', { method: 'GET' });
    }

    async getStatus() {
        return this.fetchData('/status');
    }

    async divine(action) {
        return this._fetchWithCache('/divine', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(action)
        });
    }

    async decideKill(action) {
        // 使用缓存以支持在狼人阶段“边播放边预取”的提前决策
        return this._fetchWithCache('/decide_kill', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(action)
        });
    }

    async resetWolfWantKill() {
        return this.fetchData('/reset_wolf_want_kill', { method: 'POST' });
    }

    async getWolfWantKill() {
        return this.fetchData('/get_wolf_want_kill');
    }

    async decideCureOrPoison(action) {
        return this._fetchWithCache('/decide_cure_or_poison', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(action)
        });
    }

    async kill(action) {
        return this.fetchData('/kill', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(action)
        });
    }

    async getCurrentTime() {
        return this._fetchWithCache('/current_time');
    }

    async lastWords(action) {
        return this.fetchData('/last_words', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(action)
        });
    }

    async revenge(action) {
        return this.fetchData('/revenge', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(action)
        });
    }

    async attack(action) {
        return this.fetchData('/attack', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(action)
        });
    }

    async poison(action) {
        return this.fetchData('/poison', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(action)
        });
    }

    async cure(action) {
        return this.fetchData('/cure', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(action)
        });
    }

    async toggleDayNight() {
        return this.fetchData('/toggle_day_night', { method: 'POST' });
    }

    async speak(action) {
        return this._fetchWithCache('/speak', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(action)
        });
    }

    // 新增：仅决策不落库的AI投票接口
    prefetchDecideVote(action) {
        this.prefetch('/decide_vote', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(action)
        });
    }

    async decideVote(action) {
        return this._fetchWithCache('/decide_vote', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(action)
        });
    }

    async resetVoteResult() {
        return this.fetchData('/reset_vote_result', { method: 'POST' });
    }

    prefetchVote(action) {
        // 不要对有副作用的接口进行预取，避免提前投票导致顺序错乱
        // 保留空实现以兼容现有调用
    }

    async vote(action) {
        // 每次直接提交到后端，避免命中可能存在的缓存
        return this.fetchData('/vote', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(action)
        });
    }

    prefetchGetVoteResult() {
        // 由于投票结果在所有玩家投票完成后才稳定，避免预取导致读取到中间态
        // this.prefetch('/get_vote_result');
    }

    async getVoteResult() {
        // 始终拉取最新投票结果，避免使用可能过期的预取缓存
        return this.fetchData('/get_vote_result');
    }

    async execute() {
        return this.fetchData('/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
    }

    async checkWinner() {
        // 胜负判定对“状态一致性”要求高，不使用缓存，确保拿到最新结果
        return this.fetchData('/check_winner');
    }

    async getHistory() {
        return this.fetchData('/get_history');
    }

    // TTS相关API
    async generateTTS(text, voice = null, model = "tts-1", useCache = true) {
        const requestBody = {
            text: text,
            model: model,
            use_cache: useCache
        };

        // 只有在明确指定音色时才传递voice参数
        if (voice !== null) {
            requestBody.voice = voice;
        }

        return this.fetchData('/generate_tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
    }

    async getTTSStatus() {
        return this.fetchData('/tts_status');
    }

    async clearTTSCache() {
        return this.fetchData('/clear_tts_cache', {
            method: 'POST'
        });
    }
}

export default GameData;