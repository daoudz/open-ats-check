/* ═══════════════════════════════════════════════════════════
   Open ATS Check — Frontend Application Logic
   ═══════════════════════════════════════════════════════════ */

// ─── State ───
let selectedFiles = {
    'ats': null,
    'compare-cv': null,
    'compare-jd': null,
};

let lastATSData = null;
let lastCompareData = null;

// ─── Tab Switching ───
function switchTab(tab) {
    document.querySelectorAll('.tab').forEach(t => {
        t.classList.remove('active');
        t.setAttribute('aria-selected', 'false');
    });
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));

    document.getElementById('tab-' + tab).classList.add('active');
    document.getElementById('tab-' + tab).setAttribute('aria-selected', 'true');
    document.getElementById('panel-' + tab).classList.add('active');
}

// ─── Drag & Drop / File Selection Setup ───
function setupDropzone(id, fileInputId, fileKey) {
    const zone = document.getElementById(id);
    const input = document.getElementById(fileInputId);

    if (!zone || !input) return;

    // Click on the upload area opens file picker (but NOT on clear button or file preview)
    zone.addEventListener('click', (e) => {
        // Don't trigger file picker if clicking on clear button, file preview, or upload-link
        if (e.target.closest('.btn-clear') || e.target.closest('.upload-link')) return;
        if (e.target.closest('.file-preview')) return;
        input.click();
    });

    zone.addEventListener('dragover', (e) => { e.preventDefault(); zone.classList.add('dragover'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            handleFileSelect(fileKey, e.dataTransfer.files[0]);
        }
    });

    input.addEventListener('change', () => {
        if (input.files.length) {
            handleFileSelect(fileKey, input.files[0]);
        }
    });
}

function handleFileSelect(key, file) {
    const allowed = ['pdf', 'docx', 'doc', 'txt', 'rtf', 'html', 'htm'];
    const ext = file.name.split('.').pop().toLowerCase();
    if (!allowed.includes(ext)) {
        showToast('Unsupported file type. Please use PDF, DOCX, TXT, RTF, or HTML.');
        return;
    }
    if (file.size > 10 * 1024 * 1024) {
        showToast('File too large. Maximum size is 10 MB.');
        return;
    }

    selectedFiles[key] = file;

    // Show preview
    const preview = document.getElementById('preview-' + key);
    const fname = document.getElementById('fname-' + key);
    if (preview && fname) {
        fname.textContent = file.name;
        preview.hidden = false;
    }

    updateButtonStates();
}

function clearFile(key) {
    selectedFiles[key] = null;

    // Hide preview
    const preview = document.getElementById('preview-' + key);
    if (preview) preview.hidden = true;

    // Clear the file input value so the same file can be re-selected
    const inputMap = {
        'ats': 'file-ats',
        'compare-cv': 'file-compare-cv',
        'compare-jd': 'file-compare-jd',
    };
    const input = document.getElementById(inputMap[key]);
    if (input) input.value = '';

    updateButtonStates();
}

function updateButtonStates() {
    const btnAnalyze = document.getElementById('btn-analyze');
    const btnCompare = document.getElementById('btn-compare');

    if (btnAnalyze) btnAnalyze.disabled = !selectedFiles['ats'];
    if (btnCompare) {
        const hasCV = !!selectedFiles['compare-cv'];
        const hasJD = !!selectedFiles['compare-jd'] || document.getElementById('jd-text').value.trim().length > 20;
        btnCompare.disabled = !(hasCV && hasJD);
    }
}

// ─── Reset Panel ───
function resetPanel(panel) {
    if (panel === 'ats') {
        clearFile('ats');
        const results = document.getElementById('results-ats');
        if (results) { results.hidden = true; results.innerHTML = ''; }
        document.getElementById('btn-reset-ats').hidden = true;
        lastATSData = null;
    } else if (panel === 'compare') {
        clearFile('compare-cv');
        clearFile('compare-jd');
        const jdText = document.getElementById('jd-text');
        if (jdText) jdText.value = '';
        const results = document.getElementById('results-compare');
        if (results) { results.hidden = true; results.innerHTML = ''; }
        document.getElementById('btn-reset-compare').hidden = true;
        lastCompareData = null;
    }
    updateButtonStates();
}

