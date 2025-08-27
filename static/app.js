
// AI Learning Tutor - SPEED OPTIMIZED for M3 MacBook
class SpeedOptimizedAITutor {
    constructor() {
        this.apiBase = window.location.origin;
        this.currentTopic = '';
        this.currentTopicHash = '';
        this.currentStudyGuide = null;
        this.currentSection = null;
        this.currentSectionIndex = 0;
        this.completedSections = new Set();
        this.sectionContent = {};
        this.sessionId = '';
        
        this.settings = {
            difficulty: 'medium',
            contentDepth: 'standard'
        };
        
        // Speed tracking
        this.generationTimes = {
            studyGuide: 0,
            sections: {}
        };
        
        this.init();
    }
    
    async init() {
        console.log('⚡ Initializing SPEED-OPTIMIZED AI Learning Tutor...');
        try {
            await this.checkSystemStatus();
            this.loadSettings();
            this.setupEventListeners();
            console.log('✅ Speed-optimized AI Learning Tutor initialized!');
        } catch (error) {
            console.error('❌ Initialization failed:', error);
        }
    }
    
    async checkSystemStatus() {
        try {
            const response = await fetch(`${this.apiBase}/api/health`);
            const data = await response.json();
            
            const statusEl = document.getElementById('ai-status');
            const modelEl = document.getElementById('active-model');
            
            if (data.model_available && data.fast_model) {
                statusEl.textContent = '⚡ Speed Optimized';
                statusEl.style.color = '#22c55e';
                if (modelEl) modelEl.textContent = `${data.fast_model} (Speed Mode)`;
            } else {
                statusEl.textContent = '⚡ Speed Templates';
                statusEl.style.color = '#f59e0b';
                if (modelEl) modelEl.textContent = 'Fast Templates';
            }
            
            if (data.speed_optimized) {
                this.showNotification(`⚡ Speed optimized! Target: ${data.target_generation_time}`, 'success');
            }
            
            console.log('⚡ System Status:', data);
        } catch (error) {
            console.error('❌ Failed to check system status:', error);
        }
    }
    
    loadSettings() {
        const savedDifficulty = localStorage.getItem('difficulty') || 'medium';
        
        this.settings = {
            difficulty: savedDifficulty,
            contentDepth: 'standard'
        };
        
        if (document.getElementById('difficulty-select')) {
            document.getElementById('difficulty-select').value = savedDifficulty;
        }
        
        console.log('📋 Settings loaded:', this.settings);
    }
    
    selectQuickTopic(topic) {
        document.getElementById('topic-search').value = topic;
        this.generateStudyGuide();
    }
    
