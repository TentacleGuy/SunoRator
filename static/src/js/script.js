/*AJAX Content*/
document.addEventListener('DOMContentLoaded', function() {
    const links = document.querySelectorAll('a[data-ajax="true"]');
    
    links.forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault();
            const url = this.getAttribute('href');
            
            fetch(url)
                .then(response => response.text())
                .then(html => {
                    document.getElementById('main-content').innerHTML = html;
                })
                .catch(error => console.error('Error loading content:', error));
                console.log(url);
        });
    });
});
/*logging*/
const socket = io();

socket.on('log_update', function(msg) {
    const terminalOutput = document.getElementById('terminal-output');
    terminalOutput.textContent = msg.data;
    terminalOutput.scrollTop = terminalOutput.scrollHeight; // Auto-scroll to the bottom
});