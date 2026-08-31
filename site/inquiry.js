(() => {
  const board = document.querySelector("[data-inquiry-board]");
  if (!board) return;

  const form = board.querySelector("[data-inquiry-form]");
  const list = board.querySelector("[data-inquiry-list]");
  const status = board.querySelector("[data-inquiry-status]");
  const secretToggle = board.querySelector('[name="is_secret"]');
  const passwordWrap = board.querySelector("[data-password-wrap]");
  const contentField = board.querySelector('[name="content"]');
  const counter = board.querySelector("[data-content-counter]");
  const turnstileMount = board.querySelector("[data-turnstile-mount]");
  const modal = document.querySelector("[data-inquiry-modal]");
  const modalForm = modal?.querySelector("[data-inquiry-unlock-form]");
  const modalStatus = modal?.querySelector("[data-inquiry-modal-status]");
  const modalTitle = modal?.querySelector("[data-inquiry-modal-title]");

  const apiBase = board.dataset.apiBase || "/api/inquiries";
  const formStarted = Date.now();
  const unlocked = new Map();
  let turnstileSiteKey = null;
  let turnstileWidgetId = null;

  const messages = {
    loading: board.dataset.msgLoading || "불러오는 중…",
    empty: board.dataset.msgEmpty || "등록된 문의가 없습니다.",
    submitOk: board.dataset.msgSubmitOk || "문의가 등록되었습니다.",
    submitFail: board.dataset.msgSubmitFail || "등록에 실패했습니다.",
    required: board.dataset.msgRequired || "필수 항목을 입력해 주세요.",
    secretPassword: board.dataset.msgSecretPassword || "비밀글은 비밀번호(4~32자)를 입력해 주세요.",
    unlockFail: board.dataset.msgUnlockFail || "비밀번호가 올바르지 않습니다.",
    deleteOk: board.dataset.msgDeleteOk || "삭제되었습니다.",
    deleteFail: board.dataset.msgDeleteFail || "삭제에 실패했습니다.",
    adminPassword: board.dataset.msgAdminPassword || "관리자 비밀번호",
    secretBadge: board.dataset.msgSecretBadge || "비밀",
    locked: board.dataset.msgLocked || "비밀글입니다. 비밀번호를 입력해 주세요.",
    unlockBtn: board.dataset.msgUnlockBtn || "내용 보기",
    deleteBtn: board.dataset.msgDeleteBtn || "삭제",
    contactLabel: board.dataset.msgContactLabel || "연락처",
    spamRate: board.dataset.msgSpamRate || "등록이 너무 많습니다. 잠시 후 다시 시도해 주세요.",
    spamTiming: board.dataset.msgSpamTiming || "잠시 후 다시 시도해 주세요.",
    turnstileFail: board.dataset.msgTurnstileFail || "보안 확인에 실패했습니다. 새로고침 후 다시 시도해 주세요.",
  };

  let unlockTargetId = null;

  function setStatus(text) {
    if (status) status.textContent = text || "";
  }

  function formatDate(value) {
    if (!value) return "";
    const date = new Date(value.includes("T") ? value : `${value}Z`);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function togglePasswordField() {
    if (!passwordWrap || !secretToggle) return;
    const show = secretToggle.checked;
    passwordWrap.hidden = !show;
    const input = passwordWrap.querySelector("input");
    if (input) input.required = show;
  }

  function updateCounter() {
    if (!contentField || !counter) return;
    counter.textContent = `${contentField.value.length}/300`;
  }

  function getTurnstileToken() {
    if (!turnstileSiteKey || !window.turnstile || turnstileWidgetId === null) return "";
    return window.turnstile.getResponse(turnstileWidgetId) || "";
  }

  function resetTurnstile() {
    if (!turnstileSiteKey || !window.turnstile || turnstileWidgetId === null) return;
    window.turnstile.reset(turnstileWidgetId);
  }

  function loadTurnstileScript() {
    return new Promise((resolve, reject) => {
      if (window.turnstile) {
        resolve();
        return;
      }
      const script = document.createElement("script");
      script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
      script.async = true;
      script.defer = true;
      script.onload = () => resolve();
      script.onerror = () => reject(new Error("turnstile_load_failed"));
      document.head.appendChild(script);
    });
  }

  async function initTurnstile() {
    try {
      const response = await fetch("/api/inquiry-config", { headers: { accept: "application/json" } });
      if (!response.ok) return;
      const data = await response.json();
      if (!data.turnstileSiteKey || !turnstileMount) return;

      turnstileSiteKey = data.turnstileSiteKey;
      await loadTurnstileScript();
      turnstileWidgetId = window.turnstile.render(turnstileMount, {
        sitekey: turnstileSiteKey,
        theme: "dark",
      });
    } catch {
      // Turnstile is optional when keys are not configured.
    }
  }

  function renderItem(item) {
    const unlockedItem = unlocked.get(item.id);
    const isOpen = !item.is_secret || unlockedItem;
    const body = isOpen
      ? `<p class="inquiry-contact"><span>${escapeHtml(messages.contactLabel)}</span> ${escapeHtml((unlockedItem || item).contact)}</p>
         <p class="inquiry-content">${escapeHtml((unlockedItem || item).content).replaceAll("\n", "<br />")}</p>`
      : `<p class="inquiry-locked">${escapeHtml(messages.locked)}</p>
         <button class="btn btn-ghost inquiry-unlock-btn" type="button" data-unlock-id="${item.id}">${escapeHtml(messages.unlockBtn)}</button>`;

    return `<article class="inquiry-item card" data-inquiry-id="${item.id}">
      <button class="inquiry-delete" type="button" data-delete-id="${item.id}" aria-label="${escapeHtml(messages.deleteBtn)}">×</button>
      <header class="inquiry-item-head">
        <div>
          <h2 class="inquiry-title">${escapeHtml(item.title)}</h2>
          <p class="inquiry-meta">
            <span class="inquiry-name">${escapeHtml(item.name)}</span>
            <time datetime="${escapeHtml(item.created_at)}">${escapeHtml(formatDate(item.created_at))}</time>
            ${item.is_secret ? `<span class="inquiry-badge">${escapeHtml(messages.secretBadge)}</span>` : ""}
          </p>
        </div>
      </header>
      <div class="inquiry-body">${body}</div>
    </article>`;
  }

  function renderList(items) {
    if (!list) return;
    if (!items.length) {
      list.innerHTML = `<p class="inquiry-empty">${escapeHtml(messages.empty)}</p>`;
      return;
    }
    list.innerHTML = items.map(renderItem).join("");
  }

  async function loadList() {
    setStatus(messages.loading);
    try {
      const response = await fetch(apiBase, { headers: { accept: "application/json" } });
      if (!response.ok) throw new Error("load_failed");
      const data = await response.json();
      renderList(data.items || []);
      setStatus("");
    } catch {
      setStatus(messages.submitFail);
      if (list) list.innerHTML = "";
    }
  }

  function mapSubmitError(data) {
    if (data?.error === "rate_limited") return messages.spamRate;
    if (data?.error === "spam_timing") return messages.spamTiming;
    if (data?.error === "turnstile_required" || data?.error === "turnstile_failed") {
      return messages.turnstileFail;
    }
    return messages.submitFail;
  }

  async function submitForm(event) {
    event.preventDefault();
    const formData = new FormData(form);
    const payload = {
      name: String(formData.get("name") || "").trim(),
      title: String(formData.get("title") || "").trim(),
      contact: String(formData.get("contact") || "").trim(),
      content: String(formData.get("content") || "").trim(),
      is_secret: Boolean(formData.get("is_secret")),
      password: String(formData.get("password") || "").trim(),
      website: String(formData.get("website") || "").trim(),
      company: String(formData.get("company") || "").trim(),
      form_started: formStarted,
      turnstile_token: getTurnstileToken(),
    };

    if (!payload.name || !payload.title || !payload.contact || !payload.content) {
      setStatus(messages.required);
      return;
    }

    if (payload.is_secret && (payload.password.length < 4 || payload.password.length > 32)) {
      setStatus(messages.secretPassword);
      return;
    }

    try {
      const response = await fetch(apiBase, {
        method: "POST",
        headers: { "content-type": "application/json", accept: "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        setStatus(mapSubmitError(data));
        resetTurnstile();
        return;
      }
      form.reset();
      togglePasswordField();
      updateCounter();
      resetTurnstile();
      setStatus(messages.submitOk);
      await loadList();
    } catch {
      setStatus(messages.submitFail);
      resetTurnstile();
    }
  }

  function openModal(id, title) {
    unlockTargetId = id;
    if (modalTitle) modalTitle.textContent = title;
    if (modalStatus) modalStatus.textContent = "";
    if (modalForm) modalForm.reset();
    if (modal) {
      modal.hidden = false;
      modal.querySelector("input")?.focus();
    }
  }

  function closeModal() {
    unlockTargetId = null;
    if (modal) modal.hidden = true;
  }

  async function unlockPost(event) {
    event.preventDefault();
    if (!unlockTargetId || !modalForm) return;
    const password = String(new FormData(modalForm).get("password") || "").trim();
    if (!password) return;

    try {
      const response = await fetch(`${apiBase}/${unlockTargetId}`, {
        method: "POST",
        headers: { "content-type": "application/json", accept: "application/json" },
        body: JSON.stringify({ password }),
      });
      if (!response.ok) throw new Error("unlock_failed");
      const data = await response.json();
      unlocked.set(unlockTargetId, data.item);
      closeModal();
      await loadList();
    } catch {
      if (modalStatus) modalStatus.textContent = messages.unlockFail;
    }
  }

  async function deletePost(id) {
    const password = window.prompt(messages.adminPassword);
    if (!password) return;

    try {
      const response = await fetch(`${apiBase}/${id}`, {
        method: "DELETE",
        headers: { "content-type": "application/json", accept: "application/json" },
        body: JSON.stringify({ password }),
      });
      if (!response.ok) throw new Error("delete_failed");
      unlocked.delete(id);
      setStatus(messages.deleteOk);
      await loadList();
    } catch {
      setStatus(messages.deleteFail);
    }
  }

  board.addEventListener("click", (event) => {
    const unlockBtn = event.target.closest("[data-unlock-id]");
    if (unlockBtn) {
      const id = Number(unlockBtn.dataset.unlockId);
      const card = unlockBtn.closest("[data-inquiry-id]");
      const title = card?.querySelector(".inquiry-title")?.textContent || "";
      openModal(id, title);
      return;
    }

    const deleteBtn = event.target.closest("[data-delete-id]");
    if (deleteBtn) {
      deletePost(Number(deleteBtn.dataset.deleteId));
    }
  });

  modal?.addEventListener("click", (event) => {
    if (event.target.matches("[data-inquiry-modal-close]")) closeModal();
  });

  secretToggle?.addEventListener("change", togglePasswordField);
  contentField?.addEventListener("input", updateCounter);
  form?.addEventListener("submit", submitForm);
  modalForm?.addEventListener("submit", unlockPost);

  togglePasswordField();
  updateCounter();
  initTurnstile();
  loadList();
})();
