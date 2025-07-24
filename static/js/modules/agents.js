/**
 * Agent System Module - Handles dynamic agent registry, styling, and workflow visualization
 * Ported from main.js for better separation of concerns
 */

class AgentManager {
    constructor() {
        // Core agent registry - can be extended dynamically
        this.AGENT_REGISTRY = {
            orchestrator: {
                name: "Orchestrator",
                role: "Workflow Coordination", 
                icon: "🎭",
                colors: ["#667eea", "#764ba2"],
                category: "system"
            },
            plot_generator: {
                name: "Plot Generator Agent",
                role: "Story Creation",
                icon: "📚", 
                colors: ["#f093fb", "#f5576c"],
                category: "content"
            },
            author_generator: {
                name: "Author Generator Agent",
                role: "Author Profiles",
                icon: "✍️",
                colors: ["#4facfe", "#00f2fe"],
                category: "content"
            },
            critique: {
                name: "Critique Agent",
                role: "Content Analysis",
                icon: "🔍",
                colors: ["#fa709a", "#fee140"], 
                category: "analysis"
            },
            enhancement: {
                name: "Enhancement Agent", 
                role: "Content Improvement",
                icon: "⚡",
                colors: ["#a8edea", "#fed6e3"],
                category: "improvement"
            },
            scoring: {
                name: "Scoring Agent",
                role: "Quality Evaluation", 
                icon: "📊",
                colors: ["#ffecd2", "#fcb69f"],
                category: "evaluation"
            },
            world_building: {
                name: "World Building Agent",
                role: "World Creation",
                icon: "🌍",
                colors: ["#43e97b", "#38f9d7"],
                category: "content"
            },
            characters: {
                name: "Characters Agent",
                role: "Character Development",
                icon: "👥",
                colors: ["#fa709a", "#fee140"],
                category: "content"
            },
            loregen: {
                name: "Lore Generator Agent",
                role: "Lore Expansion",
                icon: "📜",
                colors: ["#667eea", "#764ba2"],
                category: "content"
            }
        };
        
        this._initializeStyles();
    }

    /**
     * Generate colors for unknown agents automatically
     */
    generateAgentColors(agentId) {
        const hash = agentId.split('').reduce((a, b) => {
            a = ((a << 5) - a) + b.charCodeAt(0);
            return a & a;
        }, 0);
        
        const hue = Math.abs(hash) % 360;
        const saturation = 60 + (Math.abs(hash) % 30); // 60-90%
        const lightness = 45 + (Math.abs(hash) % 20);  // 45-65%
        
        return [
            `hsl(${hue}, ${saturation}%, ${lightness}%)`,
            `hsl(${(hue + 30) % 360}, ${saturation}%, ${lightness + 10}%)`
        ];
    }

    /**
     * Get agent config with fallback for unknown agents
     */
    getAgentConfig(agentId) {
        if (this.AGENT_REGISTRY[agentId]) {
            return this.AGENT_REGISTRY[agentId];
        }
        
        // Auto-generate config for unknown agents
        const colors = this.generateAgentColors(agentId);
        const name = agentId.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
        
        return {
            name: name,
            role: "Specialized Agent",
            icon: "🤖",
            colors: colors,
            category: "custom"
        };
    }

    /**
     * Generate CSS for agent styling
     */
    generateAgentCSS(agentId, config) {
        return `
            .${agentId}-message {
                --agent-gradient: linear-gradient(135deg, ${config.colors[0]} 0%, ${config.colors[1]} 100%);
                --agent-bg: ${config.colors[0]}20;
                --agent-border: ${config.colors[0]}40;
                --agent-text: ${config.colors[0]};
            }
            
            .${agentId}-message .message-avatar {
                background: var(--agent-gradient);
                color: white;
            }
            
            .${agentId}-message .agent-header {
                background: var(--agent-bg);
                border-left: 3px solid var(--agent-text);
                margin-bottom: 0.5rem;
                padding: 0.75rem;
                border-radius: 8px;
            }
        `;
    }

