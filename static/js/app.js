const API_BASE = '/api';
const TASKS_PER_PAGE = 5;
let currentUser = null;
let editingTaskId = null;
let deleteCallback = null;
let allMyTasks = [];
let allAdminTasks = [];
let myTasksShown = TASKS_PER_PAGE;
let adminTasksShown = TASKS_PER_PAGE;

/* ---- UTILS ---- */
function showToast(msg, isError = false) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.style.background = isError ? '#c62828' : '#1a4d2e';
  t.classList.remove('hidden');
  setTimeout(() => t.classList.add('hidden'), 3500);
}

function showError(elemId, msg) {
  const el = document.getElementById(elemId);
  el.textContent = msg;
  el.classList.remove('hidden');
}

function hideError(elemId) {
  document.getElementById(elemId).classList.add('hidden');
}

function showSection(name) {
  document.querySelectorAll('.main-section').forEach(s => s.classList.add('hidden'));
  const sec = document.getElementById('section-' + name);
  if (sec) sec.classList.remove('hidden');
  if (name === 'tasks') loadMyTasks();
  if (name === 'admin-users') loadAllUsers();
  if (name === 'admin-tasks') loadAllTasks();
}

function openModal(id) { document.getElementById(id).classList.remove('hidden'); }
function closeModal(id) { document.getElementById(id).classList.add('hidden'); }

function switchTab(tab) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-login').classList.add('hidden');
  document.getElementById('tab-register').classList.add('hidden');
  document.getElementById('tab-' + tab).classList.remove('hidden');
  event.target.classList.add('active');
}

async function apiFetch(path, method = 'GET', body = null) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (currentUser && currentUser.idToken) {
    opts.headers['Authorization'] = 'Bearer ' + currentUser.idToken;
  }
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(API_BASE + path, opts);
  const data = await res.json();
  return { ok: res.ok, status: res.status, data };
}

async function apiUpload(path, formData) {
  const opts = { method: 'POST', headers: {} };
  if (currentUser && currentUser.idToken) {
    opts.headers['Authorization'] = 'Bearer ' + currentUser.idToken;
  }
  opts.body = formData;
  const res = await fetch(API_BASE + path, opts);
  const data = await res.json();
  return { ok: res.ok, data };
}

/* ---- AUTH ---- */
async function register() {
  hideError('reg-error');
  document.getElementById('reg-success').classList.add('hidden');
  const nombre = document.getElementById('reg-nombre').value.trim();
  const email = document.getElementById('reg-email').value.trim();
  const password = document.getElementById('reg-password').value;
  const rol = document.getElementById('reg-rol').value;
  if (!nombre || !email || !password) { showError('reg-error', 'Por favor completa todos los campos.'); return; }
  const { ok, data } = await apiFetch('/users/register/', 'POST', { nombre, email, password, rol });
  if (ok) {
    document.getElementById('reg-success').textContent = '¡Cuenta creada! Ya puedes iniciar sesión.';
    document.getElementById('reg-success').classList.remove('hidden');
    document.getElementById('reg-nombre').value = '';
    document.getElementById('reg-email').value = '';
    document.getElementById('reg-password').value = '';
  } else {
    showError('reg-error', data.error || 'Error al registrar.');
  }
}

async function login() {
  hideError('login-error');
  const email = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value;
  if (!email || !password) { showError('login-error', 'Por favor completa todos los campos.'); return; }
  const { ok, data } = await apiFetch('/users/login/', 'POST', { email, password });
  if (ok) {
    currentUser = data;
    localStorage.setItem('ecoUser', JSON.stringify(data));
    afterLogin();
  } else {
    const msg = ['INVALID_LOGIN_CREDENTIALS', 'EMAIL_NOT_FOUND', 'INVALID_PASSWORD'].includes(data.error)
      ? 'Correo o contraseña incorrectos.' : (data.error || 'Error al iniciar sesión.');
    showError('login-error', msg);
  }
}

function updateNavAvatar() {
  const avatarEl = document.getElementById('nav-avatar');
  if (!avatarEl) return;
  if (currentUser && currentUser.foto_url) {
    avatarEl.innerHTML = `<img src="${currentUser.foto_url}" alt="foto"/>`;
    avatarEl.classList.add('has-photo');
  } else {
    const initial = (currentUser?.nombre || currentUser?.email || '?')[0].toUpperCase();
    avatarEl.innerHTML = initial;
    avatarEl.classList.remove('has-photo');
  }
}

