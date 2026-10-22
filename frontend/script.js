"use strict";

// ============================================
// JARVIS NEXUS - FRONTEND JAVASCRIPT
// ============================================

// Get the dashboard status message element
const statusMessage = document.getElementById("message");

// ============================================
// API REQUEST FUNCTION
// ============================================

async function apiRequest(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...options.headers
        }
    });

    if (!response.ok) {
        throw new Error("Request failed: HTTP " + response.status);
    }

    return await response.json();
}

// ============================================
// SHOW STATUS MESSAGE
// ============================================

function showMessage(text) {
    if (statusMessage) {
        statusMessage.textContent = text;
    }
}

// ============================================
// CHECK BACKEND CONNECTION
// ============================================

async function checkHealth() {
    try {
        const result = await apiRequest("/api/health");

        const statusElement = document.getElementById("status");

        if (statusElement) {
            statusElement.textContent = result.success
                ? "● System Online"
                : "● Offline";
        }

        await loadTasks();
        await loadReminders();

    } catch (error) {
        console.error("Backend connection error:", error);

        const statusElement = document.getElementById("status");

        if (statusElement) {
            statusElement.textContent = "● Connection Error";
        }

        showMessage("Could not connect to the backend.");
    }
}

// ============================================
// ADD A TASK
// ============================================

async function addTask() {
    const input = document.getElementById("taskInput");

    if (!input) {
        return;
    }

    const title = input.value.trim();

    if (!title) {
        showMessage("Please enter a task.");
        return;
    }

    try {
        const result = await apiRequest("/api/tasks", {
            method: "POST",
            body: JSON.stringify({ title: title })
        });

        input.value = "";

        showMessage(result.message || "Task added successfully.");

        await loadTasks();

    } catch (error) {
        console.error("Add task error:", error);
        showMessage("Could not add task: " + error.message);
    }
}

// ============================================
// LOAD AND DISPLAY TASKS
// ============================================

async function loadTasks() {
    const result = await apiRequest("/api/tasks");
    const list = document.getElementById("taskList");

    if (!list) {
        return;
    }

    list.replaceChildren();

    const tasks = Array.isArray(result)
        ? result
        : (result.tasks || []);

    tasks.forEach(function (task) {
        const item = document.createElement("li");
        const text = document.createElement("span");

        text.textContent =
            (task.completed ? "✓ " : "○ ") + task.title;

        item.appendChild(text);

        if (!task.completed) {
            const button = document.createElement("button");

            button.textContent = "Complete";

            button.addEventListener("click", function () {
                completeTask(task.id);
            });

            item.appendChild(button);
        }

        list.appendChild(item);
    });
}

// ============================================
// MARK TASK AS COMPLETE
// ============================================

async function completeTask(taskId) {
    try {
        const result = await apiRequest("/api/tasks/complete", {
            method: "POST",
            body: JSON.stringify({ task_id: taskId })
        });

        showMessage(result.message || "Task updated successfully.");

        await loadTasks();

    } catch (error) {
        console.error("Complete task error:", error);
        showMessage("Could not complete task: " + error.message);
    }
}

// ============================================
// ADD A REMINDER
// ============================================

async function addReminder() {
    const titleElement = document.getElementById("reminderTitle");
    const timeElement = document.getElementById("reminderTime");

    if (!titleElement || !timeElement) {
        return;
    }

    const title = titleElement.value.trim();
    const reminderTime = timeElement.value;

    if (!title || !reminderTime) {
        showMessage("Enter a reminder title and time.");
        return;
    }

    try {
        const result = await apiRequest("/api/reminders", {
            method: "POST",
            body: JSON.stringify({
                title: title,
                reminder_time: reminderTime
            })
        });

        titleElement.value = "";
        timeElement.value = "";

        showMessage(result.message || "Reminder saved successfully.");

        await loadReminders();

    } catch (error) {
        console.error("Add reminder error:", error);
        showMessage("Could not save reminder: " + error.message);
    }
}

// ============================================
// LOAD AND DISPLAY REMINDERS
// ============================================

async function loadReminders() {
    const result = await apiRequest("/api/reminders");
    const list = document.getElementById("reminderList");

    if (!list) {
        return;
    }

    list.replaceChildren();

    const reminders = Array.isArray(result)
        ? result
        : (result.reminders || []);

    reminders.forEach(function (reminder) {
        const item = document.createElement("li");

        item.textContent =
            reminder.title + " — " + reminder.reminder_time;

        list.appendChild(item);
    });
}

// ============================================
// JARVIS AI CHAT
// ============================================

function setupJarvisChat() {
    const chatForm = document.getElementById("chatForm");
    const chatInput = document.getElementById("chatInput");
    const chatMessages = document.getElementById("chatMessages");
    const chatStatus = document.getElementById("chatStatus");
    const chatSendButton = document.getElementById("chatSendButton");

    if (
        !chatForm ||
        !chatInput ||
        !chatMessages ||
        !chatStatus ||
        !chatSendButton
    ) {
        console.error(
            "JARVIS chat elements are missing. Check frontend/index.html."
        );
        return;
    }

    // Prevent accidental duplicate event registration
    if (chatForm.dataset.jarvisInitialized === "true") {
        return;
    }

    chatForm.dataset.jarvisInitialized = "true";

    chatForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const userText = chatInput.value.trim();

        if (!userText) {
            chatStatus.textContent = "Please type a message.";
            return;
        }

        // Display the user's message
        const userMessage = document.createElement("p");
        userMessage.textContent = "You: " + userText;
        chatMessages.appendChild(userMessage);

        chatInput.value = "";
        chatStatus.textContent = "JARVIS is thinking...";
        chatSendButton.disabled = true;

        try {
            // Send the message to the FastAPI backend
            const result = await apiRequest("/api/chat", {
                method: "POST",
                body: JSON.stringify({
                    message: userText
                })
            });

            // Display JARVIS's response
            const aiMessage = document.createElement("p");

            aiMessage.textContent = result.success
                ? "JARVIS: " + (result.response || "No response received.")
                : "JARVIS: " + (result.response || "Something went wrong.");

            chatMessages.appendChild(aiMessage);

            chatStatus.textContent = result.success
                ? ""
                : "Please try another message.";

        } catch (error) {
            console.error("JARVIS chat error:", error);

            const errorMessage = document.createElement("p");
            errorMessage.textContent =
                "JARVIS: Sorry, I could not connect. " + error.message;

            chatMessages.appendChild(errorMessage);

            chatStatus.textContent =
                "Request failed. Check that the backend is running.";
        } finally {
            chatSendButton.disabled = false;
            chatMessages.scrollTop = chatMessages.scrollHeight;
            chatInput.focus();
        }
    });
}

// ============================================
// INITIALIZE JARVIS NEXUS
// ============================================

function initializeJarvisNexus() {
    setupJarvisChat();
    checkHealth();
}

// Initialize after the HTML has loaded
if (document.readyState === "loading") {
    document.addEventListener(
        "DOMContentLoaded",
        initializeJarvisNexus,
        { once: true }
    );
} else {
    initializeJarvisNexus();
}