    /**
     * Initialize dynamic agent styles
     */
    _initializeStyles() {
        const styleSheet = document.createElement('style');
        styleSheet.id = 'dynamic-agent-styles';
        
        let css = `
            .agent-header {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                font-size: 0.875rem;
                font-weight: 500;
            }
            
            .agent-avatar-header {
                width: 24px;
                height: 24px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 0.75rem;
                flex-shrink: 0;
            }
            
            .agent-info {
                display: flex;
                flex-direction: column;
                gap: 0.125rem;
            }
            
            .agent-name {
                font-weight: 600;
                color: var(--agent-text);
            }
            
            .agent-role {
                font-size: 0.75rem;
                color: var(--text-secondary);
                opacity: 0.8;
            }
            
            .workflow-card {
                background: var(--bg-secondary);
                border: 1px solid var(--border);
                border-radius: 12px;
                margin: 1rem 0;
                padding: 1rem;
            }
            
            .workflow-header {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                font-weight: 600;
                color: var(--text-primary);
                margin-bottom: 1rem;
            }
            
            .workflow-step {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0.5rem;
                margin: 0.25rem 0;
                border-radius: 6px;
                font-size: 0.875rem;
            }
            
            .workflow-step.pending {
                background: var(--bg-tertiary);
                color: var(--text-secondary);
            }
            
            .workflow-step.active {
                background: var(--primary)20;
                color: var(--primary);
                border-left: 3px solid var(--primary);
            }
            
            .workflow-step.completed {
                background: var(--success)20;
                color: var(--success);
            }
            
            .improvement-cycle {
                background: var(--bg-secondary);
                border: 1px solid var(--border);
                border-radius: 12px;
                margin: 1rem 0;
                padding: 1rem;
            }
            
            .cycle-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 0.75rem;
            }
            
            .cycle-round {
                font-weight: 600;
                color: var(--text-primary);
            }
            
            .cycle-score {
                font-size: 0.875rem;
                color: var(--text-secondary);
            }
        `;
        
        // Generate CSS for all known agents
        Object.keys(this.AGENT_REGISTRY).forEach(agentId => {
            const config = this.AGENT_REGISTRY[agentId];
            css += this.generateAgentCSS(agentId, config);
        });
        
        styleSheet.textContent = css;
        document.head.appendChild(styleSheet);
    }

    /**
     * Add new agent style dynamically
     */
    addAgentStyle(agentId) {
        const config = this.getAgentConfig(agentId);
        const styleSheet = document.getElementById('dynamic-agent-styles');
        if (styleSheet && !styleSheet.textContent.includes(`.${agentId}-message`)) {
            styleSheet.textContent += this.generateAgentCSS(agentId, config);
        }
    }

    /**
     * Detect agent from message content or metadata
     */
    detectAgentFromMessage(data) {
        // Check if agent is specified in metadata
        if (data.agent) {
            return data.agent;
        }
        
        // Try to detect from content patterns
        const content = data.content?.toLowerCase() || '';
        
        if (content.includes('orchestrator') || content.includes('routing to') || content.includes('workflow')) {
            return 'orchestrator';
        }
        if (content.includes('plot') && (content.includes('story') || content.includes('narrative'))) {
            return 'plot_generator';
        }
        if (content.includes('author') && (content.includes('profile') || content.includes('writer'))) {
            return 'author_generator';
        }
        if (content.includes('critique') || content.includes('analysis') || content.includes('feedback')) {
            return 'critique';
        }
        if (content.includes('enhancement') || content.includes('improvement') || content.includes('refine')) {
            return 'enhancement';
        }
        if (content.includes('score') || content.includes('rating') || content.includes('evaluation')) {
            return 'scoring';
        }
        if (content.includes('world') && content.includes('building')) {
            return 'world_building';
        }
        if (content.includes('character') && (content.includes('development') || content.includes('creation'))) {
            return 'characters';
        }
        if (content.includes('lore') && (content.includes('expansion') || content.includes('generation'))) {
            return 'loregen';
        }
        
        return 'system'; // Default fallback
    }

    /**
     * Create agent header element
     */
    createAgentHeader(config, status = '') {
        const header = document.createElement('div');
        header.className = 'agent-header';
        
        header.innerHTML = `
            <div class="agent-avatar-header" style="background: linear-gradient(135deg, ${config.colors[0]} 0%, ${config.colors[1]} 100%);">
                ${config.icon}
            </div>
            <div class="agent-info">
                <div class="agent-name">${config.name}</div>
                <div class="agent-role">${config.role}${status ? ' • ' + status : ''}</div>
            </div>
        `;
        
        return header;
    }

