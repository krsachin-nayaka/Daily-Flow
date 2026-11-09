/**
 * DailyFlow – Frontend Application Logic (Vanilla JavaScript)
 *
 * Responsibilities:
 * 1. Communicate with the FastAPI backend using the standard Fetch API.
 * 2. Manage client-side UI state (active view, search term, active filters).
 * 3. Render task cards, badges, statistics, and progress bars dynamically.
 * 4. Handle modal dialogs for creating, editing, and deleting tasks.
 * 5. Provide immediate visual feedback via toasts and smooth transitions.
 */

// ============================================================================
// State Management
// ============================================================================
const state = {
  currentView: "all",        // "all" | "today" | "pending" | "completed"
  selectedCategory: "",      // "" for all categories, or "DSA", "Python", etc.
  selectedPriority: "",      // "" for all priorities, or "High", "Medium", "Low"
  searchQuery: "",           // text search query
  tasks: [],                 // task list loaded from the backend
  stats: {                   // stats from /tasks/stats
    total_tasks: 0,
    completed_tasks: 0,
    pending_tasks: 0,
    today_total: 0,
    today_completed: 0,
    completion_percentage: 0.0,
    today_completion_percentage: 0.0
  },
  taskToDelete: null         // stores { id, title } when delete modal is open
};

// Base URL for task API endpoints
const API_BASE = "/tasks";

// ============================================================================
// DOM Elements
// ============================================================================
const dom = {
  // Views and filters
  viewTitle: document.getElementById("current-view-title"),
  currentDateDisplay: document.getElementById("current-date-display"),
  navItems: document.querySelectorAll(".nav-item"),
  catPills: document.querySelectorAll(".cat-pill"),
  searchInput: document.getElementById("search-input"),
  priorityFilter: document.getElementById("priority-filter-select"),

  // Task list and empty state
  taskList: document.getElementById("task-list"),
  tasksCountText: document.getElementById("tasks-count-text"),
  emptyState: document.getElementById("empty-state"),
  emptyStateMsg: document.getElementById("empty-state-message"),

  // Navigation badge counters
  badgeAll: document.getElementById("badge-all"),
  badgeToday: document.getElementById("badge-today"),
  badgePending: document.getElementById("badge-pending"),
  badgeCompleted: document.getElementById("badge-completed"),

  // Dashboard stats
  statTotal: document.getElementById("stat-total"),
  statCompleted: document.getElementById("stat-completed"),
  statPending: document.getElementById("stat-pending"),
  statDailyPercent: document.getElementById("stat-daily-percent"),
  dailyProgressFill: document.getElementById("daily-progress-fill"),
  dailyProgressSubtext: document.getElementById("daily-progress-subtext"),

  // Task modal (Create/Edit)
  taskModal: document.getElementById("task-modal"),
  modalTitle: document.getElementById("modal-title"),
  taskForm: document.getElementById("task-form"),
  taskIdInput: document.getElementById("task-id"),
  taskTitleInput: document.getElementById("task-title-input"),
  taskDescInput: document.getElementById("task-desc-input"),
  taskCategorySelect: document.getElementById("task-category-select"),
  taskPrioritySelect: document.getElementById("task-priority-select"),
  taskDueDateInput: document.getElementById("task-due-date-input"),
  btnDueToday: document.getElementById("btn-due-today"),
  btnDueTomorrow: document.getElementById("btn-due-tomorrow"),
  btnOpenCreateModal: document.getElementById("btn-open-create-modal"),
  btnCloseModal: document.getElementById("btn-close-modal"),
  btnCancelModal: document.getElementById("btn-cancel-modal"),
  btnEmptyCreate: document.getElementById("btn-empty-create"),

  // Delete confirmation modal
  deleteModal: document.getElementById("delete-modal"),
  deleteTaskTitle: document.getElementById("delete-task-title"),
  btnCancelDelete: document.getElementById("btn-cancel-delete"),
  btnConfirmDelete: document.getElementById("btn-confirm-delete"),

  // Toast container
  toastContainer: document.getElementById("toast-container")
};

