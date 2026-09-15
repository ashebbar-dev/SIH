(() => {
  "use strict";
  const view = document.body.dataset.view;
  const state = { token: "", latestJob: null, activeJob: null, evidenceJob: null, revealedJob: null, busy: false, previewUrl: null, pollTimer: null, signedAvailable: true, signedDetail: "" };
  const $ = (id) => document.getElementById(id);
  const currentMode = () => ($("mode-signed")?.checked ? "signed" : "public");
  const originHeaders = () => ({ "X-Nishan-Token": state.token });

  async function api(path, options = {}) {
    const response = await fetch(path, { cache: "no-store", ...options });
    const payload = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
    if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
    return payload;
  }

  function setStatus(message, error = false) {
    const element = view === "mobile" ? $("mobile-status") : $("status-message");
    if (!element) return;
    element.textContent = message;
    element.classList.toggle("error", error);
  }

  function controlsDisabled(disabled) {
    state.busy = disabled;
    document.querySelectorAll("button,input[type=file],.mode-switch input").forEach((control) => { control.disabled = disabled; });
  }

  function modeChanged() {
    const signed = currentMode() === "signed";
    $("mode-help").textContent = signed && !state.signedAvailable
      ? `Signed preparation is unavailable: ${state.signedDetail}. Existing-print mode remains fully usable.`
      : signed
      ? "Signed mode traces only fresh Alice/Bob releases prepared on this laptop. A photo remains a visual-only research lead."
      : "The existing printed page is public fixture row 0: useful for reproducibility, but not a real ledger person or signed release.";
    if ($("signed-panel")) $("signed-panel").hidden = !signed;
  }

  function renderRecipients(recipients) {
    const host = $("recipient-cards");
    if (!host) return;
    host.replaceChildren();
    recipients.forEach((recipient) => {
      const card = document.createElement("div");
      card.className = "recipient-card";
      const name = document.createElement("strong");
      name.textContent = recipient.display_name;
      const row = document.createElement("div");
      row.textContent = `Carrier row ${recipient.row}`;
      const session = document.createElement("code");
      session.textContent = recipient.session_id;
      card.append(name, row, session);
      host.append(card);
    });
  }

  function renderFacts(result, duration) {
    const host = $("fact-strip");
    if (!host) return;
    host.replaceChildren();
    const visual = result.channels?.visual || {};
    const signature = result.channels?.signature || {};
    const facts = [
      ["Processing", `${duration ?? result.elapsed_seconds ?? "—"} s`],
      ["Visual score", visual.fixture_row_score ?? (visual.accused_rows?.length ? "threshold crossed" : "no accepted crossing")],
      ["Threshold", visual.threshold ?? "not needed"],
      ["Signature", signature.available ? (signature.valid ? "verified" : "available / not selected") : "unavailable"],
    ];
    facts.forEach(([label, value]) => {
      const box = document.createElement("div");
      box.className = "fact";
      const small = document.createElement("small");
      small.textContent = label;
      const strong = document.createElement("strong");
      strong.textContent = String(value);
      box.append(small, strong);
      host.append(box);
    });
  }

  function resetEvidence(job) {
    const verdict = view === "mobile" ? $("mobile-result") : $("verdict");
    verdict.className = `verdict neutral${view === "mobile" ? " compact" : ""}`;
    verdict.dataset.jobId = job.job_id;
    state.evidenceJob = job.job_id;
    $("result-context").textContent = `${job.filename || "local preparation"} · ${job.mode}`;
    $("result-title").textContent = job.type === "prepare" ? "Preparing signed copies…" : "Inspecting selected bytes…";
    $("result-summary").textContent = job.type === "prepare"
      ? "Creating fresh identities, signed releases, ledger records and witness checkpoints."
      : "The previous verdict has been cleared while this file's evidence is extracted.";
    $("recipient-cards")?.replaceChildren();
    $("fact-strip")?.replaceChildren();
    if ($("details-json")) $("details-json").textContent = "";
    if ($("report-link")) {
      $("report-link").hidden = true;
      $("report-link").removeAttribute("href");
    }
  }

  function revealVerdict(jobId) {
    if (state.revealedJob === jobId) return;
    state.revealedJob = jobId;
    const verdict = view === "mobile" ? $("mobile-result") : $("verdict");
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    verdict.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "center" });
    verdict.focus({ preventScroll: true });
  }

  function renderJobError(message, jobId) {
    const verdict = view === "mobile" ? $("mobile-result") : $("verdict");
    verdict.className = `verdict neutral${view === "mobile" ? " compact" : ""}`;
    verdict.dataset.jobId = jobId;
    $("result-title").textContent = "Input could not be analyzed";
    $("result-summary").textContent = message;
    $("recipient-cards")?.replaceChildren();
    $("fact-strip")?.replaceChildren();
    if ($("report-link")) $("report-link").hidden = true;
    revealVerdict(jobId);
  }

  function renderResult(job) {
    const result = job.result;
    if (!result) return;
    $("result-title").textContent = result.title;
    $("result-summary").textContent = result.summary;
    const verdict = view === "mobile" ? $("mobile-result") : $("verdict");
    verdict.dataset.jobId = job.job_id;
    state.evidenceJob = job.job_id;
    $("result-context").textContent = `${job.filename || "uploaded file"} · ${job.mode}`;
    verdict.className = `verdict ${result.kind === "fixture_match" || result.kind === "verified_session" || result.kind === "known_original" ? "success" : result.kind === "research_lead" ? "lead" : "inconclusive"}${view === "mobile" ? " compact" : ""}`;
    renderRecipients(result.recipients || []);
    renderFacts(result, job.duration_seconds);
    if ($("details-json")) $("details-json").textContent = JSON.stringify({ channels: result.channels, diagnostics: result.diagnostics, limitations: result.limitations }, null, 2);
    if ($("report-link") && job.report_url) {
      $("report-link").href = job.report_url;
      $("report-link").hidden = false;
    }
    if ($("uploaded-preview") && job.preview_url) {
      $("uploaded-preview").src = `${job.preview_url}?v=${encodeURIComponent(job.job_id)}`;
      $("uploaded-preview").hidden = false;
      $("preview-placeholder").hidden = true;
      $("uploaded-preview").parentElement.classList.remove("empty");
    }
    if ($("uploaded-name") && job.filename) $("uploaded-name").textContent = job.filename;
    setStatus(`Finished in ${job.duration_seconds} seconds.`);
    revealVerdict(job.job_id);
  }

  async function watchJob(jobId) {
    state.activeJob = jobId;
    controlsDisabled(true);
    let delay = 250;
    try {
      for (;;) {
        const job = await api(`/api/jobs/${encodeURIComponent(jobId)}`);
        if (job.type === "analysis" && state.evidenceJob !== jobId && job.status !== "done") resetEvidence(job);
        if (job.status === "done") {
          state.latestJob = jobId;
          if (job.type === "prepare") {
            setStatus("Fresh signed Alice and Bob copies are ready.");
            await refreshStatus();
          } else renderResult(job);
          return;
        }
        if (job.status === "error") throw new Error(job.error || "Job failed.");
        setStatus(job.type === "prepare" ? "Creating keys, releases, signatures and witness checkpoints…" : "Extracting real carrier evidence…");
        await new Promise((resolve) => setTimeout(resolve, delay));
        delay = Math.min(900, delay + 100);
      }
    } catch (error) {
      state.latestJob = jobId;
      setStatus(error.message, true);
      renderJobError(error.message, jobId);
    } finally {
      state.activeJob = null;
      controlsDisabled(false);
      modeChanged();
    }
  }

  async function submitFile(file, label = file.name) {
    if (state.busy) return;
    if (!file || file.size > 25 * 1024 * 1024) {
      setStatus("Choose a file no larger than 25 MiB.", true);
      return;
    }
    if (view === "desktop" && file.type.startsWith("image/")) {
      if (state.previewUrl) URL.revokeObjectURL(state.previewUrl);
      state.previewUrl = URL.createObjectURL(file);
      $("uploaded-preview").src = state.previewUrl;
      $("uploaded-preview").hidden = false;
      $("preview-placeholder").hidden = true;
      $("uploaded-preview").parentElement.classList.remove("empty");
      $("uploaded-name").textContent = label;
    }
    try {
      controlsDisabled(true);
      setStatus("Sending selected bytes to the local detector…");
      resetEvidence({ job_id: "pending-upload", type: "analysis", filename: label, mode: currentMode() });
      const submitted = await api(`/api/analyze?mode=${currentMode()}`, {
        method: "POST",
        headers: { ...originHeaders(), "Content-Type": "application/octet-stream", "X-File-Name": encodeURIComponent(label) },
        body: file,
      });
      resetEvidence({ job_id: submitted.job_id, type: "analysis", filename: label, mode: currentMode() });
      await watchJob(submitted.job_id);
    } catch (error) {
      setStatus(error.message, true);
      controlsDisabled(false);
      modeChanged();
    }
  }

  async function tryFixture(id) {
    try {
      controlsDisabled(true);
      setStatus("Loading the real allowlisted fixture…");
      const response = await fetch(`/api/fixtures/${encodeURIComponent(id)}`, { cache: "no-store" });
      if (!response.ok) throw new Error("Fixture could not be loaded.");
      const blob = await response.blob();
      const suffix = blob.type === "application/pdf" ? ".pdf" : ".png";
      const file = new File([blob], `nishan-${id}${suffix}`, { type: blob.type });
      controlsDisabled(false);
      await submitFile(file, file.name);
    } catch (error) {
      setStatus(error.message, true);
      controlsDisabled(false);
      modeChanged();
    }
  }

  function renderSignedFixtures(fixtures) {
    const host = $("signed-fixtures");
    if (!host) return;
    host.replaceChildren();
    fixtures.filter((item) => item.mode === "signed").forEach((fixture) => {
      const use = document.createElement("button");
      use.className = "button primary";
      use.textContent = `Inspect ${fixture.display_name}`;
      use.addEventListener("click", () => tryFixture(fixture.id));
      const download = document.createElement("a");
      download.className = "button secondary";
      download.href = `/api/fixtures/${encodeURIComponent(fixture.id)}`;
      download.textContent = `Download ${fixture.display_name}`;
      host.append(use, download);
    });
  }

  async function prepareSigned() {
    try {
      controlsDisabled(true);
      resetEvidence({ job_id: "pending-prepare", type: "prepare", filename: null, mode: "signed" });
      const submitted = await api("/api/prepare", { method: "POST", headers: originHeaders(), body: null });
      resetEvidence({ job_id: submitted.job_id, type: "prepare", filename: null, mode: "signed" });
      await watchJob(submitted.job_id);
    } catch (error) {
      setStatus(error.message, true);
      controlsDisabled(false);
      modeChanged();
    }
  }

  async function refreshStatus() {
    try {
      const status = await api("/api/status");
      state.token = status.request_token;
      state.signedAvailable = Boolean(status.capabilities.signed);
      state.signedDetail = status.capabilities.signed_detail || "compatible OpenSSL PQC algorithms were not detected";
      renderSignedFixtures(status.fixtures || []);
      if ($("prepare-signed")) {
        $("prepare-signed").disabled = !status.capabilities.signed;
        $("prepare-signed").textContent = status.capabilities.signed ? "Prepare Alice + Bob" : "Signed demo unavailable";
        $("prepare-signed").title = status.capabilities.signed ? "" : status.capabilities.signed_detail;
      }
      modeChanged();
      if (view === "desktop" && status.latest_job_id && status.latest_job_id !== state.latestJob && status.latest_job_id !== state.activeJob) {
        $("incoming-status").lastChild.textContent = " Incoming upload detected";
        watchJob(status.latest_job_id);
      }
    } catch (error) {
      setStatus(`Local server unavailable: ${error.message}`, true);
    }
  }

  function bindDesktop() {
    ["try-original", "try-marked", "try-screenshot"].forEach((id) => $(id).addEventListener("click", () => tryFixture($(id).dataset.fixture)));
    $("prepare-signed").addEventListener("click", prepareSigned);
    $("upload-input").addEventListener("change", (event) => submitFile(event.target.files[0]));
    $("drop-zone").addEventListener("click", (event) => { if (!event.target.closest("label")) $("upload-input").click(); });
    $("drop-zone").addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") $("upload-input").click(); });
    ["dragenter", "dragover"].forEach((name) => $("drop-zone").addEventListener(name, (event) => { event.preventDefault(); $("drop-zone").classList.add("dragging"); }));
    ["dragleave", "drop"].forEach((name) => $("drop-zone").addEventListener(name, (event) => { event.preventDefault(); $("drop-zone").classList.remove("dragging"); }));
    $("drop-zone").addEventListener("drop", (event) => submitFile(event.dataTransfer.files[0]));
    state.pollTimer = setInterval(refreshStatus, 1500);
  }

  function bindMobile() {
    $("camera-input").addEventListener("change", (event) => submitFile(event.target.files[0]));
    $("photo-input").addEventListener("change", (event) => submitFile(event.target.files[0]));
  }

  document.querySelectorAll(".mode-switch input").forEach((input) => input.addEventListener("change", modeChanged));
  modeChanged();
  refreshStatus().then(() => view === "desktop" ? bindDesktop() : bindMobile());
  window.addEventListener("beforeunload", () => { if (state.previewUrl) URL.revokeObjectURL(state.previewUrl); if (state.pollTimer) clearInterval(state.pollTimer); });
})();
