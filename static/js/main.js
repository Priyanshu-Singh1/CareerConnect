// CareerConnect main JavaScript helpers

document.addEventListener('DOMContentLoaded', function () {
    // 1. Auto dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });

    // 2. Toggle resume input on application form when "use profile resume" is checked
    const profileResumeCheckbox = document.getElementById('use_profile_resume');
    const customResumeInput = document.getElementById('custom_resume_input');
    const customResumeContainer = document.getElementById('custom_resume_container');

    if (profileResumeCheckbox && customResumeContainer) {
        function updateResumeVisibility() {
            if (profileResumeCheckbox.checked) {
                customResumeContainer.style.display = 'none';
                if (customResumeInput) customResumeInput.required = false;
            } else {
                customResumeContainer.style.display = 'block';
                if (customResumeInput) customResumeInput.required = true;
            }
        }
        profileResumeCheckbox.addEventListener('change', updateResumeVisibility);
        updateResumeVisibility();
    }

    // 3. Initialize Bootstrap Tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
