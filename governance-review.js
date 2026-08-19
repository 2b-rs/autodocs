(function () {
  "use strict";

  var PUBLIC_WARNING = "GitHub Issues are public and durable evidence. Include only information you intend to publish. GitHub identity proves transport identity, not Management authority, repository Acceptance, or Feature closure.";
  var RESPONSE_SCHEMA = "governance-review-response@v1";
  var RESPONSE_DIGEST_DOMAIN = "governance-review-response-digest@v1";
  var TARGET_REPOSITORY = "2b-rs/autodocs";
  var NEW_ISSUE_URL = "https://github.com/2b-rs/autodocs/issues/new";
  var CANDIDATE_STATUS = "published_pending_response";
  var CANDIDATE_BYTES_SHA256 = "f9afd3801ebff3cfdacfc6e5aa31187888ad6eb4a0eec30cb3ccd9b2035fbf36";
  var ISO8601 = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(Z|[+-]\d{2}:\d{2})$/;
  var AUTHORITY_REFERENCE = /^(?:authority|decision|document):[A-Za-z0-9][A-Za-z0-9._:/#-]{0,254}$/;
  var RELATIONSHIP_REFERENCE = /^\d{4}:\d{4}(?:-\d{2}(?:\.\d{2})?)?$/;
  var CURRENT_CLOSURE_RELATIONSHIP = "0040:0039-01";
  var RESPONSE_FIELDS = [
    "schema", "response_id", "review_id", "review_baseline_commit",
    "task_substantive_ref", "question_set_digest", "public_projection_digest",
    "answers", "transport", "claimed_authority_reference",
    "authority_verification", "client_created_at", "response_digest"
  ];

  function canonical(value) {
    if (Array.isArray(value)) return "[" + value.map(canonical).join(",") + "]";
    if (value && typeof value === "object") {
      return "{" + Object.keys(value).sort().map(function (key) {
        return JSON.stringify(key) + ":" + canonical(value[key]);
      }).join(",") + "}";
    }
    return JSON.stringify(value);
  }

  function utf8(value) { return new TextEncoder().encode(value); }
  function byteLength(value) { return utf8(value).length; }

  function hasUnpairedSurrogate(value) {
    for (var index = 0; index < value.length; index += 1) {
      var code = value.charCodeAt(index);
      if (code >= 0xd800 && code <= 0xdbff) {
        if (index + 1 >= value.length || value.charCodeAt(index + 1) < 0xdc00 || value.charCodeAt(index + 1) > 0xdfff) return true;
        index += 1;
      } else if (code >= 0xdc00 && code <= 0xdfff) return true;
    }
    return false;
  }

  function canonicalInput(value) {
    return typeof value === "string" && value === value.normalize("NFC") && !hasUnpairedSurrogate(value);
  }

  function isRealIso8601(value) {
    var match = ISO8601.exec(value);
    if (!match || !canonicalInput(value)) return false;
    var year = Number(match[1]), month = Number(match[2]), day = Number(match[3]);
    var hour = Number(match[4]), minute = Number(match[5]), second = Number(match[6]);
    var offset = match[7];
    var offsetHour = offset === "Z" ? 0 : Number(offset.slice(1, 3));
    var offsetMinute = offset === "Z" ? 0 : Number(offset.slice(4, 6));
    var leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
    var days = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    return year >= 1 && year <= 9999 && month >= 1 && month <= 12 && day >= 1 && day <= days[month - 1] && hour <= 23 && minute <= 59 && second <= 59 && offsetHour <= 23 && offsetMinute <= 59;
  }

  function safePublicText(value, maxBytes) {
    var textValue = String(value == null ? "" : value);
    var secretOrPrivate = /github_pat_[A-Za-z0-9_]{10,}|gh[pousr]_[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|\bAKIA[0-9A-Z]{16}\b|\b(?:password|token|secret|api[_ -]?key)\s*[:=]\s*\S+|\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b|\b(?:owner_token|request_id|runner_token)\b|(?:\/Users\/|_src\/spec\/|output\/logs\/|TODO-[A-Za-z0-9])/i;
    var authorityClaim = /\bmanagement-approved\b|\bfeature-closed\b|Acceptance\s*:\s*[✓x]|\bauthority[_ -]?verified\b/i;
    if (!textValue || textValue !== textValue.trim() || !canonicalInput(textValue) || byteLength(textValue) > maxBytes || /[\x00-\x1f\x7f\u2028\u2029<>`\[\]{}@]/.test(textValue) || textValue.indexOf("://") !== -1 || /www\./i.test(textValue) || secretOrPrivate.test(textValue) || authorityClaim.test(textValue)) return null;
    return textValue;
  }

  function validateDetail(kind, value, questionId) {
    var detail = String(value == null ? "" : value);
    if (kind === "iso8601") return isRealIso8601(detail) ? detail : null;
    if (kind === "public-text") return safePublicText(detail, 512);
    if (kind === "authority-reference") return canonicalInput(detail) && AUTHORITY_REFERENCE.test(detail) ? detail : null;
    if (kind === "relationship-reference") {
      return canonicalInput(detail) && RELATIONSHIP_REFERENCE.test(detail) && !(questionId === "closure-path" && detail === CURRENT_CLOSURE_RELATIONSHIP) ? detail : null;
    }
    return kind === "none" ? null : null;
  }

  function validateCandidate(candidate) {
    if (!candidate || candidate.schema !== "governance-review-candidate@v1" || candidate.candidate_status !== CANDIDATE_STATUS || !Array.isArray(candidate.questions) || candidate.questions.length !== 5) throw new Error("Governance candidate data is invalid.");
    if (!candidate.transport || candidate.transport.mode !== "github_new_issue" || candidate.transport.target_repository !== TARGET_REPOSITORY || candidate.transport.credential_mode !== "none" || candidate.transport.network_action !== "none" || candidate.transport.new_issue_url !== NEW_ISSUE_URL) throw new Error("Governance candidate transport is invalid.");
    return sha256(canonical(candidate) + "\n").then(function (hash) {
      if (hash !== CANDIDATE_BYTES_SHA256) throw new Error("Governance candidate integrity binding failed.");
    });
  }

  function sha256(value) {
    return globalThis.crypto.subtle.digest("SHA-256", utf8(value)).then(function (buffer) {
      return Array.from(new Uint8Array(buffer), function (byte) {
        return byte.toString(16).padStart(2, "0");
      }).join("");
    });
  }

  function digest(domain, payload) {
    return sha256(canonical({ domain: domain, payload: payload }) + "\n").then(function (hex) {
      return "sha256:" + hex;
    });
  }

  function text(element, value) { element.textContent = value == null ? "" : String(value); }
  function element(tag, className) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    return node;
  }
  function labelFor(input, label) {
    var node = element("label");
    node.appendChild(input);
    var caption = element("span");
    text(caption, label);
    node.appendChild(caption);
    return node;
  }

  function candidateFromPage() {
    var source = document.querySelector('script[type="application/json"][data-governance-candidate]');
    if (!source) throw new Error("Governance candidate data is missing.");
    return JSON.parse(source.textContent);
  }

  function displayDigest(container, label, value) {
    var item = element("li");
    var name = element("strong");
    text(name, label + ": ");
    item.appendChild(name);
    var code = element("code");
    text(code, value);
    item.appendChild(code);
    container.appendChild(item);
  }

  function buildQuestion(question, index) {
    var fieldset = element("fieldset", "governance-question");
    var legend = element("legend");
    text(legend, (index + 1) + ". " + question.title);
    fieldset.appendChild(legend);
    var prompt = element("p", "governance-prompt");
    text(prompt, question.prompt);
    fieldset.appendChild(prompt);
    if (question.guidance) {
      var guidance = element("p", "governance-guidance");
      text(guidance, question.guidance);
      fieldset.appendChild(guidance);
    }

    var options = element("div", "governance-options");
    options.setAttribute("role", "radiogroup");
    var groupLabel = element("span", "sr-only");
    text(groupLabel, "Select an answer");
    options.appendChild(groupLabel);
    question.allowed_answers.forEach(function (answer) {
      var input = document.createElement("input");
      input.type = "radio";
      input.name = "answer-" + question.id;
      input.value = answer.id;
      input.dataset.detailKind = answer.detail_kind;
      input.required = true;
      input.id = "answer-" + question.id + "-" + answer.id;
      options.appendChild(labelFor(input, answer.id));
    });
    fieldset.appendChild(options);

    var detailLabel = element("label", "governance-detail");
    var detailCaption = element("span");
    text(detailCaption, "Public detail (only when the selected answer requires it)");
    detailLabel.appendChild(detailCaption);
    var detail = document.createElement("input");
    detail.type = "text";
    detail.name = "detail-" + question.id;
    detail.disabled = true;
    detail.maxLength = question.allowed_answers.some(function (answer) { return answer.detail_kind === "authority-reference"; }) ? 256 : 512;
    detail.autocomplete = "off";
    detailLabel.appendChild(detail);
    fieldset.appendChild(detailLabel);

    var rationaleLabel = element("label", "governance-rationale");
    var rationaleCaption = element("span");
    text(rationaleCaption, "Public rationale (optional; never private)");
    rationaleLabel.appendChild(rationaleCaption);
    var rationale = document.createElement("textarea");
    rationale.name = "rationale-" + question.id;
    rationale.maxLength = 1200;
    rationale.rows = 3;
    rationale.disabled = !question.public_rationale_allowed;
    rationale.hidden = !question.public_rationale_allowed;
    rationale.autocomplete = "off";
    rationaleLabel.appendChild(rationale);
    fieldset.appendChild(rationaleLabel);

    options.addEventListener("change", function () {
      var selected = fieldset.querySelector('input[type="radio"]:checked');
      var kind = selected && selected.dataset.detailKind;
      var needsDetail = kind && kind !== "none";
      detail.disabled = !needsDetail;
      detail.required = !!needsDetail;
      detail.setCustomValidity("");
      if (!needsDetail) detail.value = "";
      detail.hidden = !needsDetail;
      detailLabel.hidden = !needsDetail;
    });
    detail.addEventListener("input", function () {
      var selected = fieldset.querySelector('input[type="radio"]:checked');
      var kind = selected && selected.dataset.detailKind;
      detail.setCustomValidity(validateDetail(kind, detail.value, question.id) === null ? "Enter a valid public value for the selected answer." : "");
    });
    rationale.addEventListener("input", function () {
      rationale.setCustomValidity(rationale.value && safePublicText(rationale.value, 1200) === null ? "Enter single-line public plain text only." : "");
    });
    detail.hidden = true;
    detailLabel.hidden = true;
    return fieldset;
  }

  function explicitResponse(candidate, form) {
    var fieldsets = form.querySelectorAll(".governance-question");
    var answers = candidate.questions.map(function (question, index) {
      var fieldset = fieldsets[index];
      var selected = fieldset.querySelector('input[type="radio"]:checked');
      var detail = fieldset.querySelector('input[name="detail-' + question.id + '"]');
      var rationale = fieldset.querySelector('textarea[name="rationale-' + question.id + '"]');
      var answerValue = selected ? validateDetail(selected.dataset.detailKind, detail.value, question.id) : null;
      var publicRationale = rationale && rationale.value ? safePublicText(rationale.value, 1200) : null;
      if (!selected || (selected.dataset.detailKind !== "none" && answerValue === null) || (rationale && rationale.value && publicRationale === null)) throw new Error("The public response contains an invalid value.");
      return {
        question_id: question.id,
        selected_answer: selected.value,
        answer_value: answerValue,
        public_rationale: publicRationale
      };
    });
    var response = {
      schema: RESPONSE_SCHEMA,
      response_id: "governance-review-response:browser-candidate",
      review_id: candidate.review_id,
      review_baseline_commit: candidate.review_baseline_commit,
      task_substantive_ref: candidate.task_substantive_ref,
      question_set_digest: candidate.question_set_digest,
      public_projection_digest: candidate.public_projection_digest,
      answers: answers,
      transport: {
        mode: "github_new_issue",
        target_repository: TARGET_REPOSITORY,
        credential_mode: "none",
        status: "prepared",
        identity_scope: "transport-only",
        actor: null,
        issue_receipt: null
      },
      claimed_authority_reference: null,
      authority_verification: {
        status: "unverified",
        verified_deciding_authority: null
      },
      client_created_at: new Date().toISOString(),
      response_digest: ""
    };
    if (Object.keys(response).some(function (key) { return RESPONSE_FIELDS.indexOf(key) === -1; }) || RESPONSE_FIELDS.some(function (key) { return !Object.prototype.hasOwnProperty.call(response, key); })) throw new Error("The response allowlist is incomplete.");
    return response;
  }

  function publicIssueUrl(response) {
    var body = canonical(response) + "\n";
    var url = new URL(NEW_ISSUE_URL);
    url.search = "";
    url.searchParams.set("title", "Governance review response " + response.response_id);
    url.searchParams.set("body", body);
    return url.href;
  }

  function init() {
    var root = document.querySelector("[data-governance-review]");
    if (!root) return;
    var form = root.querySelector("form");
    var questions = root.querySelector("[data-governance-questions]");
    var status = root.querySelector("[data-governance-status]");
    var link = root.querySelector("[data-governance-issue-link]");
    try {
      var candidate = candidateFromPage();
      validateCandidate(candidate).then(function () {
      text(root.querySelector("[data-review-id]"), candidate.review_id);
      text(root.querySelector("[data-baseline]"), candidate.review_baseline_commit);
      text(root.querySelector("[data-substantive-ref]"), candidate.task_substantive_ref);
      var digestList = root.querySelector("[data-digests]");
      displayDigest(digestList, "Question set digest", candidate.question_set_digest);
      displayDigest(digestList, "Public projection digest", candidate.public_projection_digest);
      text(root.querySelector("[data-warning]"), PUBLIC_WARNING);
      candidate.questions.forEach(function (question, index) {
        questions.appendChild(buildQuestion(question, index));
      });
      form.hidden = false;
      root.classList.add("is-initialized");
      text(status, "Candidate initialized. No response has been stored or submitted.");

      form.addEventListener("submit", function (event) {
        event.preventDefault();
        link.hidden = true;
        if (!form.reportValidity()) return;
        var response;
        try {
          response = explicitResponse(candidate, form);
        } catch (error) {
          text(status, "The public response contains an invalid value; nothing was prepared.");
          return;
        }
        digest(RESPONSE_DIGEST_DOMAIN, Object.keys(response).filter(function (key) {
          return key !== "response_digest";
        }).reduce(function (payload, key) {
          payload[key] = response[key];
          return payload;
        }, {})).then(function (responseDigest) {
          response.response_digest = responseDigest;
          link.href = publicIssueUrl(response);
          link.hidden = false;
          text(status, "Prepared locally. The GitHub link is not opened or submitted; identity and authority remain unverified.");
        }).catch(function () {
          text(status, "The response could not be prepared in this browser; nothing was submitted.");
        });
      });
      }).catch(function () {
        text(status, "The governance review candidate could not be initialized; no form is available.");
      });
    } catch (error) {
      text(status, "The governance review candidate could not be initialized; no form is available.");
    }
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
}());
