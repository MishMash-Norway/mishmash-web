/* People network visualization (D3). Data is inlined by
   site/people/network/index.html via Liquid before this file loads. */
(function () {
"use strict";

/* ── Colour scale (one per institution) ──────────────────────────────── */
const PALETTE = [
  "#1f77b4","#d62728","#2ca02c","#9467bd","#8c564b",
  "#e377c2","#7f7f7f","#bcbd22","#17becf","#f08030",
  "#aec7e8","#ff9896","#98df8a","#c5b0d5","#c49c94",
  "#f7b6d2","#c7c7c7","#dbdb8d","#9edae5","#ffbb78",
];
const instIds = INSTITUTIONS.map(i => i.id);
const wpIds = WORK_PACKAGES.map(w => w.id);
const color = d3.scaleOrdinal().domain(instIds).range(PALETTE);
const wpColor = d3.scaleOrdinal().domain(wpIds).range(PALETTE);

const wpById = Object.fromEntries(WORK_PACKAGES.map(w => [w.id, w]));
const wpLeaderSlugs = new Set(WORK_PACKAGES.flatMap(wp => wp.members || []));
const memberRoleLabels = new Set(["member"]);
const wpByMember = {};
WORK_PACKAGES.forEach(wp => {
  wp.members.forEach(slug => {
    (wpByMember[slug] = wpByMember[slug] || []).push(wp.id);
  });
});

function normalizeWpId(value) {
  const raw = String(value || "").trim().toLowerCase();
  if (!raw) return "";
  if (raw.startsWith("wp")) return raw.replace(/\s+/g, "");
  const match = WORK_PACKAGES.find(wp => wp.label.toLowerCase() === raw || wp.id === raw);
  return match ? match.id : "";
}

PEOPLE.forEach(person => {
  (person.wps || []).forEach(label => {
    const wpId = normalizeWpId(label);
    if (!wpId) return;
    const list = wpByMember[person.id] = wpByMember[person.id] || [];
    if (!list.includes(wpId)) list.push(wpId);
  });
});

/* ── Inst name map ──────────────────────────────────────────────────── */
const instName = Object.fromEntries(INSTITUTIONS.map(i => [i.id, i.name]));

/* ── State ──────────────────────────────────────────────────────────── */
let connectionMode = "institutions";
let roleFilter = "all";
let activeTagClusters = new Set();
let activeRawTags = new Set();
let tagMatchMode = "or";
let clusteringEnabled = true;
const DEFAULT_CLUSTER_COUNT = 20;
const MIN_CLUSTER_COUNT = 20;
const MAX_CLUSTER_TAGS = 100;
let clusterCount = DEFAULT_CLUSTER_COUNT;
let clusterModel = [];
let clusterByKey = new Map();
let showHubNodes = true;
let hiddenGroups = new Set();

const tagToGroupExact = new Map();
TAG_GROUPS.forEach(group => {
  (group.tags || []).forEach(tag => tagToGroupExact.set(tag, group.label));
});

function mapTagToGroup(tag) {
  if (tagToGroupExact.has(tag)) return tagToGroupExact.get(tag);
  const lower = tag.toLowerCase();
  for (const group of TAG_GROUPS) {
    for (const pattern of group.patterns || []) {
      if (pattern && lower.includes(String(pattern).toLowerCase())) {
        return group.label;
      }
    }
  }
  return tag;
}

function personTags(p) {
  const set = new Set();
  (p.search_keywords || []).forEach(t => { if (t) set.add(t); });
  (p.tags || []).forEach(t => { if (t) set.add(t); });
  return [...set];
}

function personTagGroups(p) {
  const set = new Set();
  personTags(p).forEach(tag => set.add(mapTagToGroup(tag)));
  return [...set];
}

function normalize(str) {
  return (str || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

function normalizeSpace(str) {
  return String(str || "").replace(/\s+/g, " ").trim();
}

function tagTokens(tag) {
  return normalize(tag)
    .replace(/[^a-z0-9\s-]/g, " ")
    .split(/[\s-]+/)
    .filter(Boolean);
}

function charBigrams(tag) {
  const txt = normalize(tag).replace(/\s+/g, " ");
  if (txt.length < 2) return [txt];
  const out = [];
  for (let i = 0; i < txt.length - 1; i += 1) out.push(txt.slice(i, i + 2));
  return out;
}

function setFromArray(arr) {
  return new Set(arr);
}

function jaccard(a, b) {
  if (!a.size && !b.size) return 1;
  let inter = 0;
  a.forEach(v => { if (b.has(v)) inter += 1; });
  const union = a.size + b.size - inter;
  return union ? inter / union : 0;
}

function dice(a, b) {
  if (!a.size && !b.size) return 1;
  let inter = 0;
  a.forEach(v => { if (b.has(v)) inter += 1; });
  return (2 * inter) / (a.size + b.size || 1);
}

function buildSimilarity(tags) {
  const n = tags.length;
  const matrix = Array.from({ length: n }, () => new Float32Array(n));
  const tokenSets = tags.map(t => setFromArray(tagTokens(t)));
  const bigramSets = tags.map(t => setFromArray(charBigrams(t)));

  for (let i = 0; i < n; i += 1) {
    matrix[i][i] = 1;
    for (let j = i + 1; j < n; j += 1) {
      const tokenSim = jaccard(tokenSets[i], tokenSets[j]);
      const charSim = dice(bigramSets[i], bigramSets[j]);
      const sim = (0.68 * tokenSim) + (0.32 * charSim);
      matrix[i][j] = sim;
      matrix[j][i] = sim;
    }
  }

  return matrix;
}

function chooseRepresentative(memberIdxs, simMatrix) {
  if (memberIdxs.length === 1) return memberIdxs[0];
  let best = memberIdxs[0];
  let bestScore = -1;

  memberIdxs.forEach(candidate => {
    let sum = 0;
    memberIdxs.forEach(other => { sum += simMatrix[candidate][other]; });
    const score = sum / memberIdxs.length;
    if (score > bestScore) {
      bestScore = score;
      best = candidate;
    }
  });

  return best;
}

function hierarchicalCluster(tags, desiredK) {
  if (!tags.length) return [];
  if (desiredK >= tags.length) {
    return tags.map((_, idx) => ({ members: [idx], rep: idx }));
  }

  const simMatrix = buildSimilarity(tags);
  let clusters = tags.map((_, idx) => ({ members: [idx], rep: idx }));

  while (clusters.length > desiredK) {
    let bestI = 0;
    let bestJ = 1;
    let bestSim = -1;

    for (let i = 0; i < clusters.length; i += 1) {
      for (let j = i + 1; j < clusters.length; j += 1) {
        const sim = simMatrix[clusters[i].rep][clusters[j].rep];
        if (sim > bestSim) {
          bestSim = sim;
          bestI = i;
          bestJ = j;
        }
      }
    }

    const mergedMembers = clusters[bestI].members.concat(clusters[bestJ].members);
    const mergedRep = chooseRepresentative(mergedMembers, simMatrix);
    const next = [];

    for (let k = 0; k < clusters.length; k += 1) {
      if (k !== bestI && k !== bestJ) next.push(clusters[k]);
    }
    next.push({ members: mergedMembers, rep: mergedRep });
    clusters = next;
  }

  return clusters;
}

function clusterLabel(memberTags, tagCounts) {
  const sorted = memberTags.slice().sort((a, b) => {
    const countDiff = (tagCounts.get(b) || 0) - (tagCounts.get(a) || 0);
    if (countDiff !== 0) return countDiff;
    return a.localeCompare(b);
  });
  return sorted[0] || "Topic";
}

function slugify(str) {
  return normalize(str).replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "topic";
}

function uniqueKey(base, used) {
  let key = base;
  let i = 2;
  while (used.has(key)) {
    key = base + "-" + i;
    i += 1;
  }
  used.add(key);
  return key;
}

function buildRawTagCounts() {
  const counts = new Map();
  PEOPLE.forEach(p => {
    personTagGroups(p).forEach(tag => {
      const clean = normalizeSpace(tag);
      if (!clean) return;
      counts.set(clean, (counts.get(clean) || 0) + 1);
    });
  });
  return counts;
}

function buildTagClusterModel() {
  const tagCounts = buildRawTagCounts();
  let tags = [...tagCounts.keys()].sort((a, b) => {
    const countDiff = (tagCounts.get(b) || 0) - (tagCounts.get(a) || 0);
    if (countDiff !== 0) return countDiff;
    return a.localeCompare(b);
  });

  if (!tags.length) return [];
  if (tags.length > MAX_CLUSTER_TAGS) tags = tags.slice(0, MAX_CLUSTER_TAGS);

  const maxAllowed = Math.max(1, tags.length);
  const desired = Math.max(MIN_CLUSTER_COUNT, clusterCount);
  const k = Math.max(1, Math.min(desired, maxAllowed));
  const rawClusters = hierarchicalCluster(tags, k);

  const usedKeys = new Set();
  const clusters = rawClusters.map(c => {
    const memberTags = c.members.map(idx => tags[idx]);
    const label = clusterLabel(memberTags, tagCounts);
    const key = uniqueKey(slugify(label), usedKeys);
    const memberNorm = new Set(memberTags.map(normalize));
    const totalCount = memberTags.reduce((acc, tag) => acc + (tagCounts.get(tag) || 0), 0);
    return { key, label, memberTags, memberNorm, totalCount };
  });

  clusters.sort((a, b) => {
    if (b.totalCount !== a.totalCount) return b.totalCount - a.totalCount;
    return a.label.localeCompare(b.label);
  });

  return clusters;
}

function personGroupSet(p) {
  const set = new Set();
  personTagGroups(p).forEach(tag => {
    const clean = normalizeSpace(tag);
    if (clean) set.add(clean);
  });
  return set;
}

function personClusterKeys(p) {
  const normTags = new Set([...personGroupSet(p)].map(normalize));
  const keys = [];
  clusterModel.forEach(cluster => {
    for (const t of cluster.memberNorm) {
      if (normTags.has(t)) {
        keys.push(cluster.key);
        break;
      }
    }
  });
  return keys;
}

function groupMemberTags(groupLabel) {
  const group = TAG_GROUPS.find(g => g.label === groupLabel);
  if (group && group.tags && group.tags.length) return group.tags;
  return [groupLabel];
}

function personWorkPackages(p) {
  return wpByMember[p.id] || [];
}

function personGroups(p) {
  if (connectionMode === "tags") {
    return clusteringEnabled ? personClusterKeys(p) : [...personGroupSet(p)];
  }
  if (connectionMode === "wp") return personWorkPackages(p);
  return (p.institutions || []).filter(i => !hiddenGroups.has(i));
}

function personNodeColor(p) {
  if (connectionMode === "wp") {
    const wpId = personWorkPackages(p)[0];
    return wpId ? wpColor(wpId) : "#999";
  }
  return color((p.institutions || [])[0] || "");
}

function addPersonPersonLinks(links, people, groupFn) {
  const byGroup = {};
  people.forEach(p => {
    groupFn(p).forEach(groupId => {
      (byGroup[groupId] = byGroup[groupId] || []).push(p.id);
    });
  });
  const seen = new Set();
  Object.values(byGroup).forEach(ids => {
    for (let a = 0; a < ids.length; a++) {
      for (let b = a + 1; b < ids.length; b++) {
        const key = [ids[a], ids[b]].sort().join("||");
        if (!seen.has(key)) {
          seen.add(key);
          links.push({ source: ids[a], target: ids[b] });
        }
      }
    }
  });
}

function buildTagList() {
  const counts = buildRawTagCounts();
  return [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function updateModeControls() {
  const hubWrap = document.getElementById("toggle-hub-wrap");
  hubWrap.style.display = connectionMode === "tags" ? "none" : "flex";
  renderTagControls();
}

function renderTagControls() {
  const container = document.getElementById("net-tag-controls");
  if (connectionMode !== "tags") {
    container.style.display = "none";
    container.innerHTML = "";
    return;
  }

  const rawTags = buildTagList();
  if (!rawTags.length) {
    container.style.display = "none";
    container.innerHTML = "";
    return;
  }

  clusterModel = buildTagClusterModel();
  clusterByKey = new Map(clusterModel.map(c => [c.key, c]));
  const validClusterKeys = new Set(clusterModel.map(c => c.key));
  [...activeTagClusters].forEach(key => {
    if (!validClusterKeys.has(key)) activeTagClusters.delete(key);
  });

  const maxClusters = Math.max(1, Math.min(MAX_CLUSTER_TAGS, rawTags.length));
  const minClusters = Math.min(MIN_CLUSTER_COUNT, maxClusters);
  if (clusterCount < minClusters) clusterCount = minClusters;
  if (clusterCount > maxClusters) clusterCount = maxClusters;

  container.style.display = "flex";
  const anyPressed = tagMatchMode === "or" ? "true" : "false";
  const allPressed = tagMatchMode === "and" ? "true" : "false";
  const selectedCount = clusteringEnabled ? activeTagClusters.size : activeRawTags.size;
  const showMatchMode = selectedCount >= 2;

  container.innerHTML = `
    <div class="net-tag-controls-inner">
      <div class="net-tag-row">
        <strong class="net-tag-label">Match:</strong>
        <div class="net-tag-match${showMatchMode ? "" : " is-hidden"}" role="group" aria-label="Tag matching mode">
          <button type="button" id="net-tag-any" class="fbtn tlogic-btn${tagMatchMode === "or" ? " active" : ""}" aria-pressed="${anyPressed}">ANY</button>
          <button type="button" id="net-tag-all" class="fbtn tlogic-btn${tagMatchMode === "and" ? " active" : ""}" aria-pressed="${allPressed}">ALL</button>
        </div>
      </div>

      <div class="net-tag-row">
        <strong class="net-tag-label">Tag groups:</strong>
        <div class="net-tag-match" role="group" aria-label="Enable or disable tag clustering">
          <button type="button" id="net-cluster-on" class="fbtn tlogic-btn${clusteringEnabled ? " active" : ""}" aria-pressed="${clusteringEnabled ? "true" : "false"}">ON</button>
          <button type="button" id="net-cluster-off" class="fbtn tlogic-btn${!clusteringEnabled ? " active" : ""}" aria-pressed="${!clusteringEnabled ? "true" : "false"}">OFF</button>
        </div>
      </div>

      <div class="net-tag-row net-cluster-size-row${clusteringEnabled ? "" : " is-disabled"}">
        <label class="net-tag-label" for="net-cluster-count">Number of Groups</label>
        <input id="net-cluster-count" class="net-cluster-count" type="range" min="${minClusters}" max="${maxClusters}" step="1" value="${clusterCount}" ${clusteringEnabled ? "" : "disabled"}>
        <output id="net-cluster-count-value" class="net-cluster-count-value">${clusterCount}</output>
      </div>

      <p class="net-tag-help">Group similar tags into themes instead of a long list. Selecting a group matches any tag in that theme. Hover a selected group to see its tags. Fewer groups mean more specific topics; more groups mean broader themes.</p>

      <div class="net-clustered-tags-section${clusteringEnabled ? "" : " is-hidden"}">
        <div class="net-tag-chip-list">
          ${clusterModel.map(cluster =>
            `<button type="button" class="fbtn tcluster-btn${activeTagClusters.has(cluster.key) ? " active" : ""}" data-cluster="${escapeHtml(cluster.key)}" title="${escapeHtml(cluster.label)}: ${escapeHtml(cluster.memberTags.join(", "))}">${escapeHtml(cluster.label)} (${cluster.totalCount})</button>`
          ).join("")}
        </div>
      </div>

      <div class="net-all-tags-section${clusteringEnabled ? " is-hidden" : ""}">
        <p class="net-section-label">ALL TAGS</p>
        <div class="net-tag-chip-list">
          ${rawTags.map(([tag, count]) =>
            `<button type="button" class="fbtn traw-btn${activeRawTags.has(tag) ? " active" : ""}" data-tag="${escapeHtml(tag)}">${escapeHtml(tag)} (${count})</button>`
          ).join("")}
        </div>
      </div>
    </div>`;

  container.querySelectorAll(".tcluster-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const key = btn.dataset.cluster;
      if (activeTagClusters.has(key)) activeTagClusters.delete(key);
      else activeTagClusters.add(key);
      render();
    });
  });

  container.querySelectorAll(".traw-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const tag = btn.dataset.tag;
      if (activeRawTags.has(tag)) activeRawTags.delete(tag);
      else activeRawTags.add(tag);
      render();
    });
  });

  const anyBtn = container.querySelector("#net-tag-any");
  const allBtn = container.querySelector("#net-tag-all");
  if (anyBtn) {
    anyBtn.addEventListener("click", () => {
      tagMatchMode = "or";
      render();
    });
  }
  if (allBtn) {
    allBtn.addEventListener("click", () => {
      tagMatchMode = "and";
      render();
    });
  }

  const clusterOnBtn = container.querySelector("#net-cluster-on");
  const clusterOffBtn = container.querySelector("#net-cluster-off");
  if (clusterOnBtn) {
    clusterOnBtn.addEventListener("click", () => {
      clusteringEnabled = true;
      render();
    });
  }
  if (clusterOffBtn) {
    clusterOffBtn.addEventListener("click", () => {
      clusteringEnabled = false;
      render();
    });
  }

  const countInput = container.querySelector("#net-cluster-count");
  const countValue = container.querySelector("#net-cluster-count-value");
  if (countInput) {
    countInput.addEventListener("input", () => {
      const min = parseInt(countInput.min, 10);
      const max = parseInt(countInput.max, 10);
      const parsed = parseInt(countInput.value, 10);
      if (Number.isNaN(parsed)) return;
      clusterCount = Math.max(min, Math.min(max, parsed));
      if (countValue) countValue.textContent = String(clusterCount);
    });

    countInput.addEventListener("change", () => {
      const min = parseInt(countInput.min, 10);
      const max = parseInt(countInput.max, 10);
      const parsed = parseInt(countInput.value, 10);
      if (Number.isNaN(parsed)) return;
      clusterCount = Math.max(min, Math.min(max, parsed));
      if (countValue) countValue.textContent = String(clusterCount);
      render();
    });
  }
}

