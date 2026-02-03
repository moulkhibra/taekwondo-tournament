// Main JavaScript for Taekwondo Tournament Management System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Handle tournament type change in player form
    const tournamentSelect = document.getElementById('tournament_id');
    if (tournamentSelect) {
        tournamentSelect.addEventListener('change', handleTournamentChange);
        // Initial check
        handleTournamentChange.call(tournamentSelect);
    }

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

function handleTournamentChange() {
    const selectedOption = this.options[this.selectedIndex];
    const tournamentText = selectedOption.text;
    const weightField = document.getElementById('weightFieldContainer');
    const weightInput = document.getElementById('weight');

    if (tournamentText.toLowerCase().includes('kyourgi')) {
        weightField.style.display = 'block';
        weightInput.required = true;
    } else {
        weightField.style.display = 'none';
        weightInput.required = false;
        weightInput.value = '';
    }
}

// Confirmation dialogs for delete actions
function confirmDelete(message = 'Are you sure you want to delete this item?') {
    return confirm(message);
}

// Print functionality
function printTournament() {
    window.print();
}

// Export functionality
function exportTournament(format, tournamentId) {
    const url = `/export/tournament/${tournamentId}/${format}`;
    window.location.href = url;
}

// Filter functionality
function applyFilters() {
    const form = document.getElementById('filterForm');
    if (form) {
        form.submit();
    }
}

// Clear filters
function clearFilters(tournamentId) {
    window.location.href = `/tournament/${tournamentId}`;
}

// Add loading states to buttons
function addLoadingState(button, originalText) {
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> ' + originalText;
}

function removeLoadingState(button, originalText) {
    button.disabled = false;
    button.innerHTML = originalText;
}

// Form validation helpers
function validateAgeGroup(age) {
    if (age < 14) {
        return 'Age must be at least 14 for competition';
    }
    if (age > 80) {
        return 'Age cannot exceed 80';
    }
    return null;
}

function validateWeight(weight) {
    if (weight && (weight < 20 || weight > 150)) {
        return 'Weight must be between 20kg and 150kg';
    }
    return null;
}

// Enhanced form validation for player form
document.addEventListener('DOMContentLoaded', function() {
    const playerForm = document.querySelector('form[action*="/player"]');
    if (playerForm) {
        playerForm.addEventListener('submit', function(e) {
            const ageInput = document.getElementById('age');
            const weightInput = document.getElementById('weight');
            
            let hasError = false;
            
            // Validate age
            if (ageInput) {
                const ageError = validateAgeGroup(parseInt(ageInput.value));
                if (ageError) {
                    showError(ageInput, ageError);
                    hasError = true;
                } else {
                    clearError(ageInput);
                }
            }
            
            // Validate weight (only if required)
            if (weightInput && weightInput.required && !weightInput.value) {
                showError(weightInput, 'Weight is required for Kyourgi tournaments');
                hasError = true;
            } else if (weightInput && weightInput.value) {
                const weightError = validateWeight(parseFloat(weightInput.value));
                if (weightError) {
                    showError(weightInput, weightError);
                    hasError = true;
                } else {
                    clearError(weightInput);
                }
            }
            
            if (hasError) {
                e.preventDefault();
            }
        });
    }
});

function showError(input, message) {
    clearError(input);
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'text-danger mt-1';
    errorDiv.style.fontSize = '0.875em';
    errorDiv.textContent = message;
    
    input.classList.add('is-invalid');
    input.parentNode.appendChild(errorDiv);
}

function clearError(input) {
    input.classList.remove('is-invalid');
    const errorDiv = input.parentNode.querySelector('.text-danger');
    if (errorDiv) {
        errorDiv.remove();
    }
}

// Dynamic match visualization (for future enhancements)
function updateMatchVisualizations() {
    const matchBoxes = document.querySelectorAll('.match-box');
    matchBoxes.forEach(function(matchBox) {
        matchBox.addEventListener('click', function() {
            // Future: Show match details modal
            console.log('Match clicked:', this);
        });
    });
}