// ============================================================================
// API Helper Functions (Using Fetch API)
// ============================================================================

/**
 * Fetch task statistics from GET /tasks/stats
 */
async function fetchStats() {
  try {
    const response = await fetch(`${API_BASE}/stats`);
    if (!response.ok) throw new Error("Failed to load statistics");
    state.stats = await response.json();
    renderStats();
  } catch (error) {
    console.error("Error fetching stats:", error);
  }
}

/**
 * Fetch tasks based on active view and filters
 */
async function fetchTasks() {
  try {
    let url;
    const params = new URLSearchParams();

    // 1. Determine endpoint depending on active view
    if (state.currentView === "today") {
      url = `${API_BASE}/today`;
    } else {
      url = `${API_BASE}/`;
      // Filter by completion if on pending or completed view
      if (state.currentView === "pending") {
        params.append("is_completed", "false");
      } else if (state.currentView === "completed") {
        params.append("is_completed", "true");
      }
    }

    // 2. Add category filter if selected
    if (state.selectedCategory) {
      params.append("category", state.selectedCategory);
    }

    // 3. Add priority filter if selected
    if (state.selectedPriority) {
      params.append("priority", state.selectedPriority);
    }

    const fullUrl = params.toString() ? `${url}?${params.toString()}` : url;
    const response = await fetch(fullUrl);
    if (!response.ok) throw new Error("Failed to fetch tasks");

    const data = await response.json();
    state.tasks = data;
    renderTasks();
  } catch (error) {
    console.error("Error fetching tasks:", error);
    showToast("Error loading tasks", "error");
  }
}

/**
 * Create a new task via POST /tasks/
 */
async function createTask(payload) {
  try {
    const response = await fetch(`${API_BASE}/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || "Failed to create task");
    }

    showToast("Task created successfully!", "success");
    closeModal();
    await fetchTasks();
    await fetchStats();
  } catch (error) {
    console.error("Error creating task:", error);
    showToast(error.message, "error");
  }
}

/**
 * Update an existing task via PUT /tasks/{id}
 */
async function updateTask(taskId, payload) {
  try {
    const response = await fetch(`${API_BASE}/${taskId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || "Failed to update task");
    }

    showToast("Task updated successfully!", "success");
    closeModal();
    await fetchTasks();
    await fetchStats();
  } catch (error) {
    console.error("Error updating task:", error);
    showToast(error.message, "error");
  }
}

/**
 * Toggle task completion via PATCH /tasks/{id}/complete
 */
async function toggleTaskComplete(taskId) {
  try {
    const response = await fetch(`${API_BASE}/${taskId}/complete`, {
      method: "PATCH"
    });

    if (!response.ok) throw new Error("Failed to update task status");

    const updatedTask = await response.json();
    const statusText = updatedTask.is_completed ? "completed" : "pending";
    showToast(`Task marked as ${statusText}`, "info");

    await fetchTasks();
    await fetchStats();
  } catch (error) {
    console.error("Error toggling task completion:", error);
    showToast("Failed to update status", "error");
  }
}

/**
 * Delete a task via DELETE /tasks/{id}
 */
async function deleteTask(taskId) {
  try {
    const response = await fetch(`${API_BASE}/${taskId}`, {
      method: "DELETE"
    });

    if (!response.ok) throw new Error("Failed to delete task");

    showToast("Task deleted", "info");
    closeDeleteModal();
    await fetchTasks();
    await fetchStats();
  } catch (error) {
    console.error("Error deleting task:", error);
    showToast("Failed to delete task", "error");
  }
}

// ============================================================================
// UI Rendering Functions
// ============================================================================

/**
 * Format today's date for display (e.g., "Monday, November 9, 2026")
 */
