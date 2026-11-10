const $ = (id) => document.getElementById(id);

function el(tag, props = {}, ...children) {
  const node = Object.assign(document.createElement(tag), props);
  node.append(...children.filter((child) => child !== null && child !== undefined && child !== ""));
  return node;
}

// Ruft die eigene API auf. Ohne gültige Anmeldung geht es zurück zur Anmeldeseite.
async function api(path, { method = "GET", body, redirect = true } = {}) {
  const response = await fetch(path, {
    method,
    headers: body === undefined ? {} : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (response.status === 401 && redirect) {
    location.href = "/anmelden";
    return new Promise(() => {});
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = Array.isArray(data.detail) ? data.detail.map((d) => d.msg.replace(/^Value error, /, "")).join(" ") : data.detail;
    throw new Error(detail || `Fehler ${response.status}`);
  }
  return data;
}

function formatTime(seconds) {
  return new Date(seconds * 1000).toLocaleString("de-DE", { dateStyle: "short", timeStyle: "short" });
}

async function logout() {
  await api("/api/logout", { method: "POST", redirect: false }).catch(() => {});
  location.href = "/anmelden";
}