    /**
     * Check if message content indicates orchestrator workflow
     */
    isOrchestratorWorkflow(content) {
        return content.includes('routing to') || 
               content.includes('workflow') || 
               content.includes('orchestrator') ||
               content.includes('agents') ||
               content.includes('sequential') ||
               content.includes('improvement');
    }

    /**
     * Parse workflow information from orchestrator message
     */
    parseWorkflowFromContent(content) {
        const workflow = {
            type: 'unknown',
            steps: [],
            currentStep: 0
        };
        
        // Detect workflow type
        if (content.includes('plot_then_author')) {
            workflow.type = 'plot_then_author';
            workflow.steps = [
                { agent: 'plot_generator', name: 'Plot Generator', task: 'Create story narrative', icon: '📚' },
                { agent: 'author_generator', name: 'Author Generator', task: 'Match author profile', icon: '✍️' },
                { agent: 'database', name: 'Database', task: 'Save results', icon: '💾' }
            ];
        } else if (content.includes('author_then_plot')) {
            workflow.type = 'author_then_plot';
            workflow.steps = [
                { agent: 'author_generator', name: 'Author Generator', task: 'Create author profile', icon: '✍️' },
                { agent: 'plot_generator', name: 'Plot Generator', task: 'Create matching story', icon: '📚' },
                { agent: 'database', name: 'Database', task: 'Save results', icon: '💾' }
            ];
        } else if (content.includes('iterative_improvement')) {
            workflow.type = 'iterative_improvement';
            workflow.steps = [
                { agent: 'critique', name: 'Critique Agent', task: 'Analyze content', icon: '🔍' },
                { agent: 'enhancement', name: 'Enhancement Agent', task: 'Improve content', icon: '⚡' },
                { agent: 'scoring', name: 'Scoring Agent', task: 'Evaluate quality', icon: '📊' },
                { agent: 'iteration', name: 'Iteration Check', task: 'Continue or finish', icon: '🔄' }
            ];
        } else if (content.includes('plot_only')) {
            workflow.type = 'plot_only';
            workflow.steps = [
                { agent: 'plot_generator', name: 'Plot Generator', task: 'Create story narrative', icon: '📚' },
                { agent: 'database', name: 'Database', task: 'Save plot', icon: '💾' }
            ];
        } else if (content.includes('author_only')) {
            workflow.type = 'author_only';
            workflow.steps = [
                { agent: 'author_generator', name: 'Author Generator', task: 'Create author profile', icon: '✍️' },
                { agent: 'database', name: 'Database', task: 'Save author', icon: '💾' }
            ];
        } else if (content.includes('critique_only')) {
            workflow.type = 'critique_only';
            workflow.steps = [
                { agent: 'critique', name: 'Critique Agent', task: 'Analyze content', icon: '🔍' },
                { agent: 'database', name: 'Database', task: 'Save analysis', icon: '💾' }
            ];
        }
        
        return workflow;
    }

    /**
     * Create workflow visualization card
     */
    createWorkflowCard(workflow) {
        const workflowCard = document.createElement('div');
        workflowCard.className = 'workflow-card orchestrator-message';
        
        const stepsHTML = workflow.steps.map((step, index) => {
            let status = 'pending';
            if (index < workflow.currentStep) status = 'completed';
            if (index === workflow.currentStep) status = 'active';
            
            return `
                <div class="workflow-step ${status}">
                    <span>${step.icon} ${step.name}</span>
                    <span style="opacity: 0.7;">→ ${step.task}</span>
                </div>
            `;
        }).join('');
        
        workflowCard.innerHTML = `
            <div class="workflow-header">
                <span class="workflow-icon">🎭</span>
                <span class="workflow-title">Orchestrator Workflow: ${workflow.type.replace('_', ' ').toUpperCase()}</span>
            </div>
            <div class="workflow-plan">
                ${stepsHTML}
            </div>
        `;
        
        return workflowCard;
    }

    /**
     * Create iterative improvement cycle visualization
     */
    createImprovementCycle(round, target = '9.5/10', current = 'TBD') {
        const cycleCard = document.createElement('div');
        cycleCard.className = 'improvement-cycle';
        
        cycleCard.innerHTML = `
            <div class="cycle-header">
                <div class="cycle-round">🔄 Improvement Cycle ${round}</div>
                <div class="cycle-score">Target: ${target} | Current: ${current}</div>
            </div>
            <div class="cycle-progress">
                <div class="workflow-step active">
                    <span>🔍 Analyzing content quality...</span>
                </div>
            </div>
        `;
        
        return cycleCard;
    }

