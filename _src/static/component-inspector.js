(function (root, factory) {
  if (typeof define === "function" && define.amd) {
    define(['score_curator'], factory);
  } else if (typeof module === "object" && module.exports) {
    // For Node.js testing
    var ScoreCurator;
    try {
      ScoreCurator = require('./score_curator.js');
    } catch (e) {
      ScoreCurator = require('../../score_curator.js');
    }
    module.exports = factory(ScoreCurator);
  } else {
    root.ComponentInspector = factory(root.ScoreCurator);
  }
})(typeof self !== "undefined" ? self : this, function (ScoreCurator) {
  "use strict";

  var CUTTLEFISH_STEREOTYPES = [
    "<<Application Software Component>>",
    "<<Sensor-Actuator Component>>",
    "<<Service Component>>",
    "<<ECU Abstraction Component>>",
    "<<Complex Device Driver>>",
    "<<Service Proxy / Adapter>>"
  ];

  function createModal(title, text, onConfirm) {
    var overlay = document.createElement("div");
    overlay.className = "inspector-modal-overlay";
    overlay.style.position = "fixed";
    overlay.style.top = "0"; overlay.style.left = "0";
    overlay.style.width = "100%"; overlay.style.height = "100%";
    overlay.style.backgroundColor = "rgba(0,0,0,0.5)";
    overlay.style.zIndex = "9999";
    overlay.style.display = "flex";
    overlay.style.alignItems = "center";
    overlay.style.justifyContent = "center";

    var modal = document.createElement("div");
    modal.className = "inspector-modal";
    modal.style.backgroundColor = "#fff";
    modal.style.padding = "20px";
    modal.style.borderRadius = "4px";
    modal.style.minWidth = "300px";

    var h3 = document.createElement("h3");
    h3.textContent = title;
    modal.appendChild(h3);

    var p = document.createElement("p");
    p.textContent = text;
    modal.appendChild(p);
    
    // Action selector
    var actionLabel = document.createElement("label");
    actionLabel.textContent = "Aktion: ";
    var actionSelect = document.createElement("select");
    actionSelect.className = "modal-action-select";
    var optDelete = document.createElement("option");
    optDelete.value = "delete_mapping";
    optDelete.textContent = "Delete Mapping";
    var optUnbind = document.createElement("option");
    optUnbind.value = "unbind_feature";
    optUnbind.textContent = "Unbind Feature";
    actionSelect.appendChild(optDelete);
    actionSelect.appendChild(optUnbind);
    actionLabel.appendChild(actionSelect);
    modal.appendChild(actionLabel);
    modal.appendChild(document.createElement("br"));
    modal.appendChild(document.createElement("br"));

    var rationaleInput = document.createElement("textarea");
    rationaleInput.className = "modal-rationale-input";
    rationaleInput.placeholder = "Rationale (required)...";
    rationaleInput.rows = 3;
    rationaleInput.style.width = "100%";
    modal.appendChild(rationaleInput);

    var btnDiv = document.createElement("div");
    btnDiv.style.marginTop = "10px";
    btnDiv.style.textAlign = "right";

    var cancelBtn = document.createElement("button");
    cancelBtn.textContent = "Cancel";
    cancelBtn.style.marginRight = "10px";
    cancelBtn.onclick = function() {
      document.body.removeChild(overlay);
    };
    
    var confirmBtn = document.createElement("button");
    confirmBtn.textContent = "Confirm";
    confirmBtn.className = "btn-danger modal-confirm-btn";
    confirmBtn.onclick = function() {
      var rationale = rationaleInput.value.trim();
      if (!rationale) {
        alert("Rationale is required");
        return;
      }
      onConfirm(actionSelect.value, rationale);
      document.body.removeChild(overlay);
    };

    btnDiv.appendChild(cancelBtn);
    btnDiv.appendChild(confirmBtn);
    modal.appendChild(btnDiv);
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
  }

  function createInspector(container, data, options) {
    options = options || {};
    var onDecision = options.onDecision || function(envelope) {
      var evt = new CustomEvent('curator-decision', { detail: envelope });
      window.dispatchEvent(evt);
    };

    container.innerHTML = "";
    container.className = "component-inspector-panel slide-over";

    var header = document.createElement("header");
    header.innerHTML = "<h2>Component Inspector</h2>";
    container.appendChild(header);

    var propsPanel = document.createElement("div");
    propsPanel.className = "inspector-properties";
    
    var dl = document.createElement("dl");
    function addProp(term, value, id) {
      var dt = document.createElement("dt");
      dt.textContent = term;
      var dd = document.createElement("dd");
      if (id) dd.id = id;
      dd.textContent = value || "N/A";
      dl.appendChild(dt);
      dl.appendChild(dd);
      return dd;
    }

    addProp("Identifier", data.identifier);
    addProp("Name", data.name);
    addProp("Universe", data.universe);
    var stereotypeDd = addProp("Current Stereotype", data.stereotype, "inspector-stereotype-val");
    addProp("Mapped Requirements", data.mapped_requirements ? data.mapped_requirements.join(", ") : "");
    addProp("Implementation Source", data.implementation_source);
    addProp("Status", data.status);

    propsPanel.appendChild(dl);
    container.appendChild(propsPanel);

    var stereoDiv = document.createElement("div");
    stereoDiv.className = "inspector-stereotype-selector";
    stereoDiv.innerHTML = "<label>Change Stereotype:</label> ";
    var select = document.createElement("select");
    var defaultOpt = document.createElement("option");
    defaultOpt.value = "";
    defaultOpt.textContent = "-- Select --";
    select.appendChild(defaultOpt);

    CUTTLEFISH_STEREOTYPES.forEach(function(st) {
      var opt = document.createElement("option");
      opt.value = st;
      opt.textContent = st;
      select.appendChild(opt);
    });

    select.addEventListener("change", function(e) {
      if (e.target.value) {
        data.stereotype = e.target.value;
        stereotypeDd.textContent = e.target.value;
        stereotypeDd.className = "badge-updated stereotype-badge";
      }
    });
    stereoDiv.appendChild(select);
    container.appendChild(stereoDiv);

    var curationDiv = document.createElement("div");
    curationDiv.className = "inspector-curation-actions";
    curationDiv.style.marginTop = "15px";
    
    function addActionBtn(label, outcome) {
      var btn = document.createElement("button");
      btn.textContent = label;
      btn.className = "btn-curation " + outcome;
      btn.style.marginRight = "5px";
      btn.addEventListener("click", function() {
        var rationale = prompt("Rationale for " + label + ":");
        if (!rationale) return;
        var env = ScoreCurator.createDecisionEnvelope({
          proposal_id: data.identifier || "unknown",
          baseline_digest: data.baseline_digest || "000000",
          curator_id: options.curatorId || "inspector-user",
          outcome: outcome,
          rationale: rationale,
          target_canonical_id: data.identifier
        });
        onDecision(env);
      });
      curationDiv.appendChild(btn);
    }

    addActionBtn("Akzeptieren", "accept");
    addActionBtn("Ablehnen", "reject");
    addActionBtn("Überarbeitung anfordern", "request_revision");
    
    container.appendChild(curationDiv);

    var deleteDiv = document.createElement("div");
    deleteDiv.className = "inspector-delete-actions";
    deleteDiv.style.marginTop = "20px";
    
    var deleteBtn = document.createElement("button");
    deleteBtn.textContent = "Löschen / Zuordnung aufheben";
    deleteBtn.className = "btn-danger delete-unbind-btn";
    
    deleteBtn.addEventListener("click", function() {
      createModal("Delete / Unbind", "Please provide a rationale for this action.", function(actionType, rationale) {
        var env = ScoreCurator.createDecisionEnvelope({
            proposal_id: data.identifier || "unknown",
            baseline_digest: data.baseline_digest || "000000",
            curator_id: options.curatorId || "inspector-user",
            outcome: actionType,
            rationale: rationale,
            target_canonical_id: data.identifier
        });
        onDecision(env);
      });
    });

    deleteDiv.appendChild(deleteBtn);
    container.appendChild(deleteDiv);

    return container;
  }

  return {
    CUTTLEFISH_STEREOTYPES: CUTTLEFISH_STEREOTYPES,
    createInspector: createInspector
  };
});
