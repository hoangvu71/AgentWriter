// Chat WebSocket and UI functionality
let ws = null;
let sessionId = null;
let userId = "user_" + Math.random().toString(36).substr(2, 9);

function connect() {
    sessionId = "session_" + Math.random().toString(36).substr(2, 9);
    ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);
    
    ws.onopen = function(event) {
        document.getElementById('status').textContent = 'Connected';
        document.getElementById('status').className = 'status connected';
    };
    
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        handleMessage(data);
    };
    
    ws.onclose = function(event) {
        document.getElementById('status').textContent = 'Disconnected';
        document.getElementById('status').className = 'status disconnected';
    };
    
    ws.onerror = function(event) {
        console.error('WebSocket error:', event);
    };
}

function handleMessage(data) {
    const chatContainer = document.getElementById('chat');
    
    if (data.type === 'stream_chunk') {
        let currentMessage = document.getElementById('current-agent-message');
        if (!currentMessage) {
            currentMessage = document.createElement('div');
            currentMessage.className = 'message agent-message';
            currentMessage.id = 'current-agent-message';
            currentMessage.style.whiteSpace = 'pre-wrap';
            chatContainer.appendChild(currentMessage);
        }
        currentMessage.textContent += data.content;
        chatContainer.scrollTop = chatContainer.scrollHeight;
    } else if (data.type === 'structured_response') {
        // Handle structured JSON responses
        const structuredMessage = document.createElement('div');
        structuredMessage.className = 'message agent-message structured-response';
        structuredMessage.style.border = '2px solid #007bff';
        structuredMessage.style.borderRadius = '8px';
        structuredMessage.style.padding = '15px';
        structuredMessage.style.backgroundColor = '#f8f9fa';
        
        // Add agent name header
        const agentHeader = document.createElement('h4');
        agentHeader.textContent = `[DATA] ${data.agent.replace('_', ' ').toUpperCase()} - Structured Response`;
        agentHeader.style.color = '#007bff';
        agentHeader.style.marginBottom = '10px';
        structuredMessage.appendChild(agentHeader);
        
        // Add JSON data as formatted text
        const jsonContent = document.createElement('pre');
        jsonContent.style.backgroundColor = '#ffffff';
        jsonContent.style.border = '1px solid #ddd';
        jsonContent.style.borderRadius = '4px';
        jsonContent.style.padding = '10px';
        jsonContent.style.overflow = 'auto';
        jsonContent.style.fontSize = '12px';
        jsonContent.textContent = JSON.stringify(data.json_data, null, 2);
        structuredMessage.appendChild(jsonContent);
        
        chatContainer.appendChild(structuredMessage);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    } else if (data.type === 'stream_end') {
        const currentMessage = document.getElementById('current-agent-message');
        if (currentMessage) {
            currentMessage.id = '';
            // Format the final message
            currentMessage.innerHTML = formatMessage(currentMessage.textContent);
        }
        
        // Log structured responses for debugging
        if (data.structured_responses) {
            console.log('Structured responses received:', data.structured_responses);
        }
    } else if (data.type === 'error') {
        const errorMessage = document.createElement('div');
        errorMessage.className = 'message agent-message';
        errorMessage.textContent = 'Error: ' + data.content;
        errorMessage.style.backgroundColor = '#f8d7da';
        errorMessage.style.color = '#721c24';
        chatContainer.appendChild(errorMessage);
        chatContainer.scrollTop = chatContainer.scrollHeight;
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
    let message = input.value.trim();
    
    if (message) {
        // Display user message (clean original message)
        const chatContainer = document.getElementById('chat');
        const userMessage = document.createElement('div');
        userMessage.className = 'message user-message';
        userMessage.textContent = message; // Show clean user message
        chatContainer.appendChild(userMessage);
        
        // Build structured context instead of text injection
        const contextObject = buildContextObject();
        const messagePayload = {
            type: 'message',
            content: message,  // Clean user message only
            user_id: userId
        };
        
        // Add structured context if parameters are selected
        if (contextObject) {
            messagePayload.context = contextObject;
        }
        
        // Send message with structured context
        ws.send(JSON.stringify(messagePayload));
        
        input.value = '';
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

// Enter key support
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('messageInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
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
    } else {
        content.style.display = 'none';
        button.textContent = '▼';
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
                allGenres = data.genres || [];
                allSubgenres = data.subgenres || [];
                allMicrogenres = data.microgenres || [];
                allTropes = data.tropes || [];
                allTones = data.tones || [];
                
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
            if (audiencesData.success && audiencesData.audiences) {
                allAudiences = audiencesData.audiences;
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
        option.textContent = `${audience.age_group} - ${audience.gender} - ${audience.sexual_orientation}`;
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
            
            data.content.forEach(item => {
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

/**
 * Build structured context object from selected parameters.
 * Matches the implementation in main.js for consistency.
 */
function buildContextObject() {
    // Check if any parameters are selected
    if (!selectedGenre && !selectedSubgenre && !selectedMicrogenre && 
        !selectedTrope && !selectedTone && !selectedAudience && !selectedContent) {
        return null;
    }
    
    const context = {};
    
    // Content selection for improvement
    if (selectedContent) {
        context.content_selection = {
            id: selectedContent.id,
            type: selectedContent.type,
            title: selectedContent.title
        };
    }
    
    // Genre hierarchy - structured instead of verbose text
    const genreHierarchy = {};
    if (selectedGenre) {
        genreHierarchy.genre = {
            id: selectedGenre.id,
            name: selectedGenre.name,
            description: selectedGenre.description
        };
    }
    if (selectedSubgenre) {
        genreHierarchy.subgenre = {
            id: selectedSubgenre.id,
            name: selectedSubgenre.name,
            description: selectedSubgenre.description
        };
    }
    if (selectedMicrogenre) {
        genreHierarchy.microgenre = {
            id: selectedMicrogenre.id,
            name: selectedMicrogenre.name,
            description: selectedMicrogenre.description
        };
    }
    if (Object.keys(genreHierarchy).length > 0) {
        context.genre_hierarchy = genreHierarchy;
    }
    
    // Story elements - structured instead of verbose text
    const storyElements = {};
    if (selectedTrope) {
        storyElements.trope = {
            id: selectedTrope.id,
            name: selectedTrope.name,
            description: selectedTrope.description
        };
    }
    if (selectedTone) {
        storyElements.tone = {
            id: selectedTone.id,
            name: selectedTone.name,
            description: selectedTone.description
        };
    }
    if (Object.keys(storyElements).length > 0) {
        context.story_elements = storyElements;
    }
    
    // Target audience - clean structure instead of verbose analysis
    if (selectedAudience) {
        context.target_audience = {
            age_group: selectedAudience.age_group,
            gender: selectedAudience.gender,
            sexual_orientation: selectedAudience.sexual_orientation
        };
    }
    
    return Object.keys(context).length > 0 ? context : null;
}

// Connect on page load
window.onload = function() {
    connect();
    loadModels();
    loadParameters();
    loadContent();
};