function displayCurrentDate() {
  const options = { weekday: "long", year: "numeric", month: "long", day: "numeric" };
  const todayStr = new Date().toLocaleDateString(undefined, options);
  dom.currentDateDisplay.textContent = todayStr;
}

/**
 * Format ISO date string (YYYY-MM-DD) into user-friendly text
 */
function formatDueDate(dateStr) {
  if (!dateStr) return null;

  const [y, m, d] = dateStr.split("-").map(Number);
  const taskDate = new Date(y, m - 1, d);

  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  const diffTime = taskDate.getTime() - today.getTime();
  const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays === 0) {
    return { text: "Due Today", class: "is-today" };
  } else if (diffDays === 1) {
    return { text: "Due Tomorrow", class: "is-upcoming" };
  } else if (diffDays === -1) {
    return { text: "Yesterday (Overdue)", class: "is-overdue" };
  } else if (diffDays < -1) {
    return { text: `${Math.abs(diffDays)} days overdue`, class: "is-overdue" };
  } else {
    const formatted = taskDate.toLocaleDateString(undefined, { month: "short", day: "numeric" });
    return { text: `Due ${formatted}`, class: "" };
  }
}

/**
 * Render the statistics cards and today's progress bar
 */
function renderStats() {
  const {
    total_tasks,
    completed_tasks,
    pending_tasks,
    today_total,
    today_completed,
    today_completion_percentage
  } = state.stats;

  // Update card numbers
  dom.statTotal.textContent = total_tasks;
  dom.statCompleted.textContent = completed_tasks;
  dom.statPending.textContent = pending_tasks;

  // Update nav badge counters
  dom.badgeAll.textContent = total_tasks;
  dom.badgeToday.textContent = today_total;
  dom.badgePending.textContent = pending_tasks;
  dom.badgeCompleted.textContent = completed_tasks;

  // Update Today's Completion Progress Bar
  dom.statDailyPercent.textContent = `${today_completion_percentage}%`;
  dom.dailyProgressFill.style.width = `${today_completion_percentage}%`;
  dom.dailyProgressSubtext.textContent = `${today_completed} of ${today_total} tasks done today`;
}

/**
 * Render task cards into the DOM
 */