    /**
     * Update workflow step status
     */
    updateWorkflowStep(workflowCard, stepIndex, status) {
        const steps = workflowCard.querySelectorAll('.workflow-step');
        if (steps[stepIndex]) {
            steps[stepIndex].className = `workflow-step ${status}`;
        }
    }

    /**
     * Generate JSON preview for structured responses
     */
    generateJSONPreview(jsonData, agentId) {
        try {
            const preview = {};
            
            // Extract key fields for preview
            if (jsonData.title) preview.title = jsonData.title;
            if (jsonData.genre) preview.genre = jsonData.genre;
            if (jsonData.score) preview.score = jsonData.score;
            if (jsonData.summary) preview.summary = jsonData.summary.substring(0, 100) + '...';
            if (jsonData.name) preview.name = jsonData.name;
            if (jsonData.style) preview.style = jsonData.style;
            
            return JSON.stringify(preview, null, 2);
        } catch (error) {
            return JSON.stringify(jsonData, null, 2).substring(0, 200) + '...';
        }
    }

    /**
     * Create collapsible JSON display with programmatic event listeners
     */
    createCollapsibleJSON(jsonData, agentId) {
        const container = document.createElement('div');
        container.className = 'json-response';
        
        const preview = this.generateJSONPreview(jsonData, agentId);
        const fullJson = JSON.stringify(jsonData, null, 2);
        
        // Create elements programmatically for better control
        const previewDiv = document.createElement('div');
        previewDiv.className = 'json-preview';
        previewDiv.dataset.collapsed = 'true';
        
        const previewCode = document.createElement('pre');
        previewCode.innerHTML = `<code>${preview}</code>`;
        
        const showFullButton = document.createElement('button');
        showFullButton.className = 'json-toggle';
        showFullButton.textContent = '📋 Show Full Response';
        
        const fullDiv = document.createElement('div');
        fullDiv.className = 'json-full';
        fullDiv.style.display = 'none';
        
        const fullCode = document.createElement('pre');
        fullCode.innerHTML = `<code>${fullJson}</code>`;
        
        const showPreviewButton = document.createElement('button');
        showPreviewButton.className = 'json-toggle';
        showPreviewButton.textContent = '📋 Show Preview';
        
        // Assemble structure
        previewDiv.appendChild(previewCode);
        previewDiv.appendChild(showFullButton);
        fullDiv.appendChild(fullCode);
        fullDiv.appendChild(showPreviewButton);
        container.appendChild(previewDiv);
        container.appendChild(fullDiv);
        
        // Use UIManager-compatible event handling if available
        if (window.uiManager && window.uiManager.addEventListenerToElement) {
            window.uiManager.addEventListenerToElement(showFullButton, 'click', () => {
                this.toggleJSONDisplay(previewDiv, fullDiv, true);
            });
            
            window.uiManager.addEventListenerToElement(showPreviewButton, 'click', () => {
                this.toggleJSONDisplay(previewDiv, fullDiv, false);
            });
        } else {
            // Fallback to direct event listeners
            showFullButton.addEventListener('click', () => {
                this.toggleJSONDisplay(previewDiv, fullDiv, true);
            });
            
            showPreviewButton.addEventListener('click', () => {
                this.toggleJSONDisplay(previewDiv, fullDiv, false);
            });
        }
        
        return container;
    }
    
    /**
     * Toggle JSON display between preview and full view
     * @param {HTMLElement} previewDiv - Preview container
     * @param {HTMLElement} fullDiv - Full JSON container  
     * @param {boolean} showFull - Whether to show full view
     */
    toggleJSONDisplay(previewDiv, fullDiv, showFull) {
        if (showFull) {
            previewDiv.style.display = 'none';
            fullDiv.style.display = 'block';
            previewDiv.dataset.collapsed = 'false';
        } else {
            previewDiv.style.display = 'block';
            fullDiv.style.display = 'none';
            previewDiv.dataset.collapsed = 'true';
        }
    }
}

// Create singleton instance
const agentManager = new AgentManager();

// Export for ES6 modules and global access
if (typeof window !== 'undefined') {
    window.agentManager = agentManager;
}

