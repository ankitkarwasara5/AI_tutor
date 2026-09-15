class LocalAITutor {
    constructor() {
        this.apiBase = window.location.origin;
        this.currentTopic = '';
        this.currentTopicHash = '';
        this.currentStudyGuide = null;
        this.currentSection = null;
        this.currentSectionIndex = 0;
        this.completedSections = new Set();
        this.sectionStartTime = null;
        this.settings = { difficulty: 'medium' };
        this.init();
    }

    async init() {
        this.loadSettings();
        this.setupEventListeners();
        await this.checkSystemStatus();
    }

    async request(path, options = {}) {
        const response = await fetch(`${this.apiBase}${path}`, {
            credentials: 'include',
            ...options,
        });

        let payload = null;
        try {
            payload = await response.json();
        } catch (_) {
            payload = null;
        }

        if (!response.ok) {
            const detail = payload?.detail;
            const message = Array.isArray(detail)
                ? detail.map(item => item.msg).join(', ')
                : detail || `Request failed with status ${response.status}`;
            throw new Error(message);
        }
        return payload;
    }

    async checkSystemStatus() {
        const statusEl = document.getElementById('ai-status');
        const modelEl = document.getElementById('active-model');
        try {
            const data = await this.request('/api/health');
            if (data.model_available && data.active_model) {
                statusEl.textContent = 'Ollama connected';
                statusEl.className = 'status-pill is-online';
                modelEl.textContent = data.active_model;
            } else {
                statusEl.textContent = 'Offline scaffold';
                statusEl.className = 'status-pill is-offline';
                modelEl.textContent = 'Start Ollama for full teaching content';
            }
        } catch (_) {
            statusEl.textContent = 'API unavailable';
            statusEl.className = 'status-pill is-offline';
            modelEl.textContent = 'Unable to reach backend';
        }
    }

    loadSettings() {
        const difficulty = localStorage.getItem('difficulty') || 'medium';
        this.settings.difficulty = difficulty;
        const quickSelect = document.getElementById('difficulty-select');
        const settingsSelect = document.getElementById('default-difficulty');
        if (quickSelect) quickSelect.value = difficulty;
        if (settingsSelect) settingsSelect.value = difficulty;
    }

    setupEventListeners() {
        document.getElementById('topic-search').addEventListener('keydown', event => {
            if (event.key === 'Enter') this.generateStudyGuide();
        });
        document.getElementById('difficulty-select').addEventListener('change', event => {
            this.settings.difficulty = event.target.value;
            localStorage.setItem('difficulty', event.target.value);
        });
    }

    selectQuickTopic(topic) {
        document.getElementById('topic-search').value = topic;
        this.generateStudyGuide();
    }

    async generateStudyGuide() {
        const input = document.getElementById('topic-search');
        const topic = input.value.trim();
        if (topic.length < 2) {
            this.showNotification('Enter a topic with at least two characters.', 'error');
            input.focus();
            return;
        }

        this.currentTopic = topic;
        this.settings.difficulty = document.getElementById('difficulty-select').value;
        this.showLoading(
            'Designing your curriculum',
            'Sequencing concepts, objectives, prerequisites, and practice…',
        );

        try {
            const data = await this.request('/api/study-guide', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic, difficulty: this.settings.difficulty }),
            });
            this.currentStudyGuide = data.structure;
            this.currentTopicHash = data.topic_hash;
            await this.loadProgress();
            this.renderStudyGuide();
            this.showPage('study-guide-page');
        } catch (error) {
            this.showNotification(error.message || 'Could not create the study guide.', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async loadProgress() {
        if (!this.currentTopicHash) return;
        try {
            const data = await this.request(`/api/progress/${this.currentTopicHash}`);
            this.completedSections.clear();
            Object.entries(data.progress || {}).forEach(([index, item]) => {
                if (item.completed) this.completedSections.add(Number(index));
            });
        } catch (_) {
            this.completedSections.clear();
        }
    }

    async saveProgress(sectionIndex, completed = true, studyTime = 0) {
        if (!this.currentTopicHash) return;
        await this.request('/api/progress/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                topic: this.currentTopic,
                topic_hash: this.currentTopicHash,
                section_index: sectionIndex,
                completed,
                study_time: Math.max(0, studyTime),
            }),
        });
    }

    renderStudyGuide() {
        const guide = this.currentStudyGuide;
        if (!guide) return;

        document.getElementById('guide-title').textContent = `${this.currentTopic} — Study Guide`;
        document.getElementById('guide-overview').textContent = guide.overview || '';
        document.getElementById('guide-difficulty').textContent = this.capitalize(this.settings.difficulty);
        document.getElementById('guide-time').textContent = guide.estimated_time || 'Self-paced';
        document.getElementById('guide-sections').textContent = `${guide.sections.length} sections`;
        document.getElementById('guide-speed-info').textContent = 'Curriculum v2';

        this.renderList('guide-prerequisites', guide.prerequisites || []);
        this.renderList('guide-outcomes', guide.learning_outcomes || []);
        const insights = document.getElementById('guide-insights');
        insights.hidden = !(guide.prerequisites?.length || guide.learning_outcomes?.length);

        const container = document.getElementById('sections-container');
        container.replaceChildren();

        guide.sections.forEach((section, index) => {
            const card = document.createElement('article');
            card.className = `section-card${this.completedSections.has(index) ? ' completed' : ''}`;
            card.tabIndex = 0;
            card.setAttribute('role', 'button');
            card.addEventListener('click', () => this.openSection(index));
            card.addEventListener('keydown', event => {
                if (event.key === 'Enter' || event.key === ' ') this.openSection(index);
            });

            const number = document.createElement('div');
            number.className = 'section-index';
            number.textContent = this.completedSections.has(index) ? '✓' : String(index + 1);

            const copy = document.createElement('div');
            const title = document.createElement('h3');
            title.textContent = section.title;
            const overview = document.createElement('p');
            overview.textContent = section.overview || '';
            copy.append(title, overview);

            if (section.key_concepts?.length) {
                const concepts = document.createElement('div');
                concepts.className = 'concept-chips';
                section.key_concepts.slice(0, 4).forEach(label => {
                    const chip = document.createElement('span');
                    chip.textContent = label;
                    concepts.appendChild(chip);
                });
                copy.appendChild(concepts);
            }

            const time = document.createElement('span');
            time.className = 'section-card__time';
            time.textContent = section.estimated_time || '';

            card.append(number, copy, time);
            container.appendChild(card);
        });

        this.updateStudyProgress();
    }

    renderList(elementId, values) {
        const element = document.getElementById(elementId);
        element.replaceChildren();
        values.forEach(value => {
            const item = document.createElement('li');
            item.textContent = value;
            element.appendChild(item);
        });
    }

    updateStudyProgress() {
        const total = this.currentStudyGuide?.sections?.length || 0;
        const done = this.completedSections.size;
        const percent = total ? Math.round((done / total) * 100) : 0;
        document.getElementById('study-progress-fill').style.width = `${percent}%`;
        document.getElementById('study-progress-text').textContent = `${percent}% complete (${done}/${total})`;
    }

    async openSection(sectionIndex) {
        const sections = this.currentStudyGuide?.sections;
        if (!sections || !sections[sectionIndex]) return;

        this.currentSectionIndex = sectionIndex;
        this.currentSection = sections[sectionIndex];
        this.sectionStartTime = Date.now();

        document.getElementById('section-number').textContent = `SECTION ${sectionIndex + 1}`;
        document.getElementById('section-title').textContent = this.currentSection.title;
        document.getElementById('section-overview').textContent = this.currentSection.overview || '';
        document.getElementById('section-difficulty').textContent = this.capitalize(this.settings.difficulty);
        document.getElementById('section-time').textContent = this.currentSection.estimated_time || 'Self-paced';
        document.getElementById('section-progress-text').textContent = `${sectionIndex + 1} of ${sections.length}`;
        this.renderObjectives(this.currentSection.learning_objectives || []);

        document.getElementById('prev-section-btn').disabled = sectionIndex === 0;
        document.getElementById('next-section-btn').disabled = sectionIndex === sections.length - 1;
        this.syncCompleteButton();
        this.showPage('section-page');
        await this.loadSectionContent();
    }

    renderObjectives(objectives) {
        const container = document.getElementById('section-objectives');
        container.replaceChildren();
        objectives.slice(0, 4).forEach(objective => {
            const item = document.createElement('span');
            item.textContent = objective;
            container.appendChild(item);
        });
    }

    sectionPayload() {
        return {
            topic: this.currentTopic,
            section_title: this.currentSection.title,
            section_index: this.currentSectionIndex,
            difficulty: this.settings.difficulty,
            section_overview: this.currentSection.overview || null,
            learning_objectives: this.currentSection.learning_objectives || [],
        };
    }

    async loadSectionContent() {
        const container = document.getElementById('section-content-container');
        container.innerHTML = '<p>Building lesson content…</p>';
        try {
            const data = await this.request('/api/section-content', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.sectionPayload()),
            });
            this.renderSectionContent(data);
        } catch (error) {
            container.replaceChildren(this.createErrorMessage(error.message));
        }
    }

    renderSectionContent(data) {
        const container = document.getElementById('section-content-container');
        container.replaceChildren();

        const meta = document.createElement('div');
        meta.className = 'content-meta';
        [
            data.cached ? 'Cached lesson' : 'Fresh lesson',
            data.model_used || 'Unknown runtime',
            data.generation_time || '',
        ].filter(Boolean).forEach(label => {
            const badge = document.createElement('span');
            badge.className = 'content-badge';
            badge.textContent = label;
            meta.appendChild(badge);
        });

        const content = document.createElement('div');
        content.className = 'formatted-content';
        this.renderMarkdownSafely(data.content || '', content);
        container.append(meta, content);
    }

    renderMarkdownSafely(markdown, container) {
        const lines = markdown.split(/\r?\n/);
        let list = null;
        let listType = null;
        let codeBlock = null;

        const closeList = () => {
            list = null;
            listType = null;
        };

        lines.forEach(rawLine => {
            const trimmed = rawLine.trim();

            if (trimmed.startsWith('```')) {
                closeList();
                if (codeBlock) {
                    container.appendChild(codeBlock);
                    codeBlock = null;
                } else {
                    codeBlock = document.createElement('pre');
                }
                return;
            }

            if (codeBlock) {
                const codeLine = document.createTextNode(`${rawLine}\n`);
                codeBlock.appendChild(codeLine);
                return;
            }

            if (!trimmed) {
                closeList();
                return;
            }

            const heading = trimmed.match(/^(#{2,4})\s+(.+)$/);
            if (heading) {
                closeList();
                const level = Math.min(heading[1].length + 1, 5);
                const element = document.createElement(`h${level}`);
                element.textContent = heading[2];
                container.appendChild(element);
                return;
            }

            const bullet = trimmed.match(/^[-*]\s+(.+)$/);
            const ordered = trimmed.match(/^\d+\.\s+(.+)$/);
            if (bullet || ordered) {
                const type = ordered ? 'ol' : 'ul';
                if (!list || listType !== type) {
                    list = document.createElement(type);
                    listType = type;
                    container.appendChild(list);
                }
                const item = document.createElement('li');
                item.textContent = (ordered ? ordered[1] : bullet[1]).replace(/\*\*/g, '');
                list.appendChild(item);
                return;
            }

            closeList();
            const paragraph = document.createElement('p');
            paragraph.textContent = trimmed.replace(/\*\*/g, '');
            container.appendChild(paragraph);
        });

        if (codeBlock) container.appendChild(codeBlock);
    }

    async regenerateSection() {
        if (!this.currentSection) return;
        this.showLoading(
            'Regenerating lesson',
            'Creating a fresh explanation, example, and practice set…',
        );
        try {
            const data = await this.request('/api/regenerate-content', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.sectionPayload()),
            });
            this.renderSectionContent(data);
            this.showNotification('Lesson regenerated.', 'success');
        } catch (error) {
            this.showNotification(error.message || 'Regeneration failed.', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async markSectionComplete() {
        const index = this.currentSectionIndex;
        const completing = !this.completedSections.has(index);
        const studyTime = this.sectionStartTime
            ? (Date.now() - this.sectionStartTime) / 1000
            : 0;
        try {
            await this.saveProgress(index, completing, studyTime);
            if (completing) this.completedSections.add(index);
            else this.completedSections.delete(index);
            this.sectionStartTime = Date.now();
            this.syncCompleteButton();
            this.updateStudyProgress();
            this.showNotification(
                completing ? 'Section marked complete.' : 'Section reopened.',
                'success',
            );
        } catch (error) {
            this.showNotification(error.message || 'Could not save progress.', 'error');
        }
    }

    syncCompleteButton() {
        const button = document.getElementById('mark-complete-btn');
        const completed = this.completedSections.has(this.currentSectionIndex);
        button.textContent = completed ? 'Completed' : 'Mark complete';
        button.classList.toggle('completed', completed);
    }

    async navigateSection(direction) {
        const nextIndex = this.currentSectionIndex + direction;
        const count = this.currentStudyGuide?.sections?.length || 0;
        if (nextIndex < 0 || nextIndex >= count) return;
        await this.persistElapsedTime();
        await this.openSection(nextIndex);
    }

    startLinearStudy() {
        if (this.currentStudyGuide?.sections?.length) this.openSection(0);
    }

    async persistElapsedTime() {
        if (!this.sectionStartTime || !this.currentTopicHash) return;
        const elapsed = (Date.now() - this.sectionStartTime) / 1000;
        try {
            await this.saveProgress(
                this.currentSectionIndex,
                this.completedSections.has(this.currentSectionIndex),
                elapsed,
            );
        } catch (_) {
            // Navigation should remain usable if progress persistence fails.
        }
        this.sectionStartTime = Date.now();
    }

    async goBackToGuide() {
        await this.persistElapsedTime();
        this.renderStudyGuide();
        this.showPage('study-guide-page');
    }

    showPage(pageId) {
        document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
        document.getElementById(pageId)?.classList.add('active');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    showLoading(title, subtitle = '') {
        document.getElementById('loading-text').textContent = title;
        document.getElementById('loading-subtext').textContent = subtitle;
        document.getElementById('loading-overlay').style.display = 'grid';
    }

    hideLoading() {
        document.getElementById('loading-overlay').style.display = 'none';
    }

    showNotification(message, type = 'info') {
        const notice = document.createElement('div');
        notice.className = `notification notification--${type}`;
        const content = document.createElement('div');
        content.className = 'notification-content';
        const text = document.createElement('span');
        text.textContent = message;
        const close = document.createElement('button');
        close.className = 'notification-close';
        close.type = 'button';
        close.textContent = '×';
        close.addEventListener('click', () => notice.remove());
        content.append(text, close);
        notice.appendChild(content);
        document.body.appendChild(notice);
        setTimeout(() => notice.remove(), 4000);
    }

    createErrorMessage(message) {
        const box = document.createElement('div');
        box.className = 'error-message';
        const title = document.createElement('strong');
        title.textContent = 'Unable to load this content.';
        const detail = document.createElement('p');
        detail.textContent = message || 'Please try again.';
        box.append(title, detail);
        return box;
    }

    saveSettings() {
        const difficulty = document.getElementById('default-difficulty').value;
        localStorage.setItem('difficulty', difficulty);
        this.settings.difficulty = difficulty;
        document.getElementById('difficulty-select').value = difficulty;
        this.showNotification('Settings saved.', 'success');
    }

    resetSettings() {
        localStorage.removeItem('difficulty');
        this.settings.difficulty = 'medium';
        document.getElementById('difficulty-select').value = 'medium';
        document.getElementById('default-difficulty').value = 'medium';
        this.showNotification('Settings reset.', 'success');
    }

    capitalize(value) {
        return value ? value.charAt(0).toUpperCase() + value.slice(1) : '';
    }
}

const app = new LocalAITutor();
window.app = app;
window.showPage = pageId => app.showPage(pageId);
window.selectQuickTopic = topic => app.selectQuickTopic(topic);
window.generateStudyGuide = () => app.generateStudyGuide();
window.startLinearStudy = () => app.startLinearStudy();
window.navigateSection = direction => app.navigateSection(direction);
window.markSectionComplete = () => app.markSectionComplete();
window.regenerateSection = () => app.regenerateSection();
window.goBackToGuide = () => app.goBackToGuide();
window.saveSettings = () => app.saveSettings();
window.resetSettings = () => app.resetSettings();
