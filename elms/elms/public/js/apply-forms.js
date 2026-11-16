(function () {
  "use strict";

  function value(form, name) {
    var field = form.elements[name];
    return field ? field.value.trim() : "";
  }

  function payloadFrom(form) {
    var kind = form.dataset.applicationKind;
    var payload = {
      application_kind: kind,
      email: value(form, "email"),
      phone: value(form, "phone"),
      consent: Boolean(form.elements.consent && form.elements.consent.checked),
      website: value(form, "website")
    };
    if (kind === "individual") {
      payload.fio = value(form, "fio");
      payload.course = value(form, "course");
      payload.course_ids = [];
    } else {
      payload.company_name = value(form, "company_name");
      payload.inn = value(form, "inn");
      payload.contact_fio = value(form, "contact_fio");
      payload.course_ids = Array.prototype.slice.call(form.elements.course_ids.selectedOptions).map(function (option) {
        return option.value;
      });
      payload.comment = value(form, "comment");
    }
    return payload;
  }

  function setMessage(form, text, state) {
    var message = form.querySelector("[data-form-message]");
    if (message) {
      message.textContent = text;
      message.dataset.state = state || "";
    }
  }

  function submit(form) {
    var button = form.querySelector("button[type=submit]");
    var payload = payloadFrom(form);
    if (!form.reportValidity()) return;
    if (button) button.disabled = true;
    setMessage(form, "Отправляем заявку…", "pending");
    frappe.call({
      method: "elms.applications.api.submit_application",
      type: "POST",
      args: { payload: JSON.stringify(payload) },
      callback: function (response) {
        var result = response && response.message;
        if (!result || !result.tracking_ref) {
          setMessage(form, "Не удалось получить tracking ref. Повторите попытку.", "error");
          if (button) button.disabled = false;
          return;
        }
        form.reset();
        setMessage(form, "Заявка принята. Номер для отслеживания: " + result.tracking_ref, "success");
        if (button) button.disabled = false;
      },
      error: function (error) {
        var message = error && error.message ? error.message : "Заявка не отправлена. Попробуйте позже.";
        setMessage(form, message, "error");
        if (button) button.disabled = false;
      }
    });
  }

  document.addEventListener("submit", function (event) {
    var form = event.target.closest("[data-elms-application-form]");
    if (!form) return;
    event.preventDefault();
    submit(form);
  });

})();