/* ── Graph builder ──────────────────────────────────────────────────── */
function buildGraph() {
  let people = PEOPLE.slice();

  if (connectionMode === "institutions") {
    people = people.filter(p => {
      const insts = p.institutions || [];
      if (!insts.length) return true;
      return insts.some(i => !hiddenGroups.has(i));
    });
  }

  if (roleFilter !== "all") {
    if (roleFilter === "Work Package") {
      people = people.filter(p => wpLeaderSlugs.has(p.id));
    } else if (roleFilter === "Member") {
      people = people.filter(p => (p.roles || []).some(r => memberRoleLabels.has(String(r).trim().toLowerCase())));
    } else {
      people = people.filter(p => (p.roles || []).some(r => r.includes(roleFilter)));
    }
  }

  if (clusteringEnabled && activeTagClusters.size) {
    const selectedClusters = [...activeTagClusters]
      .map(key => clusterByKey.get(key))
      .filter(Boolean);

    people = people.filter(p => {
      const itemTagSet = new Set([...personGroupSet(p)].map(normalize));
      const clusterMatch = cluster => {
        for (const t of cluster.memberNorm) {
          if (itemTagSet.has(t)) return true;
        }
        return false;
      };
      if (tagMatchMode === "and") return selectedClusters.every(clusterMatch);
      return selectedClusters.some(clusterMatch);
    });
  }

  if (!clusteringEnabled && activeRawTags.size) {
    const selected = [...activeRawTags].map(normalize);
    people = people.filter(p => {
      const groups = new Set([...personGroupSet(p)].map(normalize));
      if (tagMatchMode === "and") return selected.every(tag => groups.has(tag));
      return selected.some(tag => groups.has(tag));
    });
  }

  const nodes = [];
  people.forEach(p => nodes.push({ ...p, nodeType: "person" }));

  const links = [];
  const useHubs = showHubNodes && connectionMode !== "tags";

  if (connectionMode === "institutions") {
    const usedInst = new Set(people.flatMap(p => (p.institutions || []).filter(i => !hiddenGroups.has(i))));
    if (useHubs) {
      INSTITUTIONS.forEach(inst => {
        if (usedInst.has(inst.id)) nodes.push({ ...inst, nodeType: "inst" });
      });
    }
  } else if (connectionMode === "wp" && useHubs) {
    WORK_PACKAGES.forEach(wp => {
      if (hiddenGroups.has(wp.id)) return;
      if (people.some(p => personWorkPackages(p).includes(wp.id))) {
        nodes.push({ id: wp.id, label: wp.label, name: wp.name, url: wp.url, nodeType: "wp" });
      }
    });
  }

  const nodeSet = new Set(nodes.map(n => n.id));

  if (connectionMode === "institutions" && useHubs) {
    people.forEach(p => {
      (p.institutions || []).filter(i => !hiddenGroups.has(i) && nodeSet.has(i)).forEach(inst => {
        links.push({ source: p.id, target: inst });
      });
    });
  } else if (connectionMode === "wp" && useHubs) {
    people.forEach(p => {
      personWorkPackages(p).filter(wpId => !hiddenGroups.has(wpId) && nodeSet.has(wpId)).forEach(wpId => {
        links.push({ source: p.id, target: wpId });
      });
    });
  } else {
    addPersonPersonLinks(links, people, personGroups);
  }

  return { nodes, links };
}