function renderTasks() {
  dom.taskList.innerHTML = "";

  // Apply client-side search query filtering
  let filtered = state.tasks;
  if (state.searchQuery.trim() !== "") {
    const q = state.searchQuery.toLowerCase();
    filtered = filtered.filter(t =>
      t.title.toLowerCase().includes(q) ||
      (t.description && t.description.toLowerCase().includes(q))
    );
  }

  // Update tasks counter heading
  const count = filtered.length;
  dom.tasksCountText.textContent = `Showing ${count} task${count === 1 ? "" : "s"}`;

  // Check if empty
  if (count === 0) {
    dom.emptyState.style.display = "flex";
    if (state.searchQuery) {
      dom.emptyStateMsg.textContent = `No tasks matching "${state.searchQuery}"`;
    } else if (state.currentView === "today") {
      dom.emptyStateMsg.textContent = "No tasks scheduled for today. Take a breather or add one!";
    } else if (state.currentView === "completed") {
      dom.emptyStateMsg.textContent = "No completed tasks yet. Finish a task to see it here!";
    } else if (state.currentView === "pending") {
      dom.emptyStateMsg.textContent = "All caught up! No pending tasks.";
    } else {
      dom.emptyStateMsg.textContent = "Get started by creating your first task.";
    }
    return;
  }

  dom.emptyState.style.display = "none";

  // Build task cards
  filtered.forEach(task => {
    const card = document.createElement("div");
    card.className = `task-card ${task.is_completed ? "is-completed" : ""}`;
    card.dataset.taskId = task.id;

    // Priority class mapping
    const prioLower = task.priority.toLowerCase();
    const prioBadgeClass = `priority-${prioLower}`;

    // Category badge class mapping
    const catSlug = task.category.toLowerCase().replace(/[^a-z0-9]/g, "");
    const catBadgeClass = `badge-cat-${catSlug}`;

    // Due date info
    const dateInfo = formatDueDate(task.due_date);

    card.innerHTML = `
      <div class="task-checkbox-wrapper">
        <input
          type="checkbox"
          class="task-checkbox"
          ${task.is_completed ? "checked" : ""}
          aria-label="Mark task as ${task.is_completed ? "pending" : "completed"}"
        />
      </div>

      <div class="task-body">
        <h4 class="task-title">${escapeHtml(task.title)}</h4>
        ${task.description ? `<p class="task-desc">${escapeHtml(task.description)}</p>` : ""}

        <div class="task-meta">
          <span class="badge ${prioBadgeClass}">${task.priority} Priority</span>
          <span class="badge ${catBadgeClass}">${task.category}</span>
          ${dateInfo ? `<span class="badge badge-date ${dateInfo.class}">📅 ${dateInfo.text}</span>` : ""}
        </div>
      </div>

      <div class="task-actions">
        <button class="btn-icon btn-edit" title="Edit Task" aria-label="Edit Task">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
            <path d="m15 5 4 4"/>
          </svg>
        </button>
        <button class="btn-icon btn-delete" title="Delete Task" aria-label="Delete Task">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 6h18"/>
            <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
            <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
            <line x1="10" y1="11" x2="10" y2="17"/>
            <line x1="14" y1="11" x2="14" y2="17"/>
          </svg>
        </button>
      </div>
    `;

    // Event: Toggle complete on checkbox change
    const checkbox = card.querySelector(".task-checkbox");
    checkbox.addEventListener("change", () => toggleTaskComplete(task.id));

    // Event: Open edit modal
    const editBtn = card.querySelector(".btn-edit");
    editBtn.addEventListener("click", () => openEditModal(task));

    // Event: Open delete confirmation
    const deleteBtn = card.querySelector(".btn-delete");
    deleteBtn.addEventListener("click", () => openDeleteModal(task));

    dom.taskList.appendChild(card);
  });
}

/**
 * Safely escape HTML to prevent XSS injection
 */
