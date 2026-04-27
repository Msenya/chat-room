$(document).ready(function () {
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);
    console.log("Connecting to:", location.protocol + '//' + document.domain + ':' + location.port);

    // Socket connection handlers
    socket.on('connect', function () {
        console.log("Connected to the server");
        socket.emit('join', {});
    });

    socket.on('error', function (error) {
        console.error("Socket error:", error);
    });

    // Add sidebar footer
    $('#sidebar').append(`
        <div class="sidebar-footer">
            <button id="settingsBtn">
                <i class="fas fa-cog"></i>Settings
            </button>
            <button id="logoutBtn">
                <i class="fas fa-sign-out-alt"></i>Logout
            </button>
        </div>
    `);

    // Message handling
    function createMessageBubble(username, message, isSent) {
        var bubbleDiv = $('<div>')
            .addClass('message-bubble')
            .addClass(isSent ? 'sent' : 'received');
        
        var usernameDiv = $('<div>')
            .addClass('message-username')
            .text(username);
        
        var messageContent = $('<div>')
            .addClass('message-content')
            .text(message);
        
        var timestampDiv = $('<div>')
            .addClass('message-timestamp')
            .text(new Date().toLocaleTimeString());
        
        bubbleDiv.append(usernameDiv, messageContent, timestampDiv);
        return bubbleDiv;
    }

    socket.on('message', function (data) {
        console.log("Received message:", data); // Debug log
        var isSent = data.username === $('#username').val(); // Get username from hidden input
        var messageElement = createMessageBubble(data.username, data.msg, isSent);
        $('#messages').append(messageElement);
        $('#messages').scrollTop($('#messages')[0].scrollHeight);
    });

    // User list updates with green dot for online users
    socket.on('updateUserList', function (users) {
        var userList = $('#userList');
        userList.empty();
        users.forEach(function (user) {
            var userListItem = $('<li>');
            var onlineStatus = $('<span>')
                .addClass('online-status')
                .css('background-color', 'green'); // Green dot for online users
            userListItem.append(onlineStatus, $('<span>').text(user));
            userList.append(userListItem);
        });
    });

    // Message input handling
    $('#messageInput').on('keydown', function (e) {
        if (e.key === 'Enter') {
            if (e.shiftKey) {
                // Allow new line with Shift+Enter
                return true;
            } else {
                e.preventDefault();
                sendMessage();
            }
        }
    });

    $('#sendButton').click(function(e) {
        e.preventDefault();
        sendMessage();
    });

    function sendMessage() {
        var message = $('#messageInput').val().trim();
        if (message === "") {
            return;
        }
        console.log("Sending message:", message); // Debug log
        socket.emit('message', {
            msg: message,
            username: $('#username').val() // Get username from hidden input
        });
        $('#messageInput').val('');
        $('#messageInput').css('height', 'auto');
    }

    // Auto-resize input field
    $('#messageInput').on('input', function () {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Sidebar toggle with proper class handling
    var isSidebarOpen = false;
    $('#toggleSidebar').click(function () {
        isSidebarOpen = !isSidebarOpen;
        $('#sidebar').toggleClass('open');
        $('.chat-container').toggleClass('sidebar-open');
    });

    // Placeholder functionality
    $('#settingsBtn').click(function() {
        alert('Settings functionality will be implemented later');
    });

    $('#logoutBtn').click(function() {
        alert('Logout functionality will be implemented later');
    });

    // Handle kick and ban
    socket.on('kick', function (data) {
        if (data.name === $('#username').val()) {
            alert(data.msg);
            window.location.href = '/';
        }
    });

    socket.on('ban', function (data) {
        if (data.name === $('#username').val()) {
            alert(data.msg);
            window.location.href = '/';
        }
    });
});
