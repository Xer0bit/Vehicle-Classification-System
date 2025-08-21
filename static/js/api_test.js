// API Testing JavaScript for Image Classification Web UI

document.addEventListener('DOMContentLoaded', function() {
    // Initialize API testing functionality
    initializeApiTester();
    setupFormSubmission();
    setupTabs();
});

/**
 * Initialize API testing components
 */
function initializeApiTester() {
    // Show initial API key
    updateApiKey();
    
    // Setup file input for API testing
    const apiImageInput = document.getElementById('apiImage');
    if (apiImageInput) {
        apiImageInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const fileText = document.querySelector('#apiImage + label .file-input-text');
                if (fileText) {
                    fileText.textContent = `Selected: ${file.name}`;
                }
            }
        });
    }
}

/**
 * Update API key display
 */
function updateApiKey() {
    const apiKeyElement = document.getElementById('apiKey');
    if (!apiKeyElement) return;
    
    const apiKey = apiKeyElement.value;
    
    // Update header field
    const headerApiKeyElement = document.getElementById('headerApiKey');
    if (headerApiKeyElement) {
        headerApiKeyElement.value = apiKey;
    }
    
    // Generate cURL command
    generateCurlCommand(apiKey);
}

/**
 * Test health endpoint
 */
async function testHealth() {
    const url = '/api/health';
    const startTime = Date.now();
    
    try {
        showOutput('Testing health endpoint...', 'response');
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const endTime = Date.now();
        const responseTime = endTime - startTime;
        
        const data = await response.json();
        
        const output = {
            status: response.status,
            statusText: response.statusText,
            responseTime: `${responseTime}ms`,
            data: data
        };
        
        showOutput(JSON.stringify(output, null, 2), 'response');
        showHeaders(response.headers, 'headers');
        
        const curlCmd = `curl -X GET "${window.location.origin}${url}" \\
  -H "Content-Type: application/json"`;
        showOutput(curlCmd, 'curl');
        
    } catch (error) {
        showOutput(`Error: ${error.message}`, 'response');
    }
}

/**
 * Test CORS endpoint
 */
async function testCors() {
    const url = '/api/test-cors';
    const startTime = Date.now();
    
    try {
        showOutput('Testing CORS endpoint...', 'response');
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const endTime = Date.now();
        const responseTime = endTime - startTime;
        
        const data = await response.json();
        
        const output = {
            status: response.status,
            statusText: response.statusText,
            responseTime: `${responseTime}ms`,
            corsHeaders: {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods')
            },
            data: data
        };
        
        showOutput(JSON.stringify(output, null, 2), 'response');
        showHeaders(response.headers, 'headers');
        
        const curlCmd = `curl -X GET "${window.location.origin}${url}" \\
  -H "Content-Type: application/json"`;
        showOutput(curlCmd, 'curl');
        
    } catch (error) {
        showOutput(`Error: ${error.message}`, 'response');
    }
}

/**
 * Setup form submission for API classification test
 */
function setupFormSubmission() {
    const form = document.getElementById('apiTestForm');
    if (!form) return;
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const fileInput = document.getElementById('apiImage');
        const file = fileInput.files[0];
        
        if (!file) {
            showAlert('Please select an image file first.', 'error');
            return;
        }
        
        // Show loading state
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        addLoadingState(submitBtn, originalText);
        
        try {
            await testClassificationApi(file);
        } finally {
            removeLoadingState(submitBtn, originalText);
        }
    });
}

/**
 * Test classification API endpoint
 */
async function testClassificationApi(file) {
    const url = '/api/classify';
    const startTime = Date.now();
    
    try {
        showOutput('Testing classification endpoint...', 'response');
        
        // Get API key
        const apiKey = document.getElementById('headerApiKey').value;
        
        // Create form data
        const formData = new FormData();
        formData.append('image', file);
        
        // Make request
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-API-Key': apiKey
            },
            body: formData
        });
        
        const endTime = Date.now();
        const responseTime = endTime - startTime;
        
        const data = await response.json();
        
        const output = {
            status: response.status,
            statusText: response.statusText,
            responseTime: `${responseTime}ms`,
            requestHeaders: {
                'X-API-Key': apiKey
            },
            data: data
        };
        
        showOutput(JSON.stringify(output, null, 2), 'response');
        showHeaders(response.headers, 'headers');
        
        // Generate cURL command
        const curlCmd = `curl -X POST "${window.location.origin}${url}" \\
  -H "X-API-Key: ${apiKey}" \\
  -F "image=@${file.name}"`;
        showOutput(curlCmd, 'curl');
        
        // Show success message if classification was successful
        if (response.ok && data.success) {
            showAlert(`Classification successful! Predicted: ${data.class_name} (${(data.confidence * 100).toFixed(2)}%)`, 'success');
        }
        
    } catch (error) {
        showOutput(`Error: ${error.message}`, 'response');
        showAlert(`API test failed: ${error.message}`, 'error');
    }
}

