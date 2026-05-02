// FIXED ATTENDANCE JS - DEBUG ENABLED
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Attendance page loaded');
    
    const startBtn = document.getElementById('startAttendanceBtn');
    const stopBtn = document.getElementById('stopAttendanceBtn');
    const videoFeed = document.getElementById('videoFeed');
    const statusBadge = document.getElementById('statusBadge');
    const messageDiv = document.getElementById('attendanceMessage');
    const markedList = document.getElementById('markedList');
    const markedCount = document.getElementById('markedCount');
    const subjectSelect = document.getElementById('subjectSelect');
    const loadingDiv = document.getElementById('attendanceLoading');
    const videoPlaceholder = document.getElementById('videoPlaceholder');

    let pollTimer = null;
    
    // DEBUG: Log all clicks
    startBtn.addEventListener('click', function() {
        console.log('🔥 START BUTTON CLICKED!');
        const subject = subjectSelect.value.trim();
        console.log('Subject:', subject);
        
        if (!subject) {
            alert('⚠️ Please select a subject first!');
            console.log('❌ No subject selected');
            return;
        }
        
        // UI UPDATE
        console.log('🎬 Starting attendance...');
        startBtn.disabled = true;
        startBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i><span class="fw-bold">Starting...</span>';
        stopBtn.classList.remove('d-none');
        statusBadge.textContent = 'Connecting...';
        statusBadge.className = 'badge bg-warning animate-pulse';
        loadingDiv.classList.remove('d-none');
        videoPlaceholder.classList.add('d-none');
        
        showMessage(`Connecting to camera for ${subject}...`, 'info');
        
        // FORCE NEW STREAM with timestamp
        const streamUrl = `/video_feed_attendance?subject=${encodeURIComponent(subject)}&t=${Date.now()}&nocache=${Math.random()}`;
        console.log('📹 Stream URL:', streamUrl);
        videoFeed.src = streamUrl;
        videoFeed.style.display = 'block';
        
        // Start polling
        pollTimer = setInterval(updateMarkedList, 1000);
    });
    
    stopBtn.addEventListener('click', function() {
        console.log('🛑 STOP BUTTON CLICKED!');
        clearInterval(pollTimer);
        fetch('/stop_attendance', {method: 'POST'})
        .then(() => {
            videoFeed.src = '';
            videoFeed.style.display = 'none';
            startBtn.classList.remove('d-none');
            stopBtn.classList.add('d-none');
            startBtn.disabled = false;
            startBtn.innerHTML = '<i class="bi bi-play-fill me-2"></i><span class="fw-bold fs-5">START LIVE ATTENDANCE</span>';
            statusBadge.textContent = 'Ready';
            statusBadge.className = 'badge bg-success';
            loadingDiv.classList.add('d-none');
            videoPlaceholder.classList.remove('d-none');
            showMessage('Session stopped', 'success');
        });
    });
    
    videoFeed.addEventListener('loadstart', () => console.log('📹 Stream started'));
    videoFeed.addEventListener('load', () => {
        console.log('✅ VIDEO LOADED!');
        loadingDiv.classList.add('d-none');
        statusBadge.textContent = 'Live';
        statusBadge.className = 'badge bg-success';
        showMessage('✅ Live recognition active!', 'success');
    });
    
    videoFeed.addEventListener('error', (e) => {
        console.error('❌ Video error:', e);
        loadingDiv.classList.add('d-none');
        statusBadge.textContent = 'Error';
        statusBadge.className = 'badge bg-danger';
        showMessage('Camera error - check permissions or try refresh', 'danger');
        startBtn.disabled = false;
        startBtn.innerHTML = '<i class="bi bi-play-fill me-2"></i><span class="fw-bold fs-5">START LIVE ATTENDANCE</span>';
    });
    
    function updateMarkedList() {
        fetch('/get_marked_today')
            .then(r => r.json())
            .then(data => {
                markedCount.textContent = data.marked?.length || 0;
                if (data.marked?.length > 0) {
                    markedList.innerHTML = data.marked.map(n => 
                        `<div class="list-group-item">
                            <i class="bi bi-check-lg text-success me-2"></i>${n}
                        </div>`
                    ).join('');
                }
            })
            .catch(e => console.log('Poll error:', e));
    }
    
    function showMessage(msg, type) {
        messageDiv.innerHTML = `
            <div class="alert alert-${type} alert-dismissible fade show small" role="alert">
                ${msg}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
    }
    
    window.deleteTodayRecords = function() {
        if (confirm('Delete today\\'s records?')) {
            location.reload();
        }
    };
    
    // Initial check
    console.log('🎯 Attendance ready - Open Console (F12) for debug');
});

