function showIncident(incidentId) {
    // Hide all frames
    document.querySelectorAll('.incident-frame').forEach(frame => {
        frame.style.display = 'none';
    });
    // Show the selected frame
    document.getElementById(incidentId).style.display = 'block';
}

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('open');
}

// Show the first incident by default
document.addEventListener('DOMContentLoaded', () => {
    showIncident('incident1');
});