// ─── API Calls ───
async function runAnalysis() {
    const btn = document.getElementById('btn-analyze');
    const resultsEl = document.getElementById('results-ats');
    setLoading(btn, true);
    resultsEl.hidden = true;

    const formData = new FormData();
    formData.append('resume', selectedFiles['ats']);

    try {
        const resp = await fetch('/api/analyze', {
            method: 'POST',
            body: formData,
            headers: { 'Cache-Control': 'no-cache' },
        });
        const data = await resp.json();
        console.log('[ATS Analysis Response]', data);

        if (!resp.ok) {
            showToast(data.error || 'Analysis failed.');
            return;
        }

        lastATSData = data;
        renderATSResults(data, resultsEl);
        resultsEl.hidden = false;
        document.getElementById('btn-reset-ats').hidden = false;
        resultsEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (err) {
        showToast('Network error. Please try again.');
        console.error(err);
    } finally {
        setLoading(btn, false);
    }
}

async function runComparison() {
    const btn = document.getElementById('btn-compare');
    const resultsEl = document.getElementById('results-compare');
    setLoading(btn, true);
    resultsEl.hidden = true;

    const formData = new FormData();
    formData.append('resume', selectedFiles['compare-cv']);

    if (selectedFiles['compare-jd']) {
        formData.append('job_description_file', selectedFiles['compare-jd']);
    }
    const jdText = document.getElementById('jd-text').value.trim();
    if (jdText) {
        formData.append('job_description', jdText);
    }

    try {
        const resp = await fetch('/api/compare', {
            method: 'POST',
            body: formData,
            headers: { 'Cache-Control': 'no-cache' },
        });
        const data = await resp.json();
        console.log('[Compare Response]', data);

        if (!resp.ok) {
            showToast(data.error || 'Comparison failed.');
            return;
        }

        lastCompareData = data;
        renderCompareResults(data, resultsEl);
        resultsEl.hidden = false;
        document.getElementById('btn-reset-compare').hidden = false;
        resultsEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (err) {
        showToast('Network error. Please try again.');
        console.error(err);
    } finally {
        setLoading(btn, false);
    }
}

function setLoading(btn, loading) {
    const text = btn.querySelector('.btn-text');
    const loader = btn.querySelector('.btn-loader');
    if (loading) {
        text.hidden = true;
        loader.hidden = false;
        btn.disabled = true;
    } else {
        text.hidden = false;
        loader.hidden = true;
        btn.disabled = false;
    }
}

// ─── Render ATS Results ───
function renderATSResults(data, container) {
    const fileInfo = data.file_info || {};
    const overall = data.overall_score || 0;
    const sections = data.sections || [];

    // Collect all recommendations
    let allRecos = [];
    sections.forEach(s => {
        (s.recommendations || []).forEach(r => {
            allRecos.push({ text: r, section: s.name });
        });
    });

    container.innerHTML = `
        ${renderFileInfo(fileInfo)}
        ${renderTextPreview(data.text_preview)}
        ${renderScoreHero(overall, 'ATS Compatibility Score')}
        <div class="section-grid">
            ${sections.map(s => renderSectionCard(s)).join('')}
        </div>
        ${allRecos.length ? renderRecommendations(allRecos) : ''}
        <div class="export-bar">
            <button class="btn-export" onclick="exportReport('ats')">
                📥 Export Report
            </button>
        </div>
    `;

    // Animate after render
    requestAnimationFrame(() => {
        animateScore(overall);
        animateBars();
    });
}

// ─── Render Compare Results ───
function renderCompareResults(data, container) {
    const comparison = data.comparison || {};
    const atsAnalysis = data.ats_analysis || {};
    const fileInfo = data.file_info || {};
    const matchScore = comparison.match_score || 0;
    const sections = atsAnalysis.sections || [];

    container.innerHTML = `
        ${renderFileInfo(fileInfo)}
        ${renderTextPreview(data.text_preview)}
        ${renderScoreHero(matchScore, 'Job Match Score')}
        ${renderProsConsCols(comparison.pros || [], comparison.cons || [])}
        ${renderKeywordAnalysis(comparison.keyword_analysis || {})}
        ${comparison.recommendations && comparison.recommendations.length
            ? renderCompareRecommendations(comparison.recommendations)
            : ''}
        <h3 style="color:var(--text-heading);margin:28px 0 14px;font-size:16px;">📊 Full ATS Breakdown</h3>
        <div class="section-grid">
            ${sections.map(s => renderSectionCard(s)).join('')}
        </div>
        <div class="export-bar">
            <button class="btn-export" onclick="exportReport('compare')">
                📥 Export Report
            </button>
        </div>
    `;

    requestAnimationFrame(() => {
        animateScore(matchScore);
        animateBars();
    });
}

// ─── Render Helpers ───
function renderFileInfo(info) {
    return `
        <div class="file-info">
            <span>📎 <strong>${escapeHtml(info.filename || 'Resume')}</strong></span>
            <span>Format: <strong>${(info.format || '').toUpperCase()}</strong></span>
            <span>Words: <strong>${info.word_count || '—'}</strong></span>
            <span>Chars: <strong>${info.text_length || '—'}</strong></span>
        </div>
    `;
}

function renderTextPreview(preview) {
    if (!preview) return '';
    return `
        <div class="text-preview">
            <div class="text-preview-header" onclick="this.parentElement.classList.toggle('expanded')">
                <span>📝 Extracted Text Preview</span>
                <span class="text-preview-toggle">▼</span>
            </div>
            <div class="text-preview-content">
                <pre>${escapeHtml(preview)}</pre>
            </div>
        </div>
    `;
}

function renderScoreHero(score, label) {
    return `
        <div class="score-hero">
            <h2>${label}</h2>
            <div class="score-circle-wrap">
                <svg class="score-circle-svg" viewBox="0 0 180 180">
                    <defs>
                        <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="#6366f1"/>
                            <stop offset="100%" stop-color="#34d399"/>
                        </linearGradient>
                    </defs>
                    <circle class="score-circle-bg" cx="90" cy="90" r="80"/>
                    <circle class="score-circle-fg" id="score-ring" cx="90" cy="90" r="80"/>
                </svg>
                <div class="score-value" id="score-number">0<small>/100</small></div>
            </div>
            <p class="score-label">
                ${score >= 70 ? '🟢 <strong>Good</strong> — Your resume is ATS-friendly'
            : score >= 40 ? '🟡 <strong>Needs Improvement</strong> — Several areas to optimize'
                : '🔴 <strong>Low Score</strong> — Significant improvements needed'}
            </p>
        </div>
    `;
}

function renderSectionCard(section) {
    const findings = section.findings || [];
    return `
        <div class="section-card" onclick="this.classList.toggle('expanded')">
            <div class="section-card-header">
                <span class="section-icon">${section.icon || '📋'}</span>
                <span class="section-title">${escapeHtml(section.name)}</span>
                <span class="section-score">${Math.round(section.score)}</span>
            </div>
            <div class="section-bar-bg">
                <div class="section-bar-fill" data-width="${section.score}"></div>
            </div>
            <ul class="section-findings">
                ${findings.map(f => `<li>${escapeHtml(f)}</li>`).join('')}
            </ul>
        </div>
    `;
}

function renderRecommendations(recos) {
    return `
        <div class="reco-panel">
            <h3>💡 Recommendations</h3>
            <ul class="reco-list">
                ${recos.map((r, i) => {
        const prio = i < 3 ? 'high' : i < 6 ? 'medium' : 'low';
        return `<li class="reco-item ${prio}"><strong>${escapeHtml(r.section)}:</strong> ${escapeHtml(r.text)}</li>`;
    }).join('')}
            </ul>
        </div>
    `;
}

function renderCompareRecommendations(recos) {
    return `
        <div class="reco-panel">
            <h3>💡 Recommendations to Improve Match</h3>
            <ul class="reco-list">
                ${recos.map(r => {
        const prio = r.priority || 'medium';
        const icon = r.action === 'add' ? '➕' : r.action === 'remove' ? '➖' : '🔧';
        return `<li class="reco-item ${prio}">${icon} ${escapeHtml(r.text)}</li>`;
    }).join('')}
            </ul>
        </div>
    `;
}

function renderProsConsCols(pros, cons) {
    return `
        <div class="proscons-grid">
            <div class="proscons-col pros">
                <h3>✅ Strengths</h3>
                <ul class="proscons-list">
                    ${pros.length ? pros.map(p => `<li>${escapeHtml(p)}</li>`).join('')
            : '<li style="color:var(--text-muted)">No specific strengths detected</li>'}
                </ul>
            </div>
            <div class="proscons-col cons">
                <h3>❌ Gaps</h3>
                <ul class="proscons-list">
                    ${cons.length ? cons.map(c => `<li>${escapeHtml(c)}</li>`).join('')
            : '<li style="color:var(--text-muted)">No critical gaps detected</li>'}
                </ul>
            </div>
        </div>
    `;
}

function renderKeywordAnalysis(ka) {
    const matched = ka.matched_skills || [];
    const missing = ka.missing_skills || [];
    const extra = ka.extra_skills || [];

    if (!matched.length && !missing.length && !extra.length) return '';

    return `
        <div class="keyword-section">
            <h3>🔑 Keyword Analysis</h3>
            ${matched.length ? `
                <div class="keyword-row">
                    <div class="keyword-row-label">Matched Skills (${matched.length})</div>
                    <div class="pills">${matched.map(s => `<span class="pill matched">${escapeHtml(s)}</span>`).join('')}</div>
                </div>
            ` : ''}
            ${missing.length ? `
                <div class="keyword-row">
                    <div class="keyword-row-label">Missing Skills (${missing.length})</div>
                    <div class="pills">${missing.map(s => `<span class="pill missing">${escapeHtml(s)}</span>`).join('')}</div>
                </div>
            ` : ''}
            ${extra.length ? `
                <div class="keyword-row">
                    <div class="keyword-row-label">Additional Skills You Have (${extra.length})</div>
                    <div class="pills">${extra.slice(0, 20).map(s => `<span class="pill extra">${escapeHtml(s)}</span>`).join('')}</div>
                </div>
            ` : ''}
        </div>
    `;
}

// ─── Export Report ───
function exportReport(type) {
    const data = type === 'ats' ? lastATSData : lastCompareData;
    if (!data) {
        showToast('No report to export. Run an analysis first.');
        return;
    }

    let text = '';
    const divider = '═'.repeat(60);
    const subDivider = '─'.repeat(60);
    const now = new Date().toLocaleString();

    if (type === 'ats') {
        const fi = data.file_info || {};
        text += `${divider}\n`;
        text += `  ATS COMPATIBILITY REPORT\n`;
        text += `${divider}\n\n`;
        text += `File: ${fi.filename || 'Unknown'}\n`;
        text += `Format: ${(fi.format || '').toUpperCase()}  |  Words: ${fi.word_count || '—'}\n`;
        text += `Date: ${now}\n\n`;

        text += `${subDivider}\n`;
        text += `  OVERALL SCORE: ${data.overall_score}/100\n`;
        text += `${subDivider}\n\n`;

        (data.sections || []).forEach(s => {
            text += `${s.icon} ${s.name}: ${Math.round(s.score)}/100\n`;
            text += `${'─'.repeat(40)}\n`;
            (s.findings || []).forEach(f => {
                text += `  ${f}\n`;
            });
            if (s.recommendations && s.recommendations.length) {
                text += `\n  Recommendations:\n`;
                s.recommendations.forEach(r => {
                    text += `  → ${r}\n`;
                });
            }
            text += `\n`;
        });

    } else if (type === 'compare') {
        const fi = data.file_info || {};
        const comp = data.comparison || {};
        const ats = data.ats_analysis || {};

        text += `${divider}\n`;
        text += `  JOB MATCH COMPARISON REPORT\n`;
        text += `${divider}\n\n`;
        text += `File: ${fi.filename || 'Unknown'}\n`;
        text += `Date: ${now}\n\n`;

        text += `${subDivider}\n`;
        text += `  JOB MATCH SCORE: ${comp.match_score}/100\n`;
        text += `${subDivider}\n\n`;

        if (comp.pros && comp.pros.length) {
            text += `✅ STRENGTHS\n`;
            comp.pros.forEach(p => { text += `  + ${p}\n`; });
            text += `\n`;
        }

        if (comp.cons && comp.cons.length) {
            text += `❌ GAPS\n`;
            comp.cons.forEach(c => { text += `  - ${c}\n`; });
            text += `\n`;
        }

        const ka = comp.keyword_analysis || {};
        if (ka.matched_skills && ka.matched_skills.length) {
            text += `🔑 MATCHED SKILLS: ${ka.matched_skills.join(', ')}\n`;
        }
        if (ka.missing_skills && ka.missing_skills.length) {
            text += `⚠️ MISSING SKILLS: ${ka.missing_skills.join(', ')}\n`;
        }
        text += `\n`;

        if (comp.recommendations && comp.recommendations.length) {
            text += `💡 RECOMMENDATIONS\n`;
            comp.recommendations.forEach(r => {
                const icon = r.action === 'add' ? '➕' : r.action === 'remove' ? '➖' : '🔧';
                text += `  ${icon} [${(r.priority || 'medium').toUpperCase()}] ${r.text}\n`;
            });
            text += `\n`;
        }

        if (ats.sections) {
            text += `${subDivider}\n`;
            text += `  FULL ATS BREAKDOWN (Score: ${ats.overall_score}/100)\n`;
            text += `${subDivider}\n\n`;

            ats.sections.forEach(s => {
                text += `${s.icon} ${s.name}: ${Math.round(s.score)}/100\n`;
                (s.findings || []).forEach(f => {
                    text += `  ${f}\n`;
                });
                text += `\n`;
            });
        }
    }

    // Footer
    text += `${divider}\n`;
    text += `  Generated by Open ATS Check\n`;
    text += `  https://github.com/open-ats-check\n`;
    text += `  ${now}\n`;
    text += `${divider}\n`;

    // Download as text file
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const fname = data.file_info?.filename || 'resume';
    const baseName = fname.replace(/\.[^.]+$/, '');
    a.download = `${baseName}_ats_report_${type}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast('Report exported successfully!');
}

// ─── Animations ───
function animateScore(target) {
    const ring = document.getElementById('score-ring');
    const numberEl = document.getElementById('score-number');
    if (!ring || !numberEl) return;

    const circumference = 2 * Math.PI * 80; // r=80
    const offset = circumference - (target / 100) * circumference;

    setTimeout(() => {
        ring.style.strokeDashoffset = offset;
    }, 100);

    // Animate number
    let current = 0;
    const step = Math.max(1, Math.ceil(target / 60));
    const interval = setInterval(() => {
        current += step;
        if (current >= target) {
            current = Math.round(target);
            clearInterval(interval);
        }
        numberEl.innerHTML = `${current}<small>/100</small>`;
    }, 20);
}

function animateBars() {
    document.querySelectorAll('.section-bar-fill').forEach(bar => {
        setTimeout(() => {
            bar.style.width = bar.dataset.width + '%';
        }, 200);
    });
}

// ─── Toast ───
function showToast(msg) {
    const toast = document.getElementById('toast');
    const msgEl = document.getElementById('toast-msg');
    msgEl.textContent = msg;
    toast.hidden = false;
    requestAnimationFrame(() => toast.classList.add('show'));
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.hidden = true, 300);
    }, 4000);
}

// ─── Helpers ───
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// ─── Init ───
document.addEventListener('DOMContentLoaded', () => {
    setupDropzone('dropzone-ats', 'file-ats', 'ats');
    setupDropzone('dropzone-compare-cv', 'file-compare-cv', 'compare-cv');
    setupDropzone('dropzone-compare-jd', 'file-compare-jd', 'compare-jd');

    // Browse link clicks — open the file picker via data-input attribute
    document.querySelectorAll('.upload-link[data-input]').forEach(link => {
        link.addEventListener('click', (e) => {
            e.stopPropagation();
            const inputId = link.dataset.input;
            const input = document.getElementById(inputId);
            if (input) input.click();
        });
    });

    // Clear button clicks — remove file and stop propagation
    document.querySelectorAll('.btn-clear[data-key]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            e.preventDefault();
            clearFile(btn.dataset.key);
        });
    });

    // Also listen to JD text changes for button state
    const jdInput = document.getElementById('jd-text');
    if (jdInput) {
        jdInput.addEventListener('input', updateButtonStates);
    }
});