function escapeHtml(str) {
  if (!str) return "";
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// ============================================================================
// Modal & Form Handlers
// ============================================================================

/**
 * Open modal to create a new task
 */
function openCreateModal() {
  dom.modalTitle.textContent = "Create New Task";
  dom.taskIdInput.value = "";
  dom.taskForm.reset();

  // Pre-fill today's date by default if user is on Today's Tasks view
  if (state.currentView === "today") {
    dom.taskDueDateInput.value = getTodayISODate();
  }

  // Pre-fill selected category if active
  if (state.selectedCategory) {
    dom.taskCategorySelect.value = state.selectedCategory;
  }

  dom.taskModal.style.display = "flex";
  dom.taskTitleInput.focus();
}

/**
 * Open modal to edit an existing task
 */
function openEditModal(task) {
  dom.modalTitle.textContent = "Edit Task";
  dom.taskIdInput.value = task.id;
  dom.taskTitleInput.value = task.title;
  dom.taskDescInput.value = task.description || "";
  dom.taskCategorySelect.value = task.category;
  dom.taskPrioritySelect.value = task.priority;
  dom.taskDueDateInput.value = task.due_date || "";

  dom.taskModal.style.display = "flex";
  dom.taskTitleInput.focus();
}

/**
 * Close create/edit modal
 */
function closeModal() {
  dom.taskModal.style.display = "none";
  dom.taskForm.reset();
}

/**
 * Open delete confirmation modal
 */
function openDeleteModal(task) {
  state.taskToDelete = task;
  dom.deleteTaskTitle.textContent = `"${task.title}"`;
  dom.deleteModal.style.display = "flex";
}

/**
 * Close delete confirmation modal
 */
function closeDeleteModal() {
  state.taskToDelete = null;
  dom.deleteModal.style.display = "none";
}

/**
 * Return today's date formatted as YYYY-MM-DD
 */
function getTodayISODate() {
  const d = new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

/**
 * Return tomorrow's date formatted as YYYY-MM-DD
 */
function getTomorrowISODate() {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

// ============================================================================
// Toast Notification System
// ============================================================================
function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;

  const iconSvg = type === "success"
    ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>`
    : type === "error"
    ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#F43F5E" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`
    : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#06B6D4" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`;

  toast.innerHTML = `${iconSvg}<span>${escapeHtml(message)}</span>`;
  dom.toastContainer.appendChild(toast);

  // Auto remove after 3 seconds
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ============================================================================
// Event Listeners Setup
// ============================================================================
function setupEventListeners() {
  // 1. Navigation items (All, Today, Pending, Completed)
  dom.navItems.forEach(btn => {
    btn.addEventListener("click", () => {
      dom.navItems.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      const view = btn.dataset.view;
      state.currentView = view;

      // Update header title
      if (view === "all") dom.viewTitle.textContent = "All Tasks";
      if (view === "today") dom.viewTitle.textContent = "Today's Tasks";
      if (view === "pending") dom.viewTitle.textContent = "Pending Tasks";
      if (view === "completed") dom.viewTitle.textContent = "Completed Tasks";

      fetchTasks();
    });
  });

  // 2. Category Filter Pills
  dom.catPills.forEach(pill => {
    pill.addEventListener("click", () => {
      dom.catPills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");

      state.selectedCategory = pill.dataset.category;
      fetchTasks();
    });
  });

  // 3. Search Input (live filtering)
  dom.searchInput.addEventListener("input", (e) => {
    state.searchQuery = e.target.value;
    renderTasks();
  });

  // 4. Priority Filter Dropdown
  dom.priorityFilter.addEventListener("change", (e) => {
    state.selectedPriority = e.target.value;
    fetchTasks();
  });

  // 5. Open Create Modal buttons
  dom.btnOpenCreateModal.addEventListener("click", openCreateModal);
  dom.btnEmptyCreate.addEventListener("click", openCreateModal);

  // 6. Close Modal buttons
  dom.btnCloseModal.addEventListener("click", closeModal);
  dom.btnCancelModal.addEventListener("click", closeModal);

  // 7. Modal quick due date buttons
  dom.btnDueToday.addEventListener("click", () => {
    dom.taskDueDateInput.value = getTodayISODate();
  });
  dom.btnDueTomorrow.addEventListener("click", () => {
    dom.taskDueDateInput.value = getTomorrowISODate();
  });

  // 8. Form Submit (Create or Update)
  dom.taskForm.addEventListener("submit", (e) => {
    e.preventDefault();

    const title = dom.taskTitleInput.value.trim();
    if (!title) {
      showToast("Title is required", "error");
      return;
    }

    const payload = {
      title: title,
      description: dom.taskDescInput.value.trim() || null,
      category: dom.taskCategorySelect.value,
      priority: dom.taskPrioritySelect.value,
      due_date: dom.taskDueDateInput.value || null
    };

    const taskId = dom.taskIdInput.value;
    if (taskId) {
      updateTask(parseInt(taskId, 10), payload);
    } else {
      createTask(payload);
    }
  });

  // 9. Delete Confirmation Handlers
  dom.btnCancelDelete.addEventListener("click", closeDeleteModal);
  dom.btnConfirmDelete.addEventListener("click", () => {
    if (state.taskToDelete) {
      deleteTask(state.taskToDelete.id);
    }
  });

  // 10. Close modals when clicking backdrop or pressing Escape
  window.addEventListener("click", (e) => {
    if (e.target === dom.taskModal) closeModal();
    if (e.target === dom.deleteModal) closeDeleteModal();
  });

  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeModal();
      closeDeleteModal();
    }
  });
}

// ============================================================================
// Application Initialization
// ============================================================================
document.addEventListener("DOMContentLoaded", () => {
  displayCurrentDate();
  setupEventListeners();
  fetchStats();
  fetchTasks();
});
