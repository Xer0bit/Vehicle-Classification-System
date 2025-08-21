// Main JavaScript for Image Classification Web UI

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the application
    initializeFileInput();
    setupImagePreview();
    setupFlashMessagesDismissal();
});

/**
 * Initialize file input functionality
 */
function initializeFileInput() {
    const fileInput = document.getElementById('image');
    const fileLabel = document.querySelector('.file-input-label');
    const fileText = document.querySelector('.file-input-text');
    
    if (!fileInput || !fileLabel || !fileText) return;
    
    // Update label when file is selected
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            // Update label text
            fileText.textContent = `Selected: ${file.name}`;
            fileLabel.style.borderColor = '#48bb78';
            fileLabel.style.background = '#f0fff4';
            
            // Show preview if it's an image
            showImagePreview(file);
            
            // Validate file
            validateFile(file);
        } else {
            resetFileInput();
        }
    });
    
    // Drag and drop functionality
    setupDragAndDrop(fileLabel, fileInput);
}

/**
 * Setup image preview functionality
 */
function setupImagePreview() {
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
 * Show image preview
 */
function showImagePreview(file) {
    const previewContainer = document.getElementById('previewContainer');
    const imagePreview = document.getElementById('imagePreview');
    const fileName = document.getElementById('fileName');
    
    if (!previewContainer || !imagePreview || !fileName) return;
    
    if (file && file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = function(e) {
            imagePreview.src = e.target.result;
            fileName.textContent = `File: ${file.name} (${formatFileSize(file.size)})`;
            previewContainer.style.display = 'block';
            
            // Smooth show animation
            previewContainer.style.opacity = '0';
            setTimeout(() => {
                previewContainer.style.transition = 'opacity 0.3s ease';
                previewContainer.style.opacity = '1';
            }, 10);
        };
        reader.readAsDataURL(file);
    }
}

/**
 * Validate uploaded file
 */
function validateFile(file) {
    const maxSize = 16 * 1024 * 1024; // 16MB
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif'];
    
    // Check file size
    if (file.size > maxSize) {
        showAlert('File too large. Maximum size is 16MB.', 'error');
        resetFileInput();
        return false;
    }
    
    // Check file type
    if (!allowedTypes.includes(file.type)) {
        showAlert('Invalid file type. Please upload PNG, JPG, JPEG, or GIF files.', 'error');
        resetFileInput();
        return false;
    }
    
    return true;
}

/**
 * Reset file input to default state
 */
function resetFileInput() {
    const fileText = document.querySelector('.file-input-text');
    const fileLabel = document.querySelector('.file-input-label');
    const previewContainer = document.getElementById('previewContainer');
    
    if (fileText) fileText.textContent = 'Choose Image File';
    if (fileLabel) {
        fileLabel.style.borderColor = '#cbd5e0';
        fileLabel.style.background = '#f7fafc';
    }
    if (previewContainer) previewContainer.style.display = 'none';
}

/**
 * Setup drag and drop functionality
 */
function setupDragAndDrop(dropZone, fileInput) {
    if (!dropZone || !fileInput) return;
    
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    // Highlight drop zone when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.style.borderColor = '#667eea';
            dropZone.style.background = '#edf2f7';
        }, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.style.borderColor = '#cbd5e0';
            dropZone.style.background = '#f7fafc';
        }, false);
    });
    
    // Handle dropped files
    dropZone.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            fileInput.files = files;
            // Trigger change event
            const event = new Event('change', { bubbles: true });
            fileInput.dispatchEvent(event);
        }
    }
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
}

/**
 * Setup flash messages dismissal
 */
function setupFlashMessagesDismissal() {
    const flashMessages = document.querySelectorAll('.flash');
    
    flashMessages.forEach(message => {
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (message.parentNode) {
                message.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                message.style.opacity = '0';
                message.style.transform = 'translateY(-10px)';
                
                setTimeout(() => {
                    if (message.parentNode) {
                        message.remove();
                    }
                }, 300);
            }
        }, 5000);
        
        // Add click to dismiss
        message.addEventListener('click', function() {
            message.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            message.style.opacity = '0';
            message.style.transform = 'translateY(-10px)';
            
            setTimeout(() => {
                if (message.parentNode) {
                    message.remove();
                }
            }, 300);
        });
        
        // Add hover effect
        message.style.cursor = 'pointer';
        message.title = 'Click to dismiss';
    });
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    // Create alert element
    const alert = document.createElement('div');
    alert.className = `flash flash-${type}`;
    alert.textContent = message;
    alert.style.cursor = 'pointer';
    alert.title = 'Click to dismiss';
    
    // Insert at top of container
    const container = document.querySelector('.container');
    if (container) {
        const firstChild = container.firstChild;
        container.insertBefore(alert, firstChild);
        
        // Setup dismissal
        alert.addEventListener('click', function() {
            alert.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.remove();
                }
            }, 300);
        });
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.click();
            }
        }, 5000);
    }
}

/**
 * Format file size in human readable format
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.select();
        element.setSelectionRange(0, 99999); // For mobile devices
        
        try {
            document.execCommand('copy');
            showAlert('Copied to clipboard!', 'success');
        } catch (err) {
            showAlert('Failed to copy to clipboard', 'error');
        }
        
        // Deselect
        window.getSelection().removeAllRanges();
    }
}

/**
 * Toggle password visibility
 */
function togglePassword(elementId) {
    const element = document.getElementById(elementId);
    const button = element.nextElementSibling;
    
    if (element.type === 'password') {
        element.type = 'text';
        button.textContent = 'Hide';
    } else {
        element.type = 'password';
        button.textContent = 'Show';
    }
}

/**
 * Add loading state to button
 */
function addLoadingState(button, originalText) {
    button.disabled = true;
    button.innerHTML = `<span class="loading">⏳</span> Processing...`;
    button.style.cursor = 'not-allowed';
}

/**
 * Remove loading state from button
 */
function removeLoadingState(button, originalText) {
    button.disabled = false;
    button.innerHTML = originalText;
    button.style.cursor = 'pointer';
}

/**
 * Smooth scroll to element
 */
function smoothScrollTo(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// Export functions for global use
window.copyToClipboard = copyToClipboard;
window.togglePassword = togglePassword;
window.showAlert = showAlert;
window.addLoadingState = addLoadingState;
window.removeLoadingState = removeLoadingState;
window.smoothScrollTo = smoothScrollTo;