/* ── SVG / zoom setup ─────────────────────────────────────────────── */
const svg = d3.select("#net-svg");
const wrap = document.getElementById("net-wrap");
const panel = document.getElementById("net-panel");
let W = wrap.clientWidth, H = wrap.clientHeight;

function isFullscreen() {
  return document.fullscreenElement === panel;
}

function updateFullscreenUi() {
  const active = isFullscreen();
  const label = active ? "Exit full screen" : "Full screen";
  const icon = active ? "✕" : "⛶";
  ["net-fullscreen-btn", "zoom-fullscreen"].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.setAttribute("aria-pressed", active ? "true" : "false");
    el.setAttribute("aria-label", label);
    el.title = label;
    if (el.classList.contains("zoom-btn")) el.textContent = icon;
    else el.textContent = label;
    el.classList.toggle("active", active);
  });
}

function toggleFullscreen() {
  if (isFullscreen()) {
    document.exitFullscreen();
    return;
  }
  panel.requestFullscreen().catch(() => {});
}

document.getElementById("net-fullscreen-btn").addEventListener("click", toggleFullscreen);
document.getElementById("zoom-fullscreen").addEventListener("click", toggleFullscreen);
document.addEventListener("fullscreenchange", () => {
  updateFullscreenUi();
  render();
});