/**
 * Generate cURL command
 */
function generateCurlCommand(apiKey) {
    const curlCmd = `# Classification API Test
curl -X POST "${window.location.origin}/api/classify" \\
  -H "X-API-Key: ${apiKey}" \\
  -F "image=@your_image_file.jpg"

# Health Check (no auth required)
curl -X GET "${window.location.origin}/api/health"

# CORS Test (no auth required)
curl -X GET "${window.location.origin}/api/test-cors"`;
    
    showOutput(curlCmd, 'curl');
}

/**
 * Setup tab functionality
 */
function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetTab = this.textContent.toLowerCase().replace(' ', '');
            showTab(targetTab);
        });
    });
}

/**
 * Show specific tab
 */
function showTab(tabName) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => {
        content.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(button => {
        button.classList.remove('active');
    });
    
    // Show target tab content
    const targetContent = document.getElementById(tabName + 'Tab');
    if (targetContent) {
        targetContent.classList.add('active');
    }
    
    // Add active class to corresponding button
    const targetButton = Array.from(tabButtons).find(button => 
        button.textContent.toLowerCase().replace(' ', '') === tabName
    );
    if (targetButton) {
        targetButton.classList.add('active');
    }
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    // Create alert container if it doesn't exist
    let alertContainer = document.querySelector('.alert-container');
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.className = 'alert-container';
        document.body.appendChild(alertContainer);
    }

    // Create alert element
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;

    // Add alert to container
    alertContainer.appendChild(alert);

    // Remove alert after 3 seconds
    setTimeout(() => {
        alert.remove();
        if (alertContainer.children.length === 0) {
            alertContainer.remove();
        }
    }, 3000);
}

/**
 * Show output in specific tab
 */
function showOutput(content, tabType) {
    const outputElement = document.getElementById(tabType + 'Output');
    if (outputElement) {
        outputElement.textContent = content;
    }
    
    // Auto-switch to the tab with new content
    showTab(tabType);
}

/**
 * Show response headers
 */
function showHeaders(headers, tabType) {
    let headerText = '';
    
    // Convert Headers object to readable format
    if (headers.forEach) {
        headers.forEach((value, key) => {
            headerText += `${key}: ${value}\n`;
        });
    } else {
        headerText = 'Headers not available';
    }
    
    showOutput(headerText, tabType);
}

/**
 * Add loading state to a button
 */
function addLoadingState(button, originalText) {
    button.disabled = true;
    button.innerHTML = 'Processing...';
}

/**
 * Remove loading state from a button
 */
function removeLoadingState(button, originalText) {
    button.disabled = false;
    button.innerHTML = originalText;
}

/**
 * Copy API key to clipboard
 */
function copyApiCredentials() {
    const apiKey = document.getElementById('apiKey').value;
    
    const credentials = `API_KEY=${apiKey}`;
    
    navigator.clipboard.writeText(credentials).then(() => {
        showAlert('API key copied to clipboard!', 'success');
    }).catch(() => {
        showAlert('Failed to copy API key', 'error');
    });
}

/**
 * Export test results
 */
function exportTestResults() {
    const responseOutput = document.getElementById('responseOutput').textContent;
    const headersOutput = document.getElementById('headersOutput').textContent;
    const curlOutput = document.getElementById('curlOutput').textContent;
    
    const exportData = {
        timestamp: new Date().toISOString(),
        response: responseOutput,
        headers: headersOutput,
        curl: curlOutput
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `api_test_results_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showAlert('Test results exported successfully!', 'success');
}

// Make functions globally available
window.testHealth = testHealth;
window.testCors = testCors;
window.updateApiKey = updateApiKey;
window.showTab = showTab;
window.copyApiCredentials = copyApiCredentials;
window.exportTestResults = exportTestResults;
window.addLoadingState = addLoadingState;
window.removeLoadingState = removeLoadingState;
window.showAlert = showAlert;
