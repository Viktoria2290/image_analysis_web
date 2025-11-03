// Utility functions for the web interface

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Get file type icon
function getFileIcon(fileType) {
    const icons = {
        'image': 'fa-image',
        'pdf': 'fa-file-pdf',
        'text': 'fa-file-alt',
        'other': 'fa-file'
    };
    return icons[fileType] || 'fa-file';
}

// Get file type text
function getTypeText(fileType) {
    const types = {
        'image': 'Изображение',
        'pdf': 'PDF',
        'text': 'Текст',
        'other': 'Файл'
    };
    return types[fileType] || fileType;
}

// Get status text
function getStatusText(status) {
    const statusTexts = {
        'uploaded': 'Загружено',
        'processing': 'Обработка',
        'completed': 'Завершено',
        'failed': 'Ошибка'
    };
    return statusTexts[status] || status;
}

// Get CSRF token
function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

// Show notification message
function showNotification(message, type = 'info') {
    const container = document.createElement('div');
    container.className = `notification notification-${type}`;
    container.innerHTML = `
        <div class="notification-content">
            <span class="notification-message">${message}</span>
            <button class="notification-close">&times;</button>
        </div>
    `;

    document.body.appendChild(container);

    // Add styles if not already added
    if (!document.querySelector('#notification-styles')) {
        const styles = document.createElement('style');
        styles.id = 'notification-styles';
        styles.textContent = `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                animation: slideIn 0.3s ease;
            }

            .notification-content {
                background: white;
                padding: 1rem 1.5rem;
                border-radius: 8px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                display: flex;
                align-items: center;
                gap: 1rem;
                min-width: 300px;
            }

            .notification-info .notification-content {
                border-left: 4px solid #3498db;
            }

            .notification-success .notification-content {
                border-left: 4px solid #27ae60;
            }

            .notification-error .notification-content {
                border-left: 4px solid #e74c3c;
            }

            .notification-warning .notification-content {
                border-left: 4px solid #f39c12;
            }

            .notification-close {
                background: none;
                border: none;
                font-size: 1.2rem;
                cursor: pointer;
                color: #7f8c8d;
            }

            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(styles);
    }

    // Auto remove after 5 seconds
    setTimeout(() => {
        container.remove();
    }, 5000);

    // Close button
    container.querySelector('.notification-close').addEventListener('click', () => {
        container.remove();
    });
}

// Debounce function for search inputs
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Check if user is authenticated
function isAuthenticated() {
    return document.querySelector('[data-user-authenticated]') !== null;
}

// Get user data from data attributes
function getUserData() {
    const element = document.querySelector('[data-user-data]');
    return element ? JSON.parse(element.dataset.userData) : null;
}

// API error handler
function handleApiError(error) {
    console.error('API Error:', error);
    showNotification('Произошла ошибка при загрузке данных', 'error');
}

// Initialize tooltips
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(e) {
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = e.target.dataset.tooltip;
    document.body.appendChild(tooltip);

    const rect = e.target.getBoundingClientRect();
    tooltip.style.left = rect.left + rect.width / 2 - tooltip.offsetWidth / 2 + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
}

function hideTooltip() {
    const tooltip = document.querySelector('.tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initTooltips();

    // Add loading states to buttons
    document.addEventListener('click', function(e) {
        if (e.target.matches('button[data-loading]')) {
            const button = e.target;
            const originalText = button.innerHTML;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Загрузка...';
            button.disabled = true;

            // Restore button after 5 seconds (fallback)
            setTimeout(() => {
                button.innerHTML = originalText;
                button.disabled = false;
            }, 5000);
        }
    });
});