let zoom = d3.zoom().scaleExtent([0.25, 5]).on("zoom", e => g.attr("transform", e.transform));
svg.call(zoom);

const g = svg.append("g");

// Zoom buttons
document.getElementById("zoom-in")   .onclick = () => svg.transition().duration(300).call(zoom.scaleBy, 1.4);
document.getElementById("zoom-out")  .onclick = () => svg.transition().duration(300).call(zoom.scaleBy, 0.7);
document.getElementById("zoom-reset").onclick = () => svg.transition().duration(400).call(zoom.transform, d3.zoomIdentity);

/* ── Tooltip helpers ─────────────────────────────────────────────── */
const tip = document.getElementById("net-tip");

function showTip(event, d) {
  if (d.nodeType !== "person") return;
  const inst0 = (d.institutions || [])[0];
  const instLabel = inst0 ? (instName[inst0] || inst0) : "";
  const tags = personTagGroups(d);
  const wpLabels = personWorkPackages(d).map(id => wpById[id]?.label).filter(Boolean);
  const imgTag = d.image ? `<img src="${d.image}" alt="" onerror="this.style.display='none'">` : "";
  const roleStr = (d.roles || []).join(", ");
  tip.innerHTML = `${imgTag}
    <div class="tt-name">${escapeHtml(d.name)}</div>
    ${d.position ? `<div class="tt-pos">${escapeHtml(d.position)}</div>` : ""}
    ${instLabel ? `<div class="tt-inst">${escapeHtml(instLabel)}</div>` : ""}
    ${wpLabels.length ? `<div class="tt-wp">${wpLabels.map(escapeHtml).join(", ")}</div>` : ""}
    ${roleStr ? `<div class="tt-role">${escapeHtml(roleStr)}</div>` : ""}
    ${tags.length ? `<div class="tt-tags">${tags.slice(0, 8).map(escapeHtml).join(" · ")}</div>` : ""}
    <div class="tt-click" style="clear:both">Click to view profile →</div>`;
  tip.style.display = "block";
  moveTip(event);
}
function moveTip(event) {
  const r = wrap.getBoundingClientRect();
  let x = event.clientX - r.left + 14, y = event.clientY - r.top - 20;
  if (x + 240 > W) x -= 250;
  if (y + 160 > H) y -= 140;
  tip.style.left = x + "px";
  tip.style.top  = y + "px";
}
function hideTip() { tip.style.display = "none"; }