function afterLogin() {
  document.getElementById('section-auth').classList.add('hidden');
  document.getElementById('navbar').classList.remove('hidden');
  document.getElementById('nav-user-name').textContent = currentUser.nombre || currentUser.email;
  const rolBadge = document.getElementById('nav-user-role');
  rolBadge.textContent = currentUser.rol === 'administrador' ? 'Admin' : 'Trabajador';
  rolBadge.className = 'role-badge ' + (currentUser.rol === 'administrador' ? 'role-admin' : 'role-trabajador');
  if (currentUser.rol === 'administrador') {
    document.getElementById('btn-admin-users').classList.remove('hidden');
    document.getElementById('btn-admin-tasks').classList.remove('hidden');
  }
  updateNavAvatar();
  showSection('tasks');
}

function logout() {
  currentUser = null;
  localStorage.removeItem('ecoUser');
  document.getElementById('navbar').classList.add('hidden');
  document.querySelectorAll('.main-section').forEach(s => s.classList.add('hidden'));
  document.getElementById('section-auth').classList.remove('hidden');
  document.getElementById('btn-admin-users').classList.add('hidden');
  document.getElementById('btn-admin-tasks').classList.add('hidden');
  document.getElementById('login-email').value = '';
  document.getElementById('login-password').value = '';
}

/* ---- PHOTO UPLOAD ---- */
function openPhotoModal() {
  document.getElementById('photo-preview').src = currentUser.foto_url || '';
  document.getElementById('photo-preview').classList.toggle('hidden', !currentUser.foto_url);
  document.getElementById('photo-input').value = '';
  document.getElementById('photo-error').classList.add('hidden');
  openModal('modal-photo');
}

function onPhotoSelected(input) {
  const file = input.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => {
    const prev = document.getElementById('photo-preview');
    prev.src = e.target.result;
    prev.classList.remove('hidden');
  };
  reader.readAsDataURL(file);
}

async function uploadPhoto() {
  const input = document.getElementById('photo-input');
  if (!input.files[0]) {
    showError('photo-error', 'Selecciona una imagen primero.');
    return;
  }
  const btn = document.getElementById('btn-upload-photo');
  btn.disabled = true;
  btn.textContent = 'Subiendo...';
  const formData = new FormData();
  formData.append('foto', input.files[0]);
  const { ok, data } = await apiUpload('/users/upload-photo/', formData);
  btn.disabled = false;
  btn.textContent = 'Subir Foto';
  if (ok) {
    currentUser.foto_url = data.foto_url;
    localStorage.setItem('ecoUser', JSON.stringify(currentUser));
    updateNavAvatar();
    closeModal('modal-photo');
    showToast('Foto de perfil actualizada.');
  } else {
    showError('photo-error', data.error || 'Error al subir la imagen.');
  }
}

