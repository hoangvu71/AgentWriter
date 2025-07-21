let ws = null;
            let sessionId = null;
            let userId = "user_" + Math.random().toString(36).substr(2, 9);
            
            // =====================================
            // DYNAMIC AGENT REGISTRY SYSTEM
            // =====================================
            
            // Core agent registry - can be extended dynamically
            const AGENT_REGISTRY = {
                orchestrator: {
                    name: "Orchestrator",
                    role: "Workflow Coordination", 
                    icon: "🎭",
                    colors: ["#667eea", "#764ba2"],
                    category: "system"
                },
                plot_generator: {
                    name: "Plot Generator",
                    role: "Story Creation",
                    icon: "📚", 
                    colors: ["#f093fb", "#f5576c"],
                    category: "content"
                },
                author_generator: {
                    name: "Author Generator",
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
                }
            };
            
            // Generate colors for unknown agents automatically
            function generateAgentColors(agentId) {
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
            
            // Get agent config with fallback for unknown agents
            function getAgentConfig(agentId) {
                if (AGENT_REGISTRY[agentId]) {
                    return AGENT_REGISTRY[agentId];
                }
                
                // Auto-generate config for unknown agents
                const colors = generateAgentColors(agentId);
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
            
            // Generate CSS for agent styling
            function generateAgentCSS(agentId, config) {
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
            
            // Initialize dynamic agent styles
            function initializeAgentStyles() {
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
                `;
                
                // Generate CSS for all known agents
                Object.keys(AGENT_REGISTRY).forEach(agentId => {
                    const config = AGENT_REGISTRY[agentId];
                    css += generateAgentCSS(agentId, config);
                });
                
                styleSheet.textContent = css;
                document.head.appendChild(styleSheet);
            }
            
            // Add new agent style dynamically
            function addAgentStyle(agentId) {
                const config = getAgentConfig(agentId);
                const styleSheet = document.getElementById('dynamic-agent-styles');
                if (styleSheet && !styleSheet.textContent.includes(`.${agentId}-message`)) {
                    styleSheet.textContent += generateAgentCSS(agentId, config);
                }
            }
            
            // Detect agent from message content or data
            function detectAgentFromMessage(data) {
                // Method 1: Explicit agent field from structured response
                if (data.agent) {
                    return data.agent;
                }
                
                // Method 2: Parse from content header patterns
                if (data.content) {
                    // Match patterns like "[AI] Plot Generator:" or "Plot Generator:"
                    const headerMatch = data.content.match(/(?:\[AI\]\s*)?([^:\n]+):/);
                    if (headerMatch) {
                        const agentName = headerMatch[1].trim();
                        // Convert "Plot Generator" to "plot_generator"
                        return agentName.toLowerCase().replace(/\s+/g, '_');
                    }
                    
                    // Match workflow patterns
                    if (data.content.includes('routing to') || data.content.includes('orchestrator')) {
                        return 'orchestrator';
                    }
                }
                
                return 'unknown_agent';
            }
            
            // Create agent header element
            function createAgentHeader(config, status = '') {
                const header = document.createElement('div');
                header.className = 'agent-header';
                
                header.innerHTML = `
                    <div class="agent-avatar-header" style="background: ${config.colors ? `linear-gradient(135deg, ${config.colors[0]} 0%, ${config.colors[1]} 100%)` : '#gray'}">
                        ${config.icon}
                    </div>
                    <div class="agent-info">
                        <span class="agent-name">${config.name}</span>
                        <span class="agent-role">${config.role}${status ? ' • ' + status : ''}</span>
                    </div>
                `;
                
                return header;
            }
            
            // =====================================
            // SMART JSON COLLAPSING SYSTEM
            // =====================================
            
            // Generate smart preview summaries from JSON data
            function generateJSONPreview(jsonData, agentId) {
                const config = getAgentConfig(agentId);
                const icon = config.icon;
                
                try {
                    switch (agentId) {
                        case 'plot_generator':
                            return `${icon} Plot: "${jsonData.title || 'Untitled'}" - ${inferGenreFromPlot(jsonData)}`;
                        
                        case 'author_generator':
                            const authorName = jsonData.author_name || 'Unknown Author';
                            const penName = jsonData.pen_name ? ` (${jsonData.pen_name})` : '';
                            return `${icon} Author: ${authorName}${penName}`;
                        
                        case 'critique':
                            const issues = jsonData.major_issues?.length || 0;
                            const strengths = jsonData.strengths?.length || 0;
                            return `${icon} Analysis: ${issues} issues, ${strengths} strengths identified`;
                        
                        case 'enhancement':
                            const improvements = Object.keys(jsonData).filter(key => 
                                key.includes('enhanced') || key.includes('improved')).length;
                            return `${icon} Enhancement: ${improvements} areas improved`;
                        
                        case 'scoring':
                            const score = jsonData.overall_score || jsonData.total_score || 'N/A';
                            const readiness = jsonData.publication_readiness || jsonData.readiness || 'Unknown';
                            return `${icon} Score: ${score}/10 - ${readiness}`;
                        
                        case 'orchestrator':
                            return `${icon} Workflow: ${Object.keys(jsonData).length} steps planned`;
                        
                        default:
                            const dataPoints = Object.keys(jsonData).length;
                            return `${icon} ${config.name}: ${dataPoints} data points generated`;
                    }
                } catch (error) {
                    return `${icon} ${config.name}: Data generated`;
                }
            }
            
            // Infer genre from plot data
            function inferGenreFromPlot(plotData) {
                if (plotData.genre) return plotData.genre;
                if (plotData.microgenre) return plotData.microgenre;
                if (plotData.subgenre) return plotData.subgenre;
                
                const plotText = (plotData.plot_summary || '').toLowerCase();
                if (plotText.includes('magic') || plotText.includes('fantasy')) return 'Fantasy';
                if (plotText.includes('space') || plotText.includes('future')) return 'Sci-Fi';
                if (plotText.includes('love') || plotText.includes('romance')) return 'Romance';
                if (plotText.includes('murder') || plotText.includes('mystery')) return 'Mystery';
                
                return 'Fiction';
            }
            
            // Create collapsible JSON element
            function createCollapsibleJSON(jsonData, agentId) {
                const preview = generateJSONPreview(jsonData, agentId);
                const jsonContainer = document.createElement('div');
                jsonContainer.className = 'json-response';
                
                jsonContainer.innerHTML = `
                    <div class="json-preview" onclick="toggleJSON(this)">
                        <span class="json-summary">${preview}</span>
                        <button class="json-toggle">
                            <span>📄</span>
                            <span class="toggle-text">View JSON</span>
                            <span class="toggle-arrow">▼</span>
                        </button>
                    </div>
                    <div class="json-content collapsed">
                        <pre>${JSON.stringify(jsonData, null, 2)}</pre>
                    </div>
                `;
                
                return jsonContainer;
            }
            
            // Toggle JSON visibility
            function toggleJSON(previewElement) {
                const jsonContent = previewElement.parentElement.querySelector('.json-content');
                const toggleText = previewElement.querySelector('.toggle-text');
                const toggleArrow = previewElement.querySelector('.toggle-arrow');
                
                const isCollapsed = jsonContent.classList.contains('collapsed');
                
                if (isCollapsed) {
                    jsonContent.classList.remove('collapsed');
                    toggleText.textContent = 'Hide JSON';
                    toggleArrow.textContent = '▲';
                } else {
                    jsonContent.classList.add('collapsed');
                    toggleText.textContent = 'View JSON';
                    toggleArrow.textContent = '▼';
                }
            }
            
            // =====================================
            // ORCHESTRATOR WORKFLOW VISUALIZATION
            // =====================================
            
            // Detect if message is orchestrator workflow information
            function isOrchestratorWorkflow(content) {
                return content.includes('routing to') || 
                       content.includes('workflow') || 
                       content.includes('orchestrator') ||
                       content.includes('agents') ||
                       content.includes('sequential') ||
                       content.includes('improvement');
            }
            
            // Parse workflow information from orchestrator message
            function parseWorkflowFromContent(content) {
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
            
            // Create workflow visualization card
            function createWorkflowCard(workflow) {
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
            
            // Create iterative improvement cycle visualization
            function createImprovementCycle(round, target = '9.5/10', current = 'TBD') {
                const cycleCard = document.createElement('div');
                cycleCard.className = 'improvement-cycle';
                
                cycleCard.innerHTML = `
                    <div class="cycle-header">
                        <span>⚡</span>
                        <span>Iterative Improvement - Round ${round}/4</span>
                    </div>
                    <div class="cycle-steps">
                        <div class="cycle-step active">🔍 Critique Agent → Analyzing content quality...</div>
                        <div class="cycle-step pending">⚡ Enhancement Agent → Waiting for critique...</div>
                        <div class="cycle-step pending">📊 Scoring Agent → Quality evaluation pending...</div>
                    </div>
                    <div class="cycle-progress">Target: ${target} | Current: ${current}</div>
                `;
                
                return cycleCard;
            }
            
            // Update workflow step status
            function updateWorkflowStep(workflowCard, stepIndex, status) {
                const steps = workflowCard.querySelectorAll('.workflow-step');
                if (steps[stepIndex]) {
                    steps[stepIndex].className = `workflow-step ${status}`;
                }
            }
            
            // =====================================
            // TESTS FOR AGENT SYSTEM
            // =====================================
            
            // TDD: Write tests first
            function runAgentSystemTests() {
                console.log('🧪 Running Agent System Tests...');
                
                // Test 1: Agent detection from various message formats
                const testMessages = [
                    { content: '[AI] Plot Generator: Creating story...', expected: 'plot_generator' },
                    { content: 'Author Generator: Building profile...', expected: 'author_generator' },
                    { agent: 'critique', expected: 'critique' },
                    { content: 'Orchestrator routing to plot_generator', expected: 'orchestrator' },
                    { content: 'Random message', expected: 'unknown_agent' }
                ];
                
                testMessages.forEach((test, i) => {
                    const result = detectAgentFromMessage(test);
                    const passed = result === test.expected;
                    console.log(`Test ${i + 1}: ${passed ? '✅' : '❌'} ${result} === ${test.expected}`);
                });
                
                // Test 2: Agent config retrieval
                const knownAgent = getAgentConfig('plot_generator');
                const unknownAgent = getAgentConfig('future_agent');
                
                console.log('✅ Known agent config:', knownAgent.name === 'Plot Generator');
                console.log('✅ Unknown agent config:', unknownAgent.name === 'Future Agent');
                
                // Test 3: Color generation consistency
                const colors1 = generateAgentColors('test_agent');
                const colors2 = generateAgentColors('test_agent');
                console.log('✅ Color consistency:', colors1[0] === colors2[0]);
                
                // Test 4: JSON Preview Generation
                const plotData = { title: "Test Plot", plot_summary: "A magical adventure..." };
                const authorData = { author_name: "John Doe", pen_name: "J.D." };
                const scoreData = { overall_score: 8.5, publication_readiness: "Ready" };
                
                const plotPreview = generateJSONPreview(plotData, 'plot_generator');
                const authorPreview = generateJSONPreview(authorData, 'author_generator');
                const scorePreview = generateJSONPreview(scoreData, 'scoring');
                
                console.log('✅ Plot preview:', plotPreview.includes('Test Plot'));
                console.log('✅ Author preview:', authorPreview.includes('John Doe'));
                console.log('✅ Score preview:', scorePreview.includes('8.5'));
                
                console.log('🧪 Agent System Tests Complete');
            }
            
            // Theme management
            function toggleTheme() {
                const html = document.documentElement;
                const currentTheme = html.getAttribute('data-theme');
                const newTheme = currentTheme === 'light' ? 'dark' : 'light';
                
                html.setAttribute('data-theme', newTheme);
                localStorage.setItem('theme', newTheme);
                
                // Update theme icon
                const themeIcon = document.getElementById('theme-icon');
                themeIcon.textContent = newTheme === 'light' ? '🌙' : '☀️';
            }

            // Initialize theme
            function initializeTheme() {
                const savedTheme = localStorage.getItem('theme') || 'light';
                document.documentElement.setAttribute('data-theme', savedTheme);
                
                const themeIcon = document.getElementById('theme-icon');
                themeIcon.textContent = savedTheme === 'light' ? '🌙' : '☀️';
            }

            function connect() {
                sessionId = "session_" + Math.random().toString(36).substr(2, 9);
                ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);
                
                ws.onopen = function(event) {
                    updateStatus('connected');
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    handleMessage(data);
                };
                
                ws.onclose = function(event) {
                    updateStatus('disconnected');
                };
                
                ws.onerror = function(event) {
                    console.error('WebSocket error:', event);
                    updateStatus('error');
                };
            }

            function updateStatus(status) {
                const indicator = document.getElementById('statusIndicator');
                const text = document.getElementById('statusText');
                
                indicator.className = `status-indicator ${status}`;
                
                switch(status) {
                    case 'connected':
                        text.textContent = 'Connected';
                        break;
                    case 'disconnected':
                        text.textContent = 'Disconnected';
                        break;
                    case 'error':
                        text.textContent = 'Connection Error';
                        break;
                }
            }
            
            function showTypingIndicator() {
                const chatContainer = document.getElementById('chat');
                
                // Remove existing typing indicator
                const existingIndicator = document.getElementById('typing-indicator');
                if (existingIndicator) {
                    existingIndicator.remove();
                }
                
                const messageWrapper = document.createElement('div');
                messageWrapper.className = 'message assistant';
                messageWrapper.id = 'typing-indicator';
                
                const avatar = document.createElement('div');
                avatar.className = 'message-avatar';
                avatar.textContent = 'AI';
                
                const typingContent = document.createElement('div');
                typingContent.className = 'typing-indicator';
                typingContent.innerHTML = `
                    <span>AI is thinking</span>
                    <div class="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                `;
                
                messageWrapper.appendChild(avatar);
                messageWrapper.appendChild(typingContent);
                chatContainer.appendChild(messageWrapper);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
            
            function hideTypingIndicator() {
                const indicator = document.getElementById('typing-indicator');
                if (indicator) {
                    indicator.remove();
                }
            }

            function handleMessage(data) {
                const chatContainer = document.getElementById('chat');
                
                if (data.type === 'stream_chunk') {
                    // Hide typing indicator when first chunk arrives
                    hideTypingIndicator();
                    
                    let currentMessage = document.getElementById('current-agent-message');
                    if (!currentMessage) {
                        // Detect agent from message content
                        const agentId = detectAgentFromMessage(data);
                        const agentConfig = getAgentConfig(agentId);
                        
                        // Ensure agent styling is available
                        addAgentStyle(agentId);
                        
                        // Check if this is an orchestrator workflow message
                        if (agentId === 'orchestrator' && isOrchestratorWorkflow(data.content)) {
                            const workflow = parseWorkflowFromContent(data.content);
                            const workflowCard = createWorkflowCard(workflow);
                            
                            const messageWrapper = document.createElement('div');
                            messageWrapper.className = `message assistant ${agentId}-message`;
                            messageWrapper.appendChild(workflowCard);
                            chatContainer.appendChild(messageWrapper);
                            
                            // Store workflow info for later updates
                            messageWrapper.dataset.workflowType = workflow.type;
                            messageWrapper.id = 'active-workflow';
                            
                            chatContainer.scrollTop = chatContainer.scrollHeight;
                            return; // Don't create regular message for workflow
                        }
                        
                        const messageWrapper = document.createElement('div');
                        messageWrapper.className = `message assistant ${agentId}-message`;
                        
                        // Create agent header instead of generic avatar
                        const agentHeader = createAgentHeader(agentConfig, 'Working...');
                        messageWrapper.appendChild(agentHeader);
                        
                        const avatar = document.createElement('div');
                        avatar.className = 'message-avatar';
                        avatar.textContent = agentConfig.icon;
                        
                        currentMessage = document.createElement('div');
                        currentMessage.className = 'message-content';
                        currentMessage.id = 'current-agent-message';
                        currentMessage.style.whiteSpace = 'pre-wrap';
                        
                        // Store timestamp and agent info for later use
                        currentMessage.dataset.timestamp = new Date().toISOString();
                        currentMessage.dataset.agentId = agentId;
                        
                        // AI: avatar first, then content (avatar on left)
                        messageWrapper.appendChild(avatar);
                        messageWrapper.appendChild(currentMessage);
                        chatContainer.appendChild(messageWrapper);
                    }
                    currentMessage.textContent += data.content;
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                } else if (data.type === 'structured_response') {
                    // Handle structured JSON responses with agent awareness
                    const agentId = data.agent || 'unknown_agent';
                    const agentConfig = getAgentConfig(agentId);
                    
                    // Ensure agent styling is available
                    addAgentStyle(agentId);
                    
                    // Special handling for orchestrator workflow responses
                    if (agentId === 'orchestrator' && data.json_data) {
                        // Check if this contains workflow information
                        const rawContent = data.raw_content || JSON.stringify(data.json_data);
                        if (isOrchestratorWorkflow(rawContent)) {
                            const workflow = parseWorkflowFromContent(rawContent);
                            const workflowCard = createWorkflowCard(workflow);
                            
                            const messageWrapper = document.createElement('div');
                            messageWrapper.className = `message assistant ${agentId}-message`;
                            messageWrapper.appendChild(workflowCard);
                            chatContainer.appendChild(messageWrapper);
                            
                            // Store workflow info for later updates
                            messageWrapper.dataset.workflowType = workflow.type;
                            messageWrapper.id = 'active-workflow';
                            
                            chatContainer.scrollTop = chatContainer.scrollHeight;
                            return; // Don't create regular JSON message for orchestrator workflow
                        }
                    }
                    
                    // Try to find existing agent message from stream_chunk to append JSON to
                    const existingMessages = document.querySelectorAll(`.${agentId}-message`);
                    let targetMessage = null;
                    
                    // Find the most recent message from this agent that doesn't already have JSON
                    for (let i = existingMessages.length - 1; i >= 0; i--) {
                        const msg = existingMessages[i];
                        if (!msg.querySelector('.json-response') && !msg.querySelector('.workflow-card')) {
                            targetMessage = msg;
                            break;
                        }
                    }
                    
                    if (targetMessage) {
                        // Append JSON to existing message instead of creating new one
                        const messageContent = targetMessage.querySelector('.message-content');
                        if (messageContent) {
                            // Create collapsible JSON
                            const collapsibleJSON = createCollapsibleJSON(data.json_data, agentId);
                            messageContent.appendChild(collapsibleJSON);
                            
                            // Update agent header status to show data is available
                            const agentHeader = targetMessage.querySelector('.agent-header');
                            if (agentHeader) {
                                const updatedHeader = createAgentHeader(agentConfig, 'Completed with Data');
                                targetMessage.replaceChild(updatedHeader, agentHeader);
                            }
                            
                            chatContainer.scrollTop = chatContainer.scrollHeight;
                            return; // Don't create new message
                        }
                    }
                    
                    // Fallback: Create new message if no existing message found
                    const messageWrapper = document.createElement('div');
                    messageWrapper.className = `message assistant ${agentId}-message`;
                    
                    // Create agent header
                    const agentHeader = createAgentHeader(agentConfig, 'Data Generated');
                    messageWrapper.appendChild(agentHeader);
                    
                    const avatar = document.createElement('div');
                    avatar.className = 'message-avatar';
                    avatar.textContent = agentConfig.icon;
                    
                    const structuredMessage = document.createElement('div');
                    structuredMessage.className = 'message-content';
                    
                    // Create collapsible JSON instead of raw dump
                    const collapsibleJSON = createCollapsibleJSON(data.json_data, agentId);
                    structuredMessage.appendChild(collapsibleJSON);
                    
                    // Add timestamp to structured response
                    const timestamp = document.createElement('div');
                    timestamp.className = 'message-timestamp';
                    timestamp.textContent = formatTimestamp(new Date());
                    structuredMessage.appendChild(timestamp);
                    
                    // No need to check for long messages - JSON is now collapsible
                    
                    // AI: avatar first, then content (avatar on left)
                    messageWrapper.appendChild(avatar);
                    messageWrapper.appendChild(structuredMessage);
                    chatContainer.appendChild(messageWrapper);
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                } else if (data.type === 'stream_end') {
                    const currentMessage = document.getElementById('current-agent-message');
                    if (currentMessage) {
                        const agentId = currentMessage.dataset.agentId;
                        const agentConfig = getAgentConfig(agentId);
                        
                        currentMessage.id = '';
                        // Format the final message
                        const messageText = currentMessage.textContent;
                        currentMessage.innerHTML = formatMessage(messageText);
                        
                        // Add timestamp to AI message
                        const timestamp = document.createElement('div');
                        timestamp.className = 'message-timestamp';
                        const messageTime = new Date(currentMessage.dataset.timestamp);
                        timestamp.textContent = formatTimestamp(messageTime);
                        currentMessage.appendChild(timestamp);
                        
                        // Update agent header status to complete
                        const messageWrapper = currentMessage.parentElement;
                        const existingHeader = messageWrapper.querySelector('.agent-header');
                        if (existingHeader) {
                            const updatedHeader = createAgentHeader(agentConfig, 'Completed');
                            messageWrapper.replaceChild(updatedHeader, existingHeader);
                        }
                        
                        // Check if message is too long
                        setTimeout(() => handleLongMessage(currentMessage), 100);
                    }
                    
                    // Log structured responses for debugging
                    if (data.structured_responses) {
                        console.log('Structured responses received:', data.structured_responses);
                    }
                } else if (data.type === 'error') {
                    const messageWrapper = document.createElement('div');
                    messageWrapper.className = 'message assistant';
                    
                    const avatar = document.createElement('div');
                    avatar.className = 'message-avatar';
                    avatar.textContent = '⚠️';
                    
                    const errorMessage = document.createElement('div');
                    errorMessage.className = 'message-content';
                    errorMessage.textContent = 'Error: ' + data.content;
                    errorMessage.style.backgroundColor = 'var(--bg-tertiary)';
                    errorMessage.style.color = '#ef4444';
                    errorMessage.style.border = '1px solid #ef4444';
                    
                    // Add timestamp to error message
                    const timestamp = document.createElement('div');
                    timestamp.className = 'message-timestamp';
                    timestamp.textContent = formatTimestamp(new Date());
                    errorMessage.appendChild(timestamp);
                    
                    // Check if error message is too long
                    setTimeout(() => handleLongMessage(errorMessage), 100);
                    
                    // AI: avatar first, then content (avatar on left)
                    messageWrapper.appendChild(avatar);
                    messageWrapper.appendChild(errorMessage);
                    chatContainer.appendChild(messageWrapper);
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
            }
            
            function formatTimestamp(date) {
                const now = new Date();
                const diff = now - date;
                const seconds = Math.floor(diff / 1000);
                const minutes = Math.floor(seconds / 60);
                const hours = Math.floor(minutes / 60);
                
                if (seconds < 60) {
                    return 'just now';
                } else if (minutes < 60) {
                    return `${minutes}m ago`;
                } else if (hours < 24) {
                    return `${hours}h ago`;
                } else {
                    return date.toLocaleDateString();
                }
            }

            function handleLongMessage(messageElement) {
                // Check if message content is too long
                const contentHeight = messageElement.scrollHeight;
                const visibleHeight = messageElement.clientHeight;
                
                if (contentHeight > visibleHeight) {
                    messageElement.classList.add('long-message');
                    
                    // Add click handler to expand/collapse
                    messageElement.addEventListener('click', function() {
                        if (messageElement.style.maxHeight === 'none') {
                            messageElement.style.maxHeight = '500px';
                            messageElement.classList.add('long-message');
                        } else {
                            messageElement.style.maxHeight = 'none';
                            messageElement.classList.remove('long-message');
                        }
                    });
                }
            }

            function formatMessage(text) {
                // Convert numbered lists to HTML
                text = text.replace(/^(\d+\.\s\*\*)(.+?)(\*\*)/gm, '<strong>$1$2</strong>');
                text = text.replace(/^(\d+\.\s)(.+?)$/gm, '<strong>$1</strong>$2');
                
                // Convert bold text
                text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                
                // Convert line breaks
                text = text.replace(/\n/g, '<br>');
                
                return text;
            }
            
            function sendMessage() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                
                if (message && ws && ws.readyState === WebSocket.OPEN) {
                    // Display user message
                    const chatContainer = document.getElementById('chat');
                    const messageWrapper = document.createElement('div');
                    messageWrapper.className = 'message user';
                    
                    const messageContent = document.createElement('div');
                    messageContent.className = 'message-content';
                    messageContent.textContent = message;
                    
                    // Add timestamp to user message
                    const timestamp = document.createElement('div');
                    timestamp.className = 'message-timestamp';
                    timestamp.textContent = formatTimestamp(new Date());
                    messageContent.appendChild(timestamp);
                    
                    // Check if message is too long
                    setTimeout(() => handleLongMessage(messageContent), 100);
                    
                    const avatar = document.createElement('div');
                    avatar.className = 'message-avatar';
                    avatar.textContent = 'You';
                    
                    // User: content first, then avatar (avatar on right)
                    messageWrapper.appendChild(messageContent);
                    messageWrapper.appendChild(avatar);
                    chatContainer.appendChild(messageWrapper);
                    
                    // Send to server
                    ws.send(JSON.stringify({
                        type: 'message',
                        content: message,
                        user_id: userId
                    }));
                    
                    // Show typing indicator
                    showTypingIndicator();
                    
                    input.value = '';
                    input.style.height = 'auto';
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
            }
            
            // Auto-resize textarea
            function autoResize(textarea) {
                textarea.style.height = 'auto';
                textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
            }
            
            // Enter key support (with Shift+Enter for new lines)
            document.getElementById('messageInput').addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
            
            // Auto-resize textarea on input
            document.getElementById('messageInput').addEventListener('input', function(e) {
                autoResize(e.target);
            });
            
            // Model management functions
            function loadModels() {
                fetch('/models')
                    .then(response => response.json())
                    .then(data => {
                        const select = document.getElementById('modelSelect');
                        select.innerHTML = '';
                        
                        Object.entries(data.available_models).forEach(([modelId, info]) => {
                            const option = document.createElement('option');
                            option.value = modelId;
                            option.textContent = info.name;
                            if (modelId === data.current_model) {
                                option.selected = true;
                            }
                            select.appendChild(option);
                        });
                        
                        updateModelInfo(data.current_model, data.available_models);
                    })
                    .catch(error => console.error('Error loading models:', error));
            }
            
            function updateModelInfo(modelId, models) {
                const info = models[modelId];
                if (info) {
                    document.getElementById('modelInfo').textContent = 
                        `${info.description} - Best for: ${info.best_for}`;
                }
            }
            
            function switchModel() {
                const select = document.getElementById('modelSelect');
                const modelId = select.value;
                
                fetch(`/models/${modelId}/switch`, { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            console.log('Model switched successfully');
                            loadModels(); // Refresh model info
                        } else {
                            console.error('Failed to switch model:', data.message);
                        }
                    })
                    .catch(error => console.error('Error switching model:', error));
            }
            
            // Parameter management
            let selectedGenre = null;
            let selectedSubgenre = null;
            let selectedMicrogenre = null;
            let selectedTrope = null;
            let selectedTone = null;
            let selectedAudience = null;
            let selectedContent = null;
            
            function toggleParameters() {
                const content = document.getElementById('parametersContent');
                const button = document.getElementById('toggleParams');
                
                if (content.style.display === 'none') {
                    content.style.display = 'block';
                    button.textContent = '▲';
                    button.classList.add('expanded');
                } else {
                    content.style.display = 'none';
                    button.textContent = '▼';
                    button.classList.remove('expanded');
                }
            }
            
            // Global data storage for hierarchical relationships
            let allGenres = [];
            let allSubgenres = [];
            let allMicrogenres = [];
            let allTropes = [];
            let allTones = [];
            let allAudiences = [];

            async function loadParameters() {
                try {
                    // Load all data from the complete hierarchy API
                    const genresResponse = await fetch('/api/genres');
                    if (genresResponse.ok) {
                        const data = await genresResponse.json();
                        
                        if (data.success) {
                            // Store all data globally
                            const result = data.data || {};
                            allGenres = result.genres || [];
                            allSubgenres = result.subgenres || [];
                            allMicrogenres = result.microgenres || [];
                            allTropes = result.tropes || [];
                            allTones = result.tones || [];
                            
                            console.log('Loaded genres:', allGenres.length);
                            console.log('Loaded subgenres:', allSubgenres.length);
                            
                            // Populate genre dropdown
                            populateGenreDropdown();
                            
                            // Build complete packages for easy selection
                            buildCompletePackages();
                        }
                    }
                    
                    // Load audiences separately
                    const audiencesResponse = await fetch('/api/target-audiences');
                    if (audiencesResponse.ok) {
                        const audiencesData = await audiencesResponse.json();
                        if (audiencesData.success && audiencesData.data) {
                            allAudiences = audiencesData.data;
                            console.log('Loaded audiences:', allAudiences.length);
                            populateAudienceDropdown();
                        }
                    }
                } catch (error) {
                    console.error('Error loading parameters:', error);
                }
            }
            
            function populateGenreDropdown() {
                const genreSelect = document.getElementById('genreSelect');
                genreSelect.innerHTML = '<option value="">Select Genre...</option>';
                
                allGenres.forEach(genre => {
                    // Skip genres with empty names
                    if (!genre.name || genre.name.trim() === '') {
                        return;
                    }
                    const option = document.createElement('option');
                    option.value = JSON.stringify(genre);
                    option.textContent = genre.name;
                    genreSelect.appendChild(option);
                });
            }
            
            function populateAudienceDropdown() {
                const audienceSelect = document.getElementById('audienceSelect');
                audienceSelect.innerHTML = '<option value="">Select Audience...</option>';
                
                allAudiences.forEach(audience => {
                    const option = document.createElement('option');
                    option.value = JSON.stringify(audience);
                    const ageGroup = audience.age_group || 'Unknown';
                    const gender = audience.gender || 'Any';
                    const orientation = audience.sexual_orientation || 'Any';
                    option.textContent = `${ageGroup} - ${gender} - ${orientation}`;
                    audienceSelect.appendChild(option);
                });
            }
            
            function buildCompletePackages() {
                const packageSelect = document.getElementById('completePackageSelect');
                packageSelect.innerHTML = '<option value="">Choose a Complete Genre Package...</option>';
                
                // Build packages for complete chains: Genre -> Subgenre -> Microgenre -> Trope -> Tone
                allTones.forEach(tone => {
                    if (tone.trope_id) {
                        const trope = allTropes.find(t => t.id === tone.trope_id);
                        if (trope && trope.microgenre_id) {
                            const microgenre = allMicrogenres.find(m => m.id === trope.microgenre_id);
                            if (microgenre && microgenre.subgenre_id) {
                                const subgenre = allSubgenres.find(s => s.id === microgenre.subgenre_id);
                                if (subgenre && subgenre.genre_id) {
                                    const genre = allGenres.find(g => g.id === subgenre.genre_id);
                                    if (genre) {
                                        // Create complete package
                                        const packageData = {
                                            genre, subgenre, microgenre, trope, tone
                                        };
                                        
                                        const option = document.createElement('option');
                                        option.value = JSON.stringify(packageData);
                                        option.textContent = `${genre.name} > ${subgenre.name} > ${microgenre.name} > ${trope.name} > ${tone.name}`;
                                        packageSelect.appendChild(option);
                                    }
                                }
                            }
                        }
                    }
                });
            }
            
            // Complete package selection
            function selectCompletePackage() {
                const packageSelect = document.getElementById('completePackageSelect');
                
                if (packageSelect.value) {
                    const packageData = JSON.parse(packageSelect.value);
                    
                    // Set all selections based on the complete package
                    selectedGenre = packageData.genre;
                    selectedSubgenre = packageData.subgenre;
                    selectedMicrogenre = packageData.microgenre;
                    selectedTrope = packageData.trope;
                    selectedTone = packageData.tone;
                    
                    // Update all dropdowns to reflect the selection
                    updateDropdownsFromSelection();
                    updateContext();
                } else {
                    // Clear all selections
                    clearAllSelections();
                }
            }
            
            function updateDropdownsFromSelection() {
                // Update genre dropdown
                const genreSelect = document.getElementById('genreSelect');
                if (selectedGenre) {
                    genreSelect.value = JSON.stringify(selectedGenre);
                    populateSubgenreDropdown();
                }
                
                // Update subgenre dropdown
                const subgenreSelect = document.getElementById('subgenreSelect');
                if (selectedSubgenre) {
                    subgenreSelect.value = JSON.stringify(selectedSubgenre);
                    populateMicrogenreDropdown();
                }
                
                // Update microgenre dropdown
                const microgenreSelect = document.getElementById('microgenreSelect');
                if (selectedMicrogenre) {
                    microgenreSelect.value = JSON.stringify(selectedMicrogenre);
                    populateTropeDropdown();
                }
                
                // Update trope dropdown
                const tropeSelect = document.getElementById('tropeSelect');
                if (selectedTrope) {
                    tropeSelect.value = JSON.stringify(selectedTrope);
                    populateToneDropdown();
                }
                
                // Update tone dropdown
                const toneSelect = document.getElementById('toneSelect');
                if (selectedTone) {
                    toneSelect.value = JSON.stringify(selectedTone);
                }
            }
            
            // Hierarchical genre selection functions
            function onGenreChange() {
                const genreSelect = document.getElementById('genreSelect');
                selectedGenre = genreSelect.value ? JSON.parse(genreSelect.value) : null;
                selectedSubgenre = null;
                selectedMicrogenre = null;
                selectedTrope = null;
                selectedTone = null;
                
                populateSubgenreDropdown();
                updateContext();
            }
            
            function onSubgenreChange() {
                const subgenreSelect = document.getElementById('subgenreSelect');
                selectedSubgenre = subgenreSelect.value ? JSON.parse(subgenreSelect.value) : null;
                selectedMicrogenre = null;
                selectedTrope = null;
                selectedTone = null;
                
                populateMicrogenreDropdown();
                updateContext();
            }
            
            function onMicrogenreChange() {
                const microgenreSelect = document.getElementById('microgenreSelect');
                selectedMicrogenre = microgenreSelect.value ? JSON.parse(microgenreSelect.value) : null;
                selectedTrope = null;
                selectedTone = null;
                
                populateTropeDropdown();
                updateContext();
            }
            
            function onTropeChange() {
                const tropeSelect = document.getElementById('tropeSelect');
                selectedTrope = tropeSelect.value ? JSON.parse(tropeSelect.value) : null;
                selectedTone = null;
                
                populateToneDropdown();
                updateContext();
            }
            
            // Population functions for hierarchical dropdowns
            function populateSubgenreDropdown() {
                const subgenreSelect = document.getElementById('subgenreSelect');
                subgenreSelect.innerHTML = '<option value="">Select Subgenre...</option>';
                
                if (selectedGenre) {
                    subgenreSelect.disabled = false;
                    const genreSubgenres = allSubgenres.filter(sub => sub.genre_id === selectedGenre.id);
                    genreSubgenres.forEach(subgenre => {
                        const option = document.createElement('option');
                        option.value = JSON.stringify(subgenre);
                        option.textContent = subgenre.name;
                        subgenreSelect.appendChild(option);
                    });
                } else {
                    subgenreSelect.disabled = true;
                }
                
                resetDownstreamDropdowns('microgenre');
            }
            
            function populateMicrogenreDropdown() {
                const microgenreSelect = document.getElementById('microgenreSelect');
                microgenreSelect.innerHTML = '<option value="">Select Microgenre...</option>';
                
                if (selectedSubgenre) {
                    microgenreSelect.disabled = false;
                    const subgenreMicrogenres = allMicrogenres.filter(micro => micro.subgenre_id === selectedSubgenre.id);
                    subgenreMicrogenres.forEach(microgenre => {
                        const option = document.createElement('option');
                        option.value = JSON.stringify(microgenre);
                        option.textContent = microgenre.name;
                        microgenreSelect.appendChild(option);
                    });
                } else {
                    microgenreSelect.disabled = true;
                }
                
                resetDownstreamDropdowns('trope');
            }
            
            function populateTropeDropdown() {
                const tropeSelect = document.getElementById('tropeSelect');
                tropeSelect.innerHTML = '<option value="">Select Trope...</option>';
                
                if (selectedMicrogenre) {
                    tropeSelect.disabled = false;
                    const microgenreTropes = allTropes.filter(trope => trope.microgenre_id === selectedMicrogenre.id);
                    microgenreTropes.forEach(trope => {
                        const option = document.createElement('option');
                        option.value = JSON.stringify(trope);
                        option.textContent = trope.name;
                        tropeSelect.appendChild(option);
                    });
                } else {
                    tropeSelect.disabled = true;
                }
                
                resetDownstreamDropdowns('tone');
            }
            
            function populateToneDropdown() {
                const toneSelect = document.getElementById('toneSelect');
                toneSelect.innerHTML = '<option value="">Select Tone...</option>';
                
                if (selectedTrope) {
                    toneSelect.disabled = false;
                    const tropeTones = allTones.filter(tone => tone.trope_id === selectedTrope.id);
                    tropeTones.forEach(tone => {
                        const option = document.createElement('option');
                        option.value = JSON.stringify(tone);
                        option.textContent = tone.name;
                        toneSelect.appendChild(option);
                    });
                } else {
                    toneSelect.disabled = true;
                }
            }
            
            function resetDownstreamDropdowns(startFrom) {
                const dropdowns = ['microgenre', 'trope', 'tone'];
                const startIndex = dropdowns.indexOf(startFrom);
                
                for (let i = startIndex; i < dropdowns.length; i++) {
                    const select = document.getElementById(dropdowns[i] + 'Select');
                    select.innerHTML = `<option value="">Select ${dropdowns[i].charAt(0).toUpperCase() + dropdowns[i].slice(1)}...</option>`;
                    select.disabled = true;
                }
            }
            
            function clearAllSelections() {
                selectedGenre = null;
                selectedSubgenre = null;
                selectedMicrogenre = null;
                selectedTrope = null;
                selectedTone = null;
                selectedAudience = null;
                
                // Reset all dropdowns
                document.getElementById('genreSelect').value = '';
                document.getElementById('completePackageSelect').value = '';
                populateSubgenreDropdown();
                updateContext();
            }
            
            function updateContext() {
                const microgenreSelect = document.getElementById('microgenreSelect');
                const tropeSelect = document.getElementById('tropeSelect');
                const toneSelect = document.getElementById('toneSelect');
                const audienceSelect = document.getElementById('audienceSelect');
                const selectedParamsDiv = document.getElementById('selectedParams');
                
                // Update all selections
                selectedMicrogenre = microgenreSelect.value ? JSON.parse(microgenreSelect.value) : null;
                selectedTrope = tropeSelect.value ? JSON.parse(tropeSelect.value) : null;
                selectedTone = toneSelect.value ? JSON.parse(toneSelect.value) : null;
                selectedAudience = audienceSelect.value ? JSON.parse(audienceSelect.value) : null;
                
                let paramsText = '';
                
                if (selectedGenre || selectedSubgenre || selectedMicrogenre || selectedTrope || selectedTone || selectedAudience || selectedContent) {
                    paramsText = '<strong>Selected Parameters:</strong><br>';
                    
                    // Selected content for improvement
                    if (selectedContent) {
                        paramsText += `<span style="background: #6f42c1; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 5px; font-size: 12px;">Content: ${selectedContent.type.toUpperCase()} - ${selectedContent.title}</span><br>`;
                    }
                    
                    // Genre hierarchy
                    if (selectedGenre) {
                        paramsText += `<span style="background: #007bff; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 5px; font-size: 12px;">Genre: ${selectedGenre.name}</span>`;
                    }
                    if (selectedSubgenre) {
                        paramsText += `<span style="background: #0056b3; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 5px; font-size: 12px;">Subgenre: ${selectedSubgenre.name}</span>`;
                    }
                    if (selectedMicrogenre) {
                        paramsText += `<span style="background: #003d82; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 5px; font-size: 12px;">Microgenre: ${selectedMicrogenre.name}</span>`;
                    }
                    
                    // Tropes and Tones
                    if (selectedTrope) {
                        paramsText += `<br><span style="background: #dc3545; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 5px; font-size: 12px;">Trope: ${selectedTrope.name} (${selectedTrope.category})</span>`;
                    }
                    if (selectedTone) {
                        paramsText += `<span style="background: #fd7e14; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 5px; font-size: 12px;">Tone: ${selectedTone.name}</span>`;
                    }
                    
                    // Target Audience
                    if (selectedAudience) {
                        paramsText += `<br><span style="background: #28a745; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 5px; font-size: 12px;">Audience: ${selectedAudience.age_group} - ${selectedAudience.gender} - ${selectedAudience.sexual_orientation}</span>`;
                    }
                    
                    // Add descriptions
                    if (selectedMicrogenre && selectedMicrogenre.description) {
                        paramsText += `<br><em style="font-size: 12px; color: #6c757d;">Microgenre: ${selectedMicrogenre.description}</em>`;
                    }
                    if (selectedTrope && selectedTrope.description) {
                        paramsText += `<br><em style="font-size: 12px; color: #6c757d;">Trope: ${selectedTrope.description}</em>`;
                    }
                    if (selectedTone && selectedTone.description) {
                        paramsText += `<br><em style="font-size: 12px; color: #6c757d;">Tone: ${selectedTone.description}</em>`;
                    }
                    // Target audience details are shown in the main tag above
                } else {
                    paramsText = '<em style="color: #6c757d;">No parameters selected. Select parameters above to automatically include them in your requests.</em>';
                }
                
                selectedParamsDiv.innerHTML = paramsText;
            }
            
            // Content selection functions
            async function loadContent() {
                try {
                    const response = await fetch('/api/content-selection');
                    const data = await response.json();
                    
                    if (data.success) {
                        const contentSelect = document.getElementById('contentSelect');
                        contentSelect.innerHTML = '<option value="">Select Content...</option>';
                        
                        data.data.content.forEach(item => {
                            const option = document.createElement('option');
                            const value = JSON.stringify({
                                id: item.id,
                                type: item.type,
                                title: item.title
                            });
                            option.value = value;
                            option.textContent = `${item.type.toUpperCase()}: ${item.title}`;
                            contentSelect.appendChild(option);
                        });
                    }
                } catch (error) {
                    console.error('Error loading content:', error);
                }
            }
            
            function onContentChange() {
                const contentSelect = document.getElementById('contentSelect');
                selectedContent = contentSelect.value ? JSON.parse(contentSelect.value) : null;
                updateContext();
            }
            
            function refreshContent() {
                loadContent();
            }
            
            function injectParametersIntoMessage(message) {
                // Always inject parameters if any are selected
                if (!selectedGenre && !selectedSubgenre && !selectedMicrogenre && !selectedTrope && !selectedTone && !selectedAudience && !selectedContent) {
                    return message;
                }
                
                let contextText = '\n\n========== DETAILED CONTENT SPECIFICATIONS ==========';
                contextText += '\nUse these detailed specifications to guide content creation:\n';
                
                // Selected content for improvement
                if (selectedContent) {
                    contextText += '\n--- SELECTED CONTENT FOR IMPROVEMENT ---';
                    contextText += `\nCONTENT_ID: ${selectedContent.id}`;
                    contextText += `\nCONTENT_TYPE: ${selectedContent.type}`;
                    contextText += `\nCONTENT_TITLE: ${selectedContent.title}`;
                    contextText += '\nNOTE: This content should be fetched from the database for iterative improvement.';
                }
                
                // Complete Genre Hierarchy with detailed descriptions
                if (selectedGenre || selectedSubgenre || selectedMicrogenre) {
                    contextText += '\n--- GENRE HIERARCHY ---';
                    
                    if (selectedGenre) {
                        contextText += `\nMAIN GENRE: ${selectedGenre.name}`;
                        if (selectedGenre.description) {
                            contextText += `\n  Description: ${selectedGenre.description}`;
                        }
                    }
                    
                    if (selectedSubgenre) {
                        contextText += `\nSUBGENRE: ${selectedSubgenre.name}`;
                        if (selectedSubgenre.description) {
                            contextText += `\n  Description: ${selectedSubgenre.description}`;
                        }
                    }
                    
                    if (selectedMicrogenre) {
                        contextText += `\nMICROGENRE: ${selectedMicrogenre.name}`;
                        if (selectedMicrogenre.description) {
                            contextText += `\n  Description: ${selectedMicrogenre.description}`;
                        }
                    }
                }
                
                // Story Elements
                if (selectedTrope || selectedTone) {
                    contextText += '\n\n--- STORY ELEMENTS ---';
                    
                    if (selectedTrope) {
                        contextText += `\nTROPE: ${selectedTrope.name}`;
                        if (selectedTrope.description) {
                            contextText += `\n  Description: ${selectedTrope.description}`;
                        }
                        contextText += '\n  IMPORTANT: Integrate this trope naturally into the story structure.';
                    }
                    
                    if (selectedTone) {
                        contextText += `\nTONE: ${selectedTone.name}`;
                        if (selectedTone.description) {
                            contextText += `\n  Description: ${selectedTone.description}`;
                        }
                        contextText += '\n  IMPORTANT: Maintain this tone consistently throughout the content.';
                    }
                }
                
                // Target Audience Analysis
                if (selectedAudience) {
                    contextText += '\n\n--- TARGET AUDIENCE ANALYSIS ---';
                    contextText += `\nAUDIENCE PROFILE:`;
                    contextText += `\n  Age Group: ${selectedAudience.age_group}`;
                    contextText += `\n  Gender: ${selectedAudience.gender}`;
                    contextText += `\n  Sexual Orientation: ${selectedAudience.sexual_orientation}`;
                    
                    // Target audience is defined by the three core demographic fields above
                    
                    contextText += '\n  IMPORTANT: Tailor content complexity, themes, and language to this specific audience.';
                }
                
                // Creative Guidelines
                contextText += '\n\n--- CREATIVE GUIDELINES ---';
                contextText += '\n• Follow the genre conventions while being original';
                contextText += '\n• Ensure all story elements work together cohesively';
                contextText += '\n• Consider the target audience in every creative decision';
                contextText += '\n• Maintain consistency with the specified tone throughout';
                if (selectedTrope) {
                    contextText += '\n• Weave the trope into the story naturally, avoiding clichés';
                }
                
                contextText += '\n========================================\n';
                
                return message + contextText;
            }
            
            // Override the sendMessage function to inject parameters
            const originalSendMessage = sendMessage;
            sendMessage = function() {
                const input = document.getElementById('messageInput');
                let message = input.value.trim();
                
                if (message && ws && ws.readyState === WebSocket.OPEN) {
                    // Display user message with proper structure
                    const chatContainer = document.getElementById('chat');
                    const messageWrapper = document.createElement('div');
                    messageWrapper.className = 'message user';
                    
                    const messageContent = document.createElement('div');
                    messageContent.className = 'message-content';
                    messageContent.textContent = input.value; // Show original message to user
                    
                    // Add timestamp to user message
                    const timestamp = document.createElement('div');
                    timestamp.className = 'message-timestamp';
                    timestamp.textContent = formatTimestamp(new Date());
                    messageContent.appendChild(timestamp);
                    
                    // Check if message is too long
                    setTimeout(() => handleLongMessage(messageContent), 100);
                    
                    const avatar = document.createElement('div');
                    avatar.className = 'message-avatar';
                    avatar.textContent = 'You';
                    
                    // User: content first, then avatar (avatar on right)
                    messageWrapper.appendChild(messageContent);
                    messageWrapper.appendChild(avatar);
                    chatContainer.appendChild(messageWrapper);
                    
                    // Inject parameters if referenced
                    message = injectParametersIntoMessage(message);
                    
                    // Send enhanced message to server
                    ws.send(JSON.stringify({
                        type: 'message',
                        content: message, // Send enhanced message with parameters
                        user_id: userId
                    }));
                    
                    // Show typing indicator
                    showTypingIndicator();
                    
                    input.value = '';
                    input.style.height = 'auto';
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
            }

            // Connect on page load
            window.onload = function() {
                initializeTheme();
                initializeAgentStyles();
                runAgentSystemTests(); // Run tests in development
                connect();
                loadModels();
                loadParameters();
                loadContent();
            };