/* ── Drag handlers ────────────────────────────────────────────────── */
function dragstart(event, d) {
  if (!event.active) sim.alphaTarget(0.3).restart();
  d.fx = d.x; d.fy = d.y;
}
function dragged(event, d) { d.fx = event.x; d.fy = event.y; }
function dragend(event, d) {
  if (!event.active) sim.alphaTarget(0);
  d.fx = null; d.fy = null;
}

/* ── Simulation ──────────────────────────────────────────────────── */
let sim;

/* ── Main render ─────────────────────────────────────────────────── */
function render() {
  W = wrap.clientWidth; H = wrap.clientHeight;

  if (connectionMode === "tags") {
    renderTagControls();
  }

  const { nodes, links } = buildGraph();

  g.selectAll("*").remove();
  if (sim) sim.stop();

  /* links */
  const linkSel = g.append("g").attr("class", "links")
    .selectAll("line").data(links).join("line").attr("class", "n-link");

  /* nodes */
  const nodeSel = g.append("g").attr("class", "nodes")
    .selectAll("g").data(nodes).join("g")
    .attr("class", d => `node node-${d.nodeType}`)
    .call(d3.drag().on("start", dragstart).on("drag", dragged).on("end", dragend))
    .on("mouseover", showTip).on("mousemove", moveTip).on("mouseout", hideTip)
    .on("click", (_, d) => { if (d.url) window.location.href = d.url; });

  /* person circles — pie slices when multiple WPs in wp mode */
  nodeSel.filter(d => d.nodeType === "person").each(function(d) {
    const el = d3.select(this);
    const r = 20;
    if (connectionMode === "wp") {
      const wps = personWorkPackages(d);
      if (wps.length > 1) {
        const arc = d3.arc().innerRadius(0).outerRadius(r);
        const step = (2 * Math.PI) / wps.length;
        wps.forEach((wpId, i) => {
          el.append("path")
            .attr("d", arc({ startAngle: i * step, endAngle: (i + 1) * step }))
            .attr("fill", wpColor(wpId))
            .attr("fill-opacity", 0.88);
        });
        el.append("circle").attr("r", r).attr("fill", "none")
          .attr("stroke", "rgba(255,255,255,0.5)").attr("stroke-width", 1);
      } else {
        el.append("circle").attr("r", r)
          .attr("fill", wps.length ? wpColor(wps[0]) : "#999")
          .attr("fill-opacity", 0.88);
      }
    } else {
      el.append("circle").attr("r", r)
        .attr("fill", personNodeColor(d))
        .attr("fill-opacity", 0.88);
    }
  });

  nodeSel.filter(d => d.nodeType === "person")
    .append("text")
    .attr("y", 30)
    .text(d => d.name.split(" ").pop());

  /* institution rectangles */
  const IW = 100, IH = 30;
  nodeSel.filter(d => d.nodeType === "inst")
    .append("rect")
    .attr("width", IW).attr("height", IH)
    .attr("x", -IW / 2).attr("y", -IH / 2)
    .attr("rx", 6)
    .attr("fill", d => color(d.id));

  nodeSel.filter(d => d.nodeType === "inst")
    .append("text")
    .text(d => instLabel(d.id));

  /* work package rectangles */
  const WPW = 52, WPH = 28;
  nodeSel.filter(d => d.nodeType === "wp")
    .append("rect")
    .attr("width", WPW).attr("height", WPH)
    .attr("x", -WPW / 2).attr("y", -WPH / 2)
    .attr("rx", 6)
    .attr("fill", d => wpColor(d.id));

  nodeSel.filter(d => d.nodeType === "wp")
    .append("text")
    .text(d => d.label);

  const isHubLink = d => {
    const types = new Set([d.source.nodeType, d.target.nodeType]);
    return types.has("inst") || types.has("wp");
  };

  /* force simulation */
  sim = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id(d => d.id)
      .distance(d => isHubLink(d) ? 95 : 70)
      .strength(0.55))
    .force("charge", d3.forceManyBody()
      .strength(d => (d.nodeType === "inst" || d.nodeType === "wp") ? -600 : -160))
    .force("center", d3.forceCenter(W / 2, H / 2).strength(0.08))
    .force("collide", d3.forceCollide()
      .radius(d => {
        if (d.nodeType === "inst") return 62;
        if (d.nodeType === "wp") return 40;
        return 26;
      })
      .strength(0.7))
    .on("tick", () => {
      linkSel
        .attr("x1", d => d.source.x).attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
      nodeSel.attr("transform", d => `translate(${d.x},${d.y})`);
    });

  /* highlight connected on hover */
  const linkedSet = (d) => {
    const s = new Set();
    links.forEach(l => {
      if (l.source.id === d.id) s.add(l.target.id);
      if (l.target.id === d.id) s.add(l.source.id);
    });
    s.add(d.id);
    return s;
  };

  nodeSel.on("mouseover.hi", function(_, d) {
    const connected = linkedSet(d);
    nodeSel.style("opacity", n => connected.has(n.id) ? 1 : 0.22);
    linkSel
      .attr("class", l => (l.source.id === d.id || l.target.id === d.id) ? "n-link hi" : "n-link")
      .style("stroke-opacity", l => (l.source.id === d.id || l.target.id === d.id) ? 1 : 0.12);
  }).on("mouseout.hi", function() {
    nodeSel.style("opacity", 1);
    linkSel.attr("class", "n-link").style("stroke-opacity", null);
  });

  renderLegend(nodes);
}