    async generateStudyGuide() {
        const topicInput = document.getElementById('topic-search').value.trim();
        
        if (!topicInput || topicInput.length < 2) {
            this.showNotification('Please enter a valid topic', 'warning');
            return;
        }
        
        this.currentTopic = topicInput;
        this.settings.difficulty = document.getElementById('difficulty-select').value;
        
        console.log('⚡ Speed-generating study guide for:', this.currentTopic);
        this.showSpeedLoading('Creating study guide...', 'Expected: 2-5 seconds');
        
        const startTime = Date.now();
        
        try {
            const response = await fetch(`${this.apiBase}/api/study-guide`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    topic: this.currentTopic,
                    difficulty: this.settings.difficulty
                }),
                credentials: 'include'
            });
            
            const data = await response.json();
            const elapsed = (Date.now() - startTime) / 1000;
            
            this.currentStudyGuide = data.structure;
            this.currentTopicHash = data.topic_hash;
            this.sessionId = data.session_id;
            this.generationTimes.studyGuide = elapsed;
            
            await this.loadProgress();
            this.renderStudyGuide();
            this.showPage('study-guide-page');
            
            console.log(`✅ Study guide ready in ${elapsed.toFixed(1)}s`);
            this.showNotification(`⚡ Study guide generated in ${elapsed.toFixed(1)}s!`, 'success');
            
        } catch (error) {
            console.error('❌ Failed to generate study guide:', error);
            this.showNotification('Failed to generate study guide. Please try again.', 'error');
        } finally {
            this.hideLoading();
        }
    }
    
    async loadProgress() {
        if (!this.currentTopicHash) return;
        
        try {
            const response = await fetch(`${this.apiBase}/api/progress/${this.currentTopicHash}`, {
                credentials: 'include'
            });
            const progressData = await response.json();
            
            this.completedSections.clear();
            for (const [sectionIndex, progress] of Object.entries(progressData.progress)) {
                if (progress.completed) {
                    this.completedSections.add(parseInt(sectionIndex));
                }
            }
            
            console.log('💾 Loaded progress:', progressData);
            
            if (progressData.completed_sections > 0) {
                this.showNotification(`💾 Welcome back! ${progressData.completed_sections} sections completed`, 'success');
            }
        } catch (error) {
            console.error('❌ Failed to load progress:', error);
        }
    }
    
    async saveProgress(sectionIndex, completed = true, studyTime = 0) {
        if (!this.currentTopicHash) return;
        
        try {
            const response = await fetch(`${this.apiBase}/api/progress/update`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    topic: this.currentTopic,
                    topic_hash: this.currentTopicHash,
                    section_index: sectionIndex,
                    completed: completed,
                    study_time: studyTime
                }),
                credentials: 'include'
            });
            
            const result = await response.json();
            if (result.success) {
                console.log('💾 Progress saved:', {sectionIndex, completed, studyTime});
            }
        } catch (error) {
            console.error('❌ Failed to save progress:', error);
        }
    }
    
    renderStudyGuide() {
        if (!this.currentStudyGuide) return;
        
        // Update header with speed info
        document.getElementById('guide-title').textContent = `${this.currentTopic} - Study Guide`;
        document.getElementById('guide-overview').textContent = this.currentStudyGuide.overview || `Speed-optimized study guide for ${this.currentTopic}`;
        document.getElementById('guide-difficulty').textContent = this.settings.difficulty.charAt(0).toUpperCase() + this.settings.difficulty.slice(1);
        document.getElementById('guide-time').textContent = `⏱️ ${this.currentStudyGuide.estimated_time || '2-3 hours'}`;
        document.getElementById('guide-sections').textContent = `📚 ${this.currentStudyGuide.sections.length} sections`;
        
        // Add speed info
        if (this.generationTimes.studyGuide > 0) {
            const speedInfo = document.getElementById('guide-speed-info');
            if (speedInfo) {
                speedInfo.textContent = `⚡ Generated in ${this.generationTimes.studyGuide.toFixed(1)}s`;
            }
        }
        
        this.updateStudyProgress();
        
        // Render sections with speed indicators
        const sectionsContainer = document.getElementById('sections-container');
        sectionsContainer.innerHTML = this.currentStudyGuide.sections.map((section, index) => {
            const sectionTime = this.generationTimes.sections[index] || null;
            const speedBadge = sectionTime ? `<span class="speed-badge">⚡ ${sectionTime.toFixed(1)}s</span>` : '';
            
            return `
                <div class="section-card ${this.completedSections.has(index) ? 'completed' : ''}" onclick="app.openSection(${index})">
                    <div class="section-header">
                        <div class="section-number">Section ${section.id || index + 1}</div>
                        <div class="section-status">
                            ${this.completedSections.has(index) ? '✅' : '📖'}
                        </div>
                    </div>
                    <h3 class="section-title">${section.title}</h3>
                    <p class="section-overview">${section.overview}</p>
                    <div class="section-objectives">
                        <strong>Learning Objectives:</strong>
                        <ul>
                            ${section.learning_objectives.map(obj => `<li>${obj}</li>`).join('')}
                        </ul>
                    </div>
                    <div class="section-footer">
                        <span class="section-time">⏱️ ${section.estimated_time}</span>
                        <div class="section-actions">
                            ${speedBadge}
                            <span class="section-action">
                                ${this.completedSections.has(index) ? 'Review →' : 'Study →'}
                            </span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }
    
    updateStudyProgress() {
        const totalSections = this.currentStudyGuide?.sections.length || 0;
        const completedCount = this.completedSections.size;
        const percentage = totalSections > 0 ? Math.round((completedCount / totalSections) * 100) : 0;
        
        document.getElementById('study-progress-fill').style.width = `${percentage}%`;
        document.getElementById('study-progress-text').textContent = 
            `${percentage}% Complete (${completedCount}/${totalSections} sections)`;
    }
    
    async openSection(sectionIndex) {
        if (!this.currentStudyGuide || sectionIndex >= this.currentStudyGuide.sections.length) {
            return;
        }
        
        this.currentSectionIndex = sectionIndex;
        this.currentSection = this.currentStudyGuide.sections[sectionIndex];
        this.sectionStartTime = Date.now();
        
        console.log('📖 Opening section:', this.currentSection.title);
        
        // Update section page header
        document.getElementById('section-title').textContent = this.currentSection.title;
        document.getElementById('section-number').textContent = `Section ${this.currentSection.id || sectionIndex + 1}`;
        document.getElementById('section-time').textContent = `⏱️ ${this.currentSection.estimated_time}`;
        document.getElementById('section-difficulty').textContent = this.settings.difficulty.charAt(0).toUpperCase() + this.settings.difficulty.slice(1);
        document.getElementById('section-progress-text').textContent = 
            `Section ${sectionIndex + 1} of ${this.currentStudyGuide.sections.length}`;
        
        // Update navigation buttons
        document.getElementById('prev-section-btn').disabled = sectionIndex === 0;
        document.getElementById('next-section-btn').disabled = sectionIndex === this.currentStudyGuide.sections.length - 1;
        
        // Update completion button
        const completeBtn = document.getElementById('mark-complete-btn');
        if (this.completedSections.has(sectionIndex)) {
            completeBtn.textContent = '✅ Completed';
            completeBtn.classList.add('completed');
        } else {
            completeBtn.textContent = '✅ Mark as Complete';
            completeBtn.classList.remove('completed');
        }
        
        this.showPage('section-page');
        await this.loadSectionContent();
    }
    
    async loadSectionContent() {
        const contentContainer = document.getElementById('section-content-container');
        
        // Show speed-optimized loading
        contentContainer.innerHTML = `
            <div class="speed-loading-message">
                <div class="loading-spinner speed-spinner"></div>
                <p>⚡ Speed-generating content for "${this.currentSection.title}"...</p>
                <small>Expected: 3-8 seconds with fast models</small>
                <div class="speed-progress">
                    <div class="speed-progress-bar"></div>
                </div>
            </div>
        `;
        
        const startTime = Date.now();
        
        try {
            const response = await fetch(`${this.apiBase}/api/section-content`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    topic: this.currentTopic,
                    section_title: this.currentSection.title,
                    section_index: this.currentSectionIndex,
                    difficulty: this.settings.difficulty
                }),
                credentials: 'include'
            });
            
            const contentData = await response.json();
            const elapsed = (Date.now() - startTime) / 1000;
            
            // Store generation time
            this.generationTimes.sections[this.currentSectionIndex] = elapsed;
            
            this.renderSectionContent(contentData, elapsed);
            
            if (contentData.cached) {
                this.showNotification('💾 Loaded cached content instantly!', 'success');
            } else {
                this.showNotification(`⚡ Generated in ${elapsed.toFixed(1)}s!`, 'success');
            }
            
            console.log(`✅ Section content loaded in ${elapsed.toFixed(1)}s`);
        } catch (error) {
            console.error('❌ Failed to load section content:', error);
            contentContainer.innerHTML = `
                <div class="error-message">
                    <h3>❌ Failed to load content</h3>
                    <p>Unable to load content for this section. Please try again.</p>
                    <button class="btn btn--primary" onclick="app.loadSectionContent()">
                        🔄 Retry
                    </button>
                </div>
            `;
        }
    }
    
    renderSectionContent(contentData, generationTime = null) {
        const contentContainer = document.getElementById('section-content-container');
        
        // Enhanced content formatting
        let formattedContent = contentData.content;
        
        // Better markdown processing
        formattedContent = formattedContent
            .replace(/^## (.*$)/gim, '<h3>$1</h3>')
            .replace(/^### (.*$)/gim, '<h4>$1</h4>')
            .replace(/^#### (.*$)/gim, '<h5>$1</h5>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        if (!formattedContent.startsWith('<h') && !formattedContent.startsWith('<p>')) {
            formattedContent = `<p>${formattedContent}</p>`;
        }
        
        const speedBadge = generationTime ? 
            `<span class="content-badge speed-badge">⚡ Generated in ${generationTime.toFixed(1)}s</span>` : '';
        
        contentContainer.innerHTML = `
            <article class="section-content-article">
                <div class="content-meta">
                    <span class="content-badge ${contentData.cached ? 'cached' : 'fresh'}">
                        ${contentData.cached ? '💾 Cached Content' : '✨ Fresh Content'}
                        ${contentData.model_used ? ` (${contentData.model_used})` : ''}
                    </span>
                    ${speedBadge}
                    ${contentData.generation_time ? `<span class="content-badge">⏱️ ${contentData.generation_time}</span>` : ''}
                </div>
                <div class="formatted-content">
                    ${formattedContent}
                </div>
            </article>
        `;
    }
    
    async regenerateSection() {
        if (!this.currentSection) {
            this.showNotification('No section selected for regeneration', 'warning');
            return;
        }
        
        console.log('⚡ Speed-regenerating content for:', this.currentSection.title);
        
        const contentContainer = document.getElementById('section-content-container');
        
        // Show speed-optimized regeneration loading
        contentContainer.innerHTML = `
            <div class="speed-loading-message regenerate-loading">
                <div class="loading-spinner speed-spinner"></div>
                <p>🔄 Speed-regenerating "${this.currentSection.title}"...</p>
                <small>Creating fresh content in 3-8 seconds...</small>
                <div class="speed-progress">
                    <div class="speed-progress-bar regenerate-progress"></div>
                </div>
            </div>
        `;
        
        const startTime = Date.now();
        
        try {
            const response = await fetch(`${this.apiBase}/api/regenerate-content`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    topic: this.currentTopic,
                    section_title: this.currentSection.title,
                    section_index: this.currentSectionIndex,
                    difficulty: this.settings.difficulty
                }),
                credentials: 'include'
            });
            
            const contentData = await response.json();
            const elapsed = (Date.now() - startTime) / 1000;
            
            // Update generation time
            this.generationTimes.sections[this.currentSectionIndex] = elapsed;
            
            this.renderSectionContent(contentData, elapsed);
            
            this.showNotification(`🔄⚡ Content regenerated in ${elapsed.toFixed(1)}s!`, 'success');
            console.log(`✅ Content regenerated in ${elapsed.toFixed(1)}s`);
        } catch (error) {
            console.error('❌ Failed to regenerate content:', error);
            contentContainer.innerHTML = `
                <div class="error-message">
                    <h3>❌ Failed to regenerate content</h3>
                    <p>Unable to regenerate content. Please try again.</p>
                    <button class="btn btn--primary" onclick="app.regenerateSection()">
                        🔄 Try Again
                    </button>
                </div>
            `;
            this.showNotification('Failed to regenerate content. Please try again.', 'error');
        }
    }
    
    markSectionComplete() {
        const wasCompleted = this.completedSections.has(this.currentSectionIndex);
        const studyTime = this.sectionStartTime ? (Date.now() - this.sectionStartTime) / 1000 : 0;
        
        if (wasCompleted) {
            this.completedSections.delete(this.currentSectionIndex);
            document.getElementById('mark-complete-btn').textContent = '✅ Mark as Complete';
            document.getElementById('mark-complete-btn').classList.remove('completed');
            this.saveProgress(this.currentSectionIndex, false, studyTime);
            this.showNotification('Section marked as incomplete', 'info');
        } else {
            this.completedSections.add(this.currentSectionIndex);
            document.getElementById('mark-complete-btn').textContent = '✅ Completed';
            document.getElementById('mark-complete-btn').classList.add('completed');
            this.saveProgress(this.currentSectionIndex, true, studyTime);
            this.showNotification('🎉 Section completed!', 'success');
        }
        
        this.updateStudyProgress();
    }
    
    navigateSection(direction) {
        const newIndex = this.currentSectionIndex + direction;
        
        if (newIndex >= 0 && newIndex < this.currentStudyGuide.sections.length) {
            if (this.sectionStartTime) {
                const studyTime = (Date.now() - this.sectionStartTime) / 1000;
                this.saveProgress(this.currentSectionIndex, this.completedSections.has(this.currentSectionIndex), studyTime);
            }
            
            this.openSection(newIndex);
        }
    }
    
    startLinearStudy() {
        this.openSection(0);
    }
    
    setupEventListeners() {
        document.getElementById('topic-search').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.generateStudyGuide();
            }
        });
        
        document.getElementById('difficulty-select').addEventListener('change', (e) => {
            this.settings.difficulty = e.target.value;
            localStorage.setItem('difficulty', e.target.value);
        });
    }
    
    showSpeedLoading(text = 'Loading...', subText = '') {
        const overlay = document.getElementById('loading-overlay');
        const loadingText = document.getElementById('loading-text');
        const loadingSubtext = document.getElementById('loading-subtext') || 
            document.createElement('small');
        
        if (overlay) overlay.style.display = 'flex';
        if (loadingText) loadingText.textContent = text;
        
        if (!document.getElementById('loading-subtext')) {
            loadingSubtext.id = 'loading-subtext';
            loadingSubtext.style.marginTop = '0.5rem';
            loadingSubtext.style.opacity = '0.7';
            loadingText.parentElement.appendChild(loadingSubtext);
        }
        loadingSubtext.textContent = subText;
    }
    
    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.style.display = 'none';
    }
    
    showPage(pageId) {
        console.log('📄 Showing page:', pageId);
        document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
        const targetPage = document.getElementById(pageId);
        if (targetPage) {
            targetPage.classList.add('active');
        }
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification--${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="notification-close">×</button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 4000); // Faster notification timeout for speed-optimized experience
    }
    
    goBackToGuide() {
        if (this.sectionStartTime) {
            const studyTime = (Date.now() - this.sectionStartTime) / 1000;
            this.saveProgress(this.currentSectionIndex, this.completedSections.has(this.currentSectionIndex), studyTime);
        }
        
        this.showPage('study-guide-page');
        if (this.currentStudyGuide) {
            this.renderStudyGuide();
        }
    }
    
    saveSettings() {
        try {
            const difficulty = document.getElementById('default-difficulty').value;
            
            localStorage.setItem('difficulty', difficulty);
            this.settings = { difficulty, contentDepth: 'standard' };
            
            document.getElementById('difficulty-select').value = difficulty;
            
            this.showNotification('⚡ Settings saved!', 'success');
        } catch (error) {
            this.showNotification('Failed to save settings', 'error');
        }
    }
    
    resetSettings() {
        localStorage.removeItem('difficulty');
        this.loadSettings();
        
        document.getElementById('default-difficulty').value = 'medium';
        
        this.showNotification('🔄 Settings reset!', 'success');
    }
}

// Initialize speed-optimized app
const app = new SpeedOptimizedAITutor();

// Global functions
window.app = app;
window.showPage = (pageId) => app.showPage(pageId);
window.selectQuickTopic = (topic) => app.selectQuickTopic(topic);
window.generateStudyGuide = () => app.generateStudyGuide();
window.startLinearStudy = () => app.startLinearStudy();
window.navigateSection = (direction) => app.navigateSection(direction);
window.markSectionComplete = () => app.markSectionComplete();
window.regenerateSection = () => app.regenerateSection();
window.goBackToGuide = () => app.goBackToGuide();
window.saveSettings = () => app.saveSettings();
window.resetSettings = () => app.resetSettings();

console.log('⚡💾 Speed-Optimized AI Learning Tutor loaded - Target: 3-10 second generation!');
