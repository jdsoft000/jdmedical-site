(() => {
  const form = document.querySelector("[data-contact-form]");
  if (!form) return;

  const to = form.dataset.mailTo || "jdmedical.co.ltd@gmail.com";
  const status = form.querySelector("[data-form-status]");

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const subject = (form.querySelector('[name="subject"]')?.value || "").trim();
    const email = (form.querySelector('[name="email"]')?.value || "").trim();
    const message = (form.querySelector('[name="message"]')?.value || "").trim();

    if (!subject || !email || !message) {
      if (status) status.textContent = form.dataset.msgRequired || "모든 항목을 입력해 주세요.";
      return;
    }

    const body = [
      form.dataset.msgFrom || "보낸 사람",
      email,
      "",
      form.dataset.msgBody || "문의 내용",
      message,
    ].join("\n");

    const mailto = `mailto:${encodeURIComponent(to)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    window.location.href = mailto;
    if (status) status.textContent = form.dataset.msgOpen || "메일 앱이 열립니다. 전송을 완료해 주세요.";
  });
})();