/* ── Legend ──────────────────────────────────────────────────────── */
function renderLegend(nodes) {
  const leg = document.getElementById("net-legend");
  if (connectionMode === "tags") {
    leg.innerHTML = "";
    return;
  }

  if (connectionMode === "wp") {
    const usedWps = WORK_PACKAGES.filter(wp => nodes.some(n => n.id === wp.id));
    leg.innerHTML = usedWps.map(wp => `
      <div class="leg-item${hiddenGroups.has(wp.id) ? " faded" : ""}" data-group="${wp.id}" title="${escapeHtml(wp.name)}">
        <div class="leg-dot" style="background:${wpColor(wp.id)}"></div>
        <span>${escapeHtml(wp.label)}</span>
      </div>`).join("");
  } else {
    const usedInsts = INSTITUTIONS.filter(i => nodes.some(n => n.id === i.id));
    leg.innerHTML = usedInsts.map(i => `
      <div class="leg-item${hiddenGroups.has(i.id) ? " faded" : ""}" data-group="${i.id}" title="${i.name}">
        <div class="leg-dot" style="background:${color(i.id)}"></div>
        <span>${escapeHtml(instLabel(i.id))}</span>
      </div>`).join("");
  }

  leg.querySelectorAll(".leg-item").forEach(el => {
    el.addEventListener("click", () => {
      const id = el.dataset.group;
      if (hiddenGroups.has(id)) hiddenGroups.delete(id);
      else hiddenGroups.add(id);
      render();
    });
  });
}

/* ── Controls ────────────────────────────────────────────────────── */
document.querySelectorAll(".mbtn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".mbtn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    connectionMode = btn.dataset.mode;
    hiddenGroups.clear();
    if (connectionMode !== "tags") {
      activeTagClusters.clear();
      activeRawTags.clear();
      tagMatchMode = "or";
      clusteringEnabled = true;
      clusterCount = DEFAULT_CLUSTER_COUNT;
    }
    if (connectionMode === "tags") showHubNodes = false;
    else showHubNodes = document.getElementById("toggle-hub").checked;
    updateModeControls();
    render();
  });
});

document.querySelectorAll(".rbtn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".rbtn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    roleFilter = btn.dataset.role;
    render();
  });
});

document.getElementById("toggle-hub").addEventListener("change", function() {
  showHubNodes = this.checked;
  render();
});

/* ── Resize ──────────────────────────────────────────────────────── */
let resizeTimer;
window.addEventListener("resize", () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(render, 200);
});

/* ── Initial render ──────────────────────────────────────────────── */
updateModeControls();
render();

})();
