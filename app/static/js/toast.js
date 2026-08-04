function showToast(message, category = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${category}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}