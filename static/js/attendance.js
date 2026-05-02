// Clean Attendance JS - No Errors
(function() {
    'use strict';
    
    document.addEventListener('DOMContentLoaded', initAttendancePage);
    
    function initAttendancePage() {
        const startBtn = document.getElementById('startAttendanceBtn');
        const stopBtn = document.getElementById('stopAttendanceBtn');
        const videoFeed = document.getElementById('videoFeed');
        const statusBadge = document.getElementById('statusBadge');
        const messageDiv = document.getElementById('attendanceMessage');
        const markedList = document.getElementById('markedList');
        const markedCount = document.getElementById('markedCount');
        const subjectSelect = document.getElementById('subjectSelect');
        const loadingDiv = document.getElementById('attendanceLoading');
        
        let pollTimer = null;
        
        startBtn.addEventListener('click', startAttendance);
        stopBtn.addEventListener('click', stopAttendance);
        
        function startAttendance() {
            const subject = subjectSelect.value.trim();
            if (!subject) {
                showMessage('Please select a subject first', 'warning');
                return;
            }
            
            // UI state
            startBtn.classList.add('d-none');
            stopBtn.classList.remove('d-none');
            statusBadge.textContent = 'Live';
            statusBadge.className = 'badge bg-success';
            loadingDiv.classList.remove('d-none');
            
            showMessage('Live attendance started - ' + subject, 'success');
            
            // Load video
            videoFeed.src = '/video_feed_attendance?subject=' + encodeURIComponent(subject) + '&t=' + Date.now();
            
            // Start polling
            pollTimer = setInterval(updateAttendanceList, 1000);
        }
        
        function stopAttendance() {
            stopBtn.disabled = true;
            
            fetch('/stop_attendance', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    statusBadge.textContent = 'Stopped';
                    statusBadge.className = 'badge bg-secondary';
                    videoFeed.src = '';
                    startBtn.classList.remove('d-none');
                    stopBtn.classList.add('d-none');
                    stopBtn.disabled = false;
                    
                    if (pollTimer) {
                        clearInterval(pollTimer);
                        pollTimer = null;
                    }
                    
                    showMessage('Attendance stopped successfully', 'success');
                }
            })
            .catch(err => {
                showMessage('Error stopping attendance', 'danger');
                stopBtn.disabled = false;
            });
        }
        
        function updateAttendanceList() {
            fetch('/get_marked_today')
                .then(res => res.json())
                .then(data => {
                    const count = data.marked ? data.marked.length : 0;
                    markedCount.textContent = count;
                    
                    if (count > 0) {
                        markedList.innerHTML = data.marked.map(name => 
                            '<div class="list-group-item d-flex align-items-center">' +
                                '<i class="bi bi-check-circle-fill text-success me-2"></i>' +
                                '<strong>' + name + '</strong>' +
                            '</div>'
                        ).join('');
                    } else {
                        markedList.innerHTML = '<div class="list-group-item text-center text-muted py-3">No faces detected yet</div>';
                    }
                })
                .catch(() => {}); // Silent fail for polling
        }
        
        function showMessage(msg, type) {
            const alertHtml = `
                <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                    <i class="bi bi-info-circle me-2"></i>${msg}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
            messageDiv.innerHTML = alertHtml;
        }
        
        // Initial poll
        updateAttendanceList();
    }
    
    // Global functions
    window.deleteTodayRecords = function() {
        if (confirm('Delete today\\'s records?')) {
            const today = new Date().toLocaleDateString('en-GB', {
                day: '2-digit',
                month: '2-digit', 
                year: 'numeric'
            }).replace(/\//g, '-');
            
            fetch('/delete_record/Attendance_' + today + '.csv', {method: 'DELETE'})
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert('Delete failed: ' + (data.message || 'Unknown error'));
                    }
                });
        }
    };
})();

