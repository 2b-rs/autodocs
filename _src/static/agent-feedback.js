/**
 * _src/static/agent-feedback.js -- Client-side UX validation and preview logic (Task 0046-01.01).
 *
 * Implements:
 * - Real-time character count and boundary checking (max 4000 chars)
 * - Dynamic attribution policy handling (Identified vs. Anonymous)
 * - Safe client-side HTML preview rendering (XSS protection via DOM text nodes / strict escaping)
 * - Form validation and AJAX / JSON envelope submission handling
 */

(function () {
  'use strict';

  const MAX_FEEDBACK_LENGTH = 4000;
  const MAX_AGENT_NAME_LENGTH = 120;
  const MAX_BASELINE_LENGTH = 128;
  const MAX_SUBMITTER_LENGTH = 120;

  const AGENT_REGEX = /^[a-zA-Z0-9][a-zA-Z0-9_\-\.]*$/;
  const BASELINE_REGEX = /^[a-zA-Z0-9_\-\.\:@]+$/;

  // DOM Elements
  const form = document.getElementById('agentFeedbackForm');
  if (!form) return;

  const targetInput = document.getElementById('target_agent');
  const baselineInput = document.getElementById('observed_baseline');
  const categorySelect = document.getElementById('category');
  const attrIdentified = document.getElementById('attr_identified');
  const attrAnonymous = document.getElementById('attr_anonymous');
  const submitterGroup = document.getElementById('submitter_group');
  const submitterInput = document.getElementById('submitter');
  const submitterReq = document.getElementById('submitter_req_indicator');
  const visibilitySelect = document.getElementById('consent_visibility');
  const textInput = document.getElementById('feedback_text');
  const charCounter = document.getElementById('char_counter');
  const btnPreview = document.getElementById('btnPreview');
  const btnSubmit = document.getElementById('btnSubmit');
  const previewContainer = document.getElementById('previewContainer');
  const statusAlert = document.getElementById('statusAlert');

  /**
   * Escape HTML entities to prevent XSS injection.
   */
  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  /**
   * Show status message banner.
   */
  function showStatus(message, type) {
    if (!statusAlert) return;
    statusAlert.className = 'form-status-alert ' + (type === 'error' ? 'error' : 'success');
    statusAlert.textContent = message;
    statusAlert.style.display = 'block';
    statusAlert.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  /**
   * Clear status message banner.
   */
  function clearStatus() {
    if (!statusAlert) return;
    statusAlert.textContent = '';
    statusAlert.style.display = 'none';
    statusAlert.className = 'form-status-alert';
  }

  /**
   * Update character counter and highlight limits.
   */
  function updateCharCount() {
    if (!textInput || !charCounter) return;
    const len = textInput.value.length;
    charCounter.textContent = len + ' / ' + MAX_FEEDBACK_LENGTH + ' characters';

    charCounter.classList.remove('limit-near', 'limit-reached');
    if (len >= MAX_FEEDBACK_LENGTH) {
      charCounter.classList.add('limit-reached');
    } else if (len >= MAX_FEEDBACK_LENGTH * 0.9) {
      charCounter.classList.add('limit-near');
    }
  }

  /**
   * Handle attribution radio change (Identified vs. Anonymous).
   */
  function handleAttributionChange() {
    const isAnonymous = attrAnonymous && attrAnonymous.checked;
    if (submitterGroup) {
      if (isAnonymous) {
        submitterGroup.style.display = 'none';
        if (submitterInput) {
          submitterInput.value = '';
          submitterInput.removeAttribute('required');
        }
        if (submitterReq) submitterReq.style.display = 'none';
      } else {
        submitterGroup.style.display = 'block';
        if (submitterInput) {
          submitterInput.setAttribute('required', 'required');
        }
        if (submitterReq) submitterReq.style.display = 'inline';
      }
    }
  }

  /**
   * Validate current form values and return sanitized data or throw error.
   */
  function validateForm() {
    const target = targetInput ? targetInput.value.trim() : '';
    const baseline = baselineInput ? baselineInput.value.trim() : '';
    const category = categorySelect ? categorySelect.value : 'general';
    const isAnonymous = attrAnonymous && attrAnonymous.checked;
    const attribution = isAnonymous ? 'anonymous' : 'identified';
    const submitter = (!isAnonymous && submitterInput) ? submitterInput.value.trim() : null;
    const visibility = visibilitySelect ? visibilitySelect.value : 'private';
    const text = textInput ? textInput.value.trim() : '';

    if (!target) {
      throw new Error('Target agent is required.');
    }
    if (target.length > MAX_AGENT_NAME_LENGTH || !AGENT_REGEX.test(target)) {
      throw new Error('Target agent must contain only letters, numbers, hyphens, and dots (max 120 chars).');
    }

    if (!baseline) {
      throw new Error('Observed baseline revision is required.');
    }
    if (baseline.length > MAX_BASELINE_LENGTH || !BASELINE_REGEX.test(baseline)) {
      throw new Error('Observed baseline contains invalid characters or exceeds 128 characters.');
    }

    if (!isAnonymous) {
      if (!submitter) {
        throw new Error('Submitter name / ID is required for identified feedback.');
      }
      if (submitter.length > MAX_SUBMITTER_LENGTH || !AGENT_REGEX.test(submitter)) {
        throw new Error('Submitter identifier must contain only letters, numbers, hyphens, and dots (max 120 chars).');
      }
    }

    if (!text) {
      throw new Error('Feedback content cannot be empty.');
    }
    if (text.length > MAX_FEEDBACK_LENGTH) {
      throw new Error('Feedback content exceeds maximum length of ' + MAX_FEEDBACK_LENGTH + ' characters.');
    }

    return {
      target_agent: target,
      observed_baseline: baseline,
      category: category,
      attribution: attribution,
      submitter: submitter,
      consent_visibility: visibility,
      feedback_text: text
    };
  }

  /**
   * Render preview in DOM safely.
   */
  function renderPreview(data) {
    if (!previewContainer) return;

    const isAnonymous = data.attribution === 'anonymous';
    const submitterDisplay = isAnonymous ? '[Anonymous Submitter]' : data.submitter;
    const authorityBadge = isAnonymous
      ? '<span class="badge badge-warning">No Approval Authority (Anonymous Policy)</span>'
      : '<span class="badge badge-success">Eligible for Review</span>';

    const warnings = [];
    if (data.feedback_text.length > 2000) {
      warnings.push('Feedback text is lengthy; ensure it is focused on specific behavioral or factual changes.');
    }
    const lower = data.feedback_text.toLowerCase();
    if (lower.includes('api_key') || lower.includes('token') || lower.includes('secret')) {
      warnings.push('Warning: text may contain sensitive credential keywords; verify no secrets are submitted.');
    }

    let warnHtml = '';
    if (warnings.length > 0) {
      const items = warnings.map(w => '<li>' + escapeHtml(w) + '</li>').join('');
      warnHtml = '<div class="feedback-warnings" role="alert"><ul class="warning-list">' + items + '</ul></div>';
    }

    const html = '<div class="agent-feedback-preview" role="region" aria-label="Feedback Submission Preview">' +
      '<div class="preview-header">' +
        '<h3 class="preview-title">Submission Preview</h3>' +
        '<div class="preview-authority-status">' + authorityBadge + '</div>' +
      '</div>' +
      warnHtml +
      '<dl class="preview-meta-grid">' +
        '<div class="meta-item"><dt>Target Agent:</dt><dd><code>' + escapeHtml(data.target_agent) + '</code></dd></div>' +
        '<div class="meta-item"><dt>Observed Baseline:</dt><dd><code>' + escapeHtml(data.observed_baseline) + '</code></dd></div>' +
        '<div class="meta-item"><dt>Category:</dt><dd>' + escapeHtml(data.category.replace(/_/g, ' ')) + '</dd></div>' +
        '<div class="meta-item"><dt>Attribution:</dt><dd>' + escapeHtml(data.attribution) + ' (' + escapeHtml(submitterDisplay) + ')</dd></div>' +
        '<div class="meta-item"><dt>Visibility:</dt><dd>' + escapeHtml(data.consent_visibility) + '</dd></div>' +
        '<div class="meta-item"><dt>Length:</dt><dd>' + data.feedback_text.length + ' characters</dd></div>' +
      '</dl>' +
      '<div class="preview-body">' +
        '<div class="preview-body-label">Feedback Content:</div>' +
        '<pre class="preview-content-box" tabindex="0">' + escapeHtml(data.feedback_text) + '</pre>' +
      '</div>' +
    '</div>';

    previewContainer.innerHTML = html;
    previewContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  // Event Listeners
  if (textInput) {
    textInput.addEventListener('input', updateCharCount);
    updateCharCount();
  }

  if (attrIdentified) attrIdentified.addEventListener('change', handleAttributionChange);
  if (attrAnonymous) attrAnonymous.addEventListener('change', handleAttributionChange);
  handleAttributionChange();

  if (btnPreview) {
    btnPreview.addEventListener('click', function () {
      clearStatus();
      try {
        const validatedData = validateForm();
        renderPreview(validatedData);
      } catch (err) {
        showStatus(err.message, 'error');
      }
    });
  }

  form.addEventListener('submit', function (evt) {
    evt.preventDefault();
    clearStatus();

    let validatedData;
    try {
      validatedData = validateForm();
    } catch (err) {
      showStatus(err.message, 'error');
      return;
    }

    if (btnSubmit) btnSubmit.disabled = true;

    // Send payload as JSON
    const actionUrl = form.getAttribute('action') || '/api/feedback';
    fetch(actionUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(validatedData)
    })
    .then(function (res) {
      if (!res.ok) {
        return res.json().then(function (j) {
          throw new Error(j.error || ('Server returned status ' + res.status));
        }).catch(function (e) {
          throw new Error(e.message || ('Server returned status ' + res.status));
        });
      }
      return res.json();
    })
    .then(function (result) {
      showStatus('Feedback successfully recorded with ID: ' + (result.envelope_id || 'OK'), 'success');
      renderPreview(validatedData);
      form.reset();
      updateCharCount();
      handleAttributionChange();
    })
    .catch(function (err) {
      // In standalone client preview mode or offline fallback, render preview and note
      renderPreview(validatedData);
      showStatus('Note: Envelope generated and validated successfully (' + err.message + ')', 'error');
    })
    .finally(function () {
      if (btnSubmit) btnSubmit.disabled = false;
    });
  });

})();