/* ---- TASKS ---- */
function estadoLabel(e) { return { pendiente: 'Pendiente', en_proceso: 'En Proceso', completada: 'Completada' }[e] || e; }
function prioridadLabel(p) { return { baja: 'Baja', media: 'Media', alta: 'Alta' }[p] || p; }
function formatDate(str) {
  if (!str) return '';
  try { return new Date(str).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' }); }
  catch { return str; }
}

function renderTaskCard(task, showOwner = false) {
  const product = task.producto
    ? `<div class="task-product">♻️ ${task.producto}${task.cantidad ? ' – ' + task.cantidad + ' ' + (task.unidad || '') : ''}</div>`
    : '';
  const owner = showOwner ? `<span>👤 ${task.creado_por_nombre || 'Desconocido'}</span>` : '';
  const isOwner = currentUser && task.creado_por_uid === currentUser.uid;
  const isAdmin = currentUser && currentUser.rol === 'administrador';
  const canEdit = isOwner || isAdmin;
  return `
    <div class="task-card estado-${task.estado}" id="card-${task.id}">
      <div class="task-card-header">
        <h4>${task.titulo || 'Sin título'}</h4>
        <span class="task-badge badge-${task.estado}">${estadoLabel(task.estado)}</span>
      </div>
      <p class="task-desc">${task.descripcion || ''}</p>
      ${product}
      <div class="task-meta">
        <span>🏷️ <b>${prioridadLabel(task.prioridad)}</b></span>
        ${owner}
        <span>📅 ${formatDate(task.fecha_creacion)}</span>
      </div>
      ${canEdit ? `
      <div class="task-actions">
        <button onclick="openEditTaskModal('${task.id}')" class="btn btn-sm btn-outline">✏️ Editar</button>
        <button onclick="confirmDeleteTask('${task.id}')" class="btn btn-sm btn-danger">🗑️ Eliminar</button>
      </div>` : ''}
    </div>`;
}

function renderStats(tasks) {
  const c = { pendiente: 0, en_proceso: 0, completada: 0 };
  tasks.forEach(t => { if (c[t.estado] !== undefined) c[t.estado]++; });
  return `
    <div class="stat-chip"><div class="stat-dot dot-pendiente"></div>${c.pendiente} Pendientes</div>
    <div class="stat-chip"><div class="stat-dot dot-en_proceso"></div>${c.en_proceso} En Proceso</div>
    <div class="stat-chip"><div class="stat-dot dot-completada"></div>${c.completada} Completadas</div>
    <div class="stat-chip">📋 Total: ${tasks.length}</div>`;
}

function renderTasksWithPagination(tasks, listId, statsId, showOwner, shownCount, loadMoreFn) {
  const list = document.getElementById(listId);
  const stats = document.getElementById(statsId);
  if (stats) stats.innerHTML = renderStats(tasks);

  if (!tasks || tasks.length === 0) {
    list.innerHTML = '<div class="empty-state"><div class="empty-icon">📋</div><p>No hay tareas aún.</p></div>';
    return;
  }

  const visible = tasks.slice(0, shownCount);
  const remaining = tasks.length - shownCount;

  list.innerHTML = visible.map(t => renderTaskCard(t, showOwner)).join('');

  if (remaining > 0) {
    const btn = document.createElement('div');
    btn.className = 'load-more-wrap';
    btn.innerHTML = `<button class="btn btn-outline btn-load-more" onclick="${loadMoreFn}()">
      Ver más (${remaining} restante${remaining !== 1 ? 's' : ''}) ↓
    </button>`;
    list.appendChild(btn);
  }
}

async function loadMyTasks() {
  const list = document.getElementById('tasks-list');
  list.innerHTML = '<div class="empty-state"><div class="empty-icon">⏳</div><p>Cargando...</p></div>';
  const { ok, data } = await apiFetch('/tasks/');
  if (!ok) { list.innerHTML = `<div class="empty-state"><p>Error: ${data.error}</p></div>`; return; }
  allMyTasks = data.tareas || [];
  myTasksShown = TASKS_PER_PAGE;
  renderTasksWithPagination(allMyTasks, 'tasks-list', 'tasks-stats',
    currentUser.rol === 'administrador', myTasksShown, 'loadMoreMyTasks');
}

function loadMoreMyTasks() {
  myTasksShown += TASKS_PER_PAGE;
  renderTasksWithPagination(allMyTasks, 'tasks-list', 'tasks-stats',
    currentUser.rol === 'administrador', myTasksShown, 'loadMoreMyTasks');
}

async function loadAllTasks() {
  const list = document.getElementById('admin-tasks-list');
  list.innerHTML = '<div class="empty-state"><div class="empty-icon">⏳</div><p>Cargando...</p></div>';
  const { ok, data } = await apiFetch('/tasks/all/');
  if (!ok) { list.innerHTML = `<div class="empty-state"><p>Error: ${data.error}</p></div>`; return; }
  allAdminTasks = data.tareas || [];
  adminTasksShown = TASKS_PER_PAGE;
  renderTasksWithPagination(allAdminTasks, 'admin-tasks-list', 'admin-tasks-stats',
    true, adminTasksShown, 'loadMoreAdminTasks');
}

function loadMoreAdminTasks() {
  adminTasksShown += TASKS_PER_PAGE;
  renderTasksWithPagination(allAdminTasks, 'admin-tasks-list', 'admin-tasks-stats',
    true, adminTasksShown, 'loadMoreAdminTasks');
}

function openCreateTaskModal() {
  editingTaskId = null;
  document.getElementById('modal-task-title').textContent = 'Nueva Tarea / Solicitud';
  document.getElementById('btn-save-task').textContent = 'Crear Tarea';
  ['task-titulo', 'task-descripcion', 'task-cantidad'].forEach(id => document.getElementById(id).value = '');
  document.getElementById('task-producto').value = '';
  document.getElementById('task-unidad').value = 'litros';
  document.getElementById('task-estado').value = 'pendiente';
  document.getElementById('task-prioridad').value = 'media';
  hideError('task-error');
  openModal('modal-task');
}

async function openEditTaskModal(taskId) {
  editingTaskId = taskId;
  document.getElementById('modal-task-title').textContent = 'Editar Tarea';
  document.getElementById('btn-save-task').textContent = 'Guardar Cambios';
  hideError('task-error');
  const { ok, data } = await apiFetch(`/tasks/${taskId}/`);
  if (!ok) { showToast('Error al cargar la tarea.', true); return; }
  document.getElementById('task-titulo').value = data.titulo || '';
  document.getElementById('task-descripcion').value = data.descripcion || '';
  document.getElementById('task-producto').value = data.producto || '';
  document.getElementById('task-cantidad').value = data.cantidad || '';
  document.getElementById('task-unidad').value = data.unidad || 'litros';
  document.getElementById('task-estado').value = data.estado || 'pendiente';
  document.getElementById('task-prioridad').value = data.prioridad || 'media';
  openModal('modal-task');
}

async function saveTask() {
  hideError('task-error');
  const titulo = document.getElementById('task-titulo').value.trim();
  const descripcion = document.getElementById('task-descripcion').value.trim();
  const producto = document.getElementById('task-producto').value;
  const cantidad = parseFloat(document.getElementById('task-cantidad').value) || 0;
  const unidad = document.getElementById('task-unidad').value;
  const estado = document.getElementById('task-estado').value;
  const prioridad = document.getElementById('task-prioridad').value;
  if (!titulo || !descripcion) { showError('task-error', 'El título y la descripción son obligatorios.'); return; }
  const body = { titulo, descripcion, producto, cantidad, unidad, estado, prioridad };
  const btn = document.getElementById('btn-save-task');
  btn.disabled = true;
  const result = editingTaskId
    ? await apiFetch(`/tasks/${editingTaskId}/`, 'PATCH', body)
    : await apiFetch('/tasks/', 'POST', body);
  btn.disabled = false;
  if (result.ok) {
    closeModal('modal-task');
    showToast(editingTaskId ? 'Tarea actualizada.' : 'Tarea creada.');
    loadMyTasks();
  } else {
    showError('task-error', result.data.error || 'Error al guardar.');
  }
}

function confirmDeleteTask(taskId) {
  document.getElementById('confirm-message').textContent = '¿Eliminar esta tarea?';
  deleteCallback = () => deleteTask(taskId);
  openModal('modal-confirm');
}

async function confirmDelete() {
  closeModal('modal-confirm');
  if (deleteCallback) { await deleteCallback(); deleteCallback = null; }
}

async function deleteTask(taskId) {
  const { ok, data } = await apiFetch(`/tasks/${taskId}/`, 'DELETE');
  if (ok) { showToast('Tarea eliminada.'); loadMyTasks(); }
  else { showToast(data.error || 'Error al eliminar.', true); }
}

/* ---- ADMIN USERS ---- */
async function loadAllUsers() {
  const list = document.getElementById('users-list');
  list.innerHTML = '<div class="empty-state"><div class="empty-icon">⏳</div><p>Cargando usuarios...</p></div>';
  const { ok, data } = await apiFetch('/users/all/');
  if (!ok) { list.innerHTML = `<div class="empty-state"><p>Error: ${data.error}</p></div>`; return; }
  if (!data.usuarios || data.usuarios.length === 0) {
    list.innerHTML = '<div class="empty-state"><div class="empty-icon">👥</div><p>No hay usuarios.</p></div>';
    return;
  }
  list.innerHTML = data.usuarios.map(u => {
    const isCurrentUser = u.uid === currentUser.uid;
    const rolClass = u.rol === 'administrador' ? 'role-admin' : 'role-trabajador';
    const avatarContent = u.foto_url
      ? `<img src="${u.foto_url}" alt="${u.nombre}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;"/>`
      : (u.nombre || u.email || '?')[0].toUpperCase();
    return `
      <div class="user-card">
        <div class="user-avatar">${avatarContent}</div>
        <h4>${u.nombre || 'Sin nombre'}</h4>
        <div class="user-email">${u.email}</div>
        <span class="role-badge ${rolClass}">${u.rol === 'administrador' ? 'Administrador' : 'Trabajador'}</span>
        <div class="user-card-actions">
          ${!isCurrentUser ? `
            <button onclick="toggleUserRole('${u.uid}','${u.rol}','${u.nombre}')" class="btn btn-sm btn-warn">
              ${u.rol === 'administrador' ? '⬇️ Trabajador' : '⬆️ Admin'}
            </button>
            <button onclick="confirmDeleteUser('${u.uid}','${u.nombre}')" class="btn btn-sm btn-danger">🗑️</button>
          ` : '<span style="font-size:0.8rem;color:#9e9e9e;">(Tu cuenta)</span>'}
        </div>
      </div>`;
  }).join('');
}

async function toggleUserRole(uid, currentRol, nombre) {
  const newRol = currentRol === 'administrador' ? 'trabajador' : 'administrador';
  const { ok, data } = await apiFetch(`/users/${uid}/update/`, 'PATCH', { rol: newRol });
  if (ok) { showToast(`Rol de ${nombre} → ${newRol}.`); loadAllUsers(); }
  else { showToast(data.error || 'Error.', true); }
}

function confirmDeleteUser(uid, nombre) {
  document.getElementById('confirm-message').textContent = `¿Eliminar al usuario "${nombre}"? También se borrarán sus tareas.`;
  deleteCallback = () => deleteUser(uid);
  openModal('modal-confirm');
}

async function deleteUser(uid) {
  const { ok, data } = await apiFetch(`/users/${uid}/delete/`, 'DELETE');
  if (ok) { showToast('Usuario eliminado.'); loadAllUsers(); }
  else { showToast(data.error || 'Error.', true); }
}

/* ---- INIT ---- */
window.addEventListener('load', () => {
  const saved = localStorage.getItem('ecoUser');
  if (saved) {
    try { currentUser = JSON.parse(saved); afterLogin(); }
    catch { localStorage.removeItem('ecoUser'); }
  }
});

/* ---- IA CHAT REFINADO ---- */

function toggleChat() {
  const chatWindow = document.getElementById('ai-window');
  if (chatWindow) {
    chatWindow.classList.toggle('ai-hidden'); // Usamos ai-hidden para evitar conflictos con .hidden general
  }
}

// Cambié el nombre a handleKeyPress para evitar conflictos con otras funciones de teclado
function handleKeyPress(e) {
  if (e.key === 'Enter') sendMessage();
}

async function sendMessage() {
  const input = document.getElementById('ai-input');
  const msgContainer = document.getElementById('ai-messages');
  const text = input.value.trim();

  if (!text) return;

  // 1. Mostrar mensaje del usuario
  msgContainer.innerHTML += `<div class="msg user">${text}</div>`;
  input.value = '';
  msgContainer.scrollTop = msgContainer.scrollHeight;

  try {
    // CORRECCIÓN: Obtener el token desde currentUser o ecoUser (donde lo guarda tu login)
    const userData = JSON.parse(localStorage.getItem('ecoUser'));
    const token = userData ? userData.idToken : null;

    if (!token) {
        msgContainer.innerHTML += `<div class="msg bot">⚠️ Debes estar logueado para usar la IA.</div>`;
        return;
    }

    const response = await fetch('/api/ia/chat/', { // Usamos ruta relativa por consistencia con tu API_BASE
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ mensaje: text })
    });

    const data = await response.json();

    // 2. Mostrar respuesta de la IA
    const respuestaIA = data.respuesta || "Acción procesada correctamente.";
    msgContainer.innerHTML += `<div class="msg bot">${respuestaIA}</div>`;
    
    // 3. MEJORA: Si la IA menciona que creó o eliminó algo, refrescamos la lista
    const keywords = ['creado', 'eliminado', 'actualizado', 'borrado', 'lista'];
    if (keywords.some(word => respuestaIA.toLowerCase().includes(word))) {
        setTimeout(() => loadMyTasks(), 1500); // Recarga las tareas después de un breve delay
    }

  } catch (error) {
    console.error("Error IA:", error);
    msgContainer.innerHTML += `<div class="msg bot">⚠️ Error al conectar con el servicio de IA.</div>`;
  }
  
  msgContainer.scrollTop = msgContainer.scrollHeight;
}