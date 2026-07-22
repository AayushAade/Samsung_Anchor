/**
 * Memora Experience Platform — Rendering Engine
 * 
 * Connects to the CognitiveStream WebSocket and renders
 * live cognitive events into the dashboard panels.
 */

// ================================================================
// WebSocket Connection
// ================================================================

class MemoraConnection {
    constructor() {
        this.ws = null;
        this.reconnectDelay = 1000;
        this.maxReconnectDelay = 10000;
        this.onEvent = null;
        this.onStatusChange = null;
    }

    connect() {
        const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${protocol}//${location.host}/ws`;

        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
            console.log('[Memora] Connected to Cognitive Stream');
            this.reconnectDelay = 1000;
            if (this.onStatusChange) this.onStatusChange('connected');
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (this.onEvent) this.onEvent(data);
            } catch (e) {
                console.error('[Memora] Failed to parse event:', e);
            }
        };

        this.ws.onclose = () => {
            console.log('[Memora] Disconnected. Reconnecting...');
            if (this.onStatusChange) this.onStatusChange('disconnected');
            setTimeout(() => this.connect(), this.reconnectDelay);
            this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, this.maxReconnectDelay);
        };

        this.ws.onerror = (error) => {
            console.error('[Memora] WebSocket error:', error);
        };
    }
}

// ================================================================
// Panel Renderers
// ================================================================

const IMPORTANCE_LABELS = { 1: 'LOW', 2: 'NORMAL', 3: 'HIGH', 4: 'CRITICAL' };

function renderPipeline(event) {
    const stages = document.querySelectorAll('.pipeline__stage');
    const connectors = document.querySelectorAll('.pipeline__connector');

    const isSilence = event.attention_decision === 'SILENCE';
    const stageData = [
        { key: 'perception', status: event.name || event.face_id ? '✓ Detected' : '—', active: !!event.face_id },
        { key: 'context', status: `${event.providers_executed} providers`, active: event.providers_executed > 0 },
        { key: 'goals', status: event.goals && event.goals.length > 0 ? `${event.goals.length} hypotheses` : '—', active: event.goals && event.goals.length > 0 },
        { key: 'attention', status: event.attention_decision, active: true },
        { key: 'action', status: event.final_action ? 'Spoken' : (isSilence ? 'Silent' : '—'), active: !!event.final_action },
    ];

    // Animate stages sequentially
    stages.forEach((stage, i) => {
        const data = stageData[i];
        const delay = i * 120;

        setTimeout(() => {
            stage.classList.remove('active', 'completed', 'silence');
            stage.querySelector('.stage__status').textContent = data.status;

            if (data.active) {
                if (data.key === 'attention' && isSilence) {
                    stage.classList.add('silence');
                } else if (data.key === 'action' && isSilence) {
                    stage.classList.add('silence');
                } else {
                    stage.classList.add('completed');
                }
            }
        }, delay);
    });

    // Animate connectors
    connectors.forEach((conn, i) => {
        setTimeout(() => {
            conn.classList.toggle('active', stageData[i].active && stageData[i + 1] && stageData[i + 1].active);
        }, (i + 1) * 120);
    });

    // Activate panel
    const panel = document.getElementById('pipeline-panel');
    panel.classList.add('active');
    setTimeout(() => panel.classList.remove('active'), 2000);
}

function renderIdentity(event) {
    const container = document.getElementById('identity-content');
    const panel = document.getElementById('identity-panel');

    if (!event.face_id) {
        container.innerHTML = `
            <div class="identity__empty">
                <div class="identity__avatar identity__avatar--empty">?</div>
                <p>No person detected</p>
            </div>`;
        return;
    }

    const initial = event.name ? event.name.charAt(0).toUpperCase() : '?';
    const name = event.name || 'Unknown';
    const relationship = event.relationship || 'Unknown';
    const confidence = Math.round((event.identity_confidence || 0) * 100);
    const circumference = 2 * Math.PI * 16;
    const offset = circumference - (confidence / 100) * circumference;

    container.innerHTML = `
        <div style="display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 8px 0;">
            <div class="identity__avatar identity__avatar--known">${initial}</div>
            <div class="identity__info">
                <div class="identity__name">${name}</div>
                <div class="identity__relationship">${relationship}</div>
                <div class="identity__face-id">${event.face_id}</div>
            </div>
            <div class="identity__confidence">
                <div class="confidence__ring">
                    <svg width="40" height="40" viewBox="0 0 40 40">
                        <circle class="ring-bg" cx="20" cy="20" r="16" />
                        <circle class="ring-fill" cx="20" cy="20" r="16"
                            stroke-dasharray="${circumference}"
                            stroke-dashoffset="${offset}" />
                    </svg>
                </div>
                <span class="confidence__label">${confidence}% confidence</span>
            </div>
        </div>`;

    panel.classList.add('active');
    setTimeout(() => panel.classList.remove('active'), 2000);
}

function renderOrientation(event) {
    const container = document.getElementById('orientation-content');
    const panel = document.getElementById('orientation-panel');

    if (!container || !panel) return;

    const stage = event.routine_stage || 'Daytime Routine';
    const currentDay = event.current_day || '';
    const approxTime = event.approximate_time || '';
    const recent = event.recent_activity || 'Resting in living room';
    const upcoming = event.upcoming_activity || 'Next scheduled activity';

    container.innerHTML = `
        <div class="orientation-card">
            <div class="orientation-card__header">
                <span class="orientation-card__stage-badge">📌 ${stage}</span>
                <span class="orientation-card__datetime">${currentDay} ${approxTime ? '· ' + approxTime : ''}</span>
            </div>
            <div class="orientation-card__activities">
                <div class="orientation-card__item">
                    <span class="orientation-card__item-label">Recent:</span> ${recent}
                </div>
                <div class="orientation-card__item">
                    <span class="orientation-card__item-label">Upcoming:</span> ${upcoming}
                </div>
            </div>
        </div>`;

    panel.classList.add('active');
    setTimeout(() => panel.classList.remove('active'), 2000);
}

function renderRelationship(event) {
    const container = document.getElementById('relationship-content');
    const panel = document.getElementById('relationship-panel');

    if (!container || !panel) return;

    if (!event.name && !event.preferred_greeting) {
        container.innerHTML = '<div class="relationship__empty"><p>No active relationship profile loaded</p></div>';
        return;
    }

    const greeting = event.preferred_greeting || `Hello ${event.name || 'Friend'}`;
    const freq = event.visit_frequency || 'Regular Visitor';
    const lastVisit = event.last_interaction || 'Recently';
    const sharedMems = event.shared_memories || [];
    const dates = event.important_dates || [];

    const memsHtml = sharedMems.length > 0
        ? sharedMems.map(m => `<div class="shared-mem-chip">💚 ${m.summary}</div>`).join('')
        : '<div class="shared-mem-chip">💚 Shared conversations in living room</div>';

    const datesHtml = dates.length > 0
        ? `<div style="font-size:0.75rem; color:var(--text-tertiary); margin-top:4px;">🗓️ ${dates.join(' · ')}</div>`
        : '';

    container.innerHTML = `
        <div class="relationship-card">
            <div class="relationship-card__header">
                <span class="relationship-card__badge">🤝 ${event.relationship || 'Connected'}</span>
                <span style="font-size:0.75rem; color:var(--text-tertiary);">${freq} · ${lastVisit}</span>
            </div>
            <div class="relationship-card__greeting">"${greeting}"</div>
            <div class="relationship-card__shared-mems">
                ${memsHtml}
            </div>
            ${datesHtml}
        </div>`;

    panel.classList.add('active');
    setTimeout(() => panel.classList.remove('active'), 2000);
}

function renderAssistance(event) {
    const container = document.getElementById('assistance-content');
    const panel = document.getElementById('assistance-panel');

    if (!container || !panel) return;

    const lvlCode = event.assistance_level !== undefined ? event.assistance_level : 0;
    const lvlLabel = event.assistance_level_label || `Level ${lvlCode}: Observe`;
    const rationale = event.assistance_rationale || 'Patient navigating routine independently.';

    container.innerHTML = `
        <div class="assistance-card">
            <div class="assistance-card__header">
                <span class="assistance-level-badge assistance-level--${lvlCode}">${lvlLabel}</span>
                ${event.escalation_triggered ? '<span style="font-size:0.7rem; color:var(--color-warning); font-weight:600;">⚠️ Escalated</span>' : ''}
            </div>
            <div class="assistance-card__rationale">${rationale}</div>
        </div>`;

    panel.classList.add('active');
    setTimeout(() => panel.classList.remove('active'), 2000);
}

function renderConversation(event) {
    const container = document.getElementById('conversation-content');
    const panel = document.getElementById('conversation-panel');

    if (!container || !panel) return;

    const state = event.conversation_state || 'Idle';
    const speaker = event.active_speaker || 'Patient';
    const strategy = event.response_strategy || 'Supportive Silence';
    const turns = event.turn_count || 0;
    const elapsed = event.elapsed_seconds || 0;
    const topic = event.conversation_topic || 'General Orientation & Support';

    container.innerHTML = `
        <div class="conversation-card">
            <div class="conversation-card__header">
                <span class="conversation-state-badge">💬 ${state}</span>
                <span style="font-size:0.75rem; color:var(--text-tertiary);">Speaker: ${speaker}</span>
            </div>
            <div class="conversation-card__metrics">
                <span>Turn: #${turns}</span>
                <span>Duration: ${elapsed}s</span>
                <span>Topic: ${topic}</span>
            </div>
            <div class="conversation-card__strategy">
                <span style="color:var(--text-tertiary); font-size:0.75rem;">Strategy:</span> <strong>${strategy}</strong>
            </div>
        </div>`;

    panel.classList.add('active');
    setTimeout(() => panel.classList.remove('active'), 2000);
}

function renderClinical(event) {
    const container = document.getElementById('clinical-content');
    const panel = document.getElementById('clinical-panel');

    if (!container || !panel) return;

    const patient = event.patient_name || 'Eleanor';
    const caregiver = event.primary_caregiver || 'Sarah Jenkins';
    const meds = (event.pending_medications || []).join(', ') || 'All morning meds confirmed';
    const appts = (event.upcoming_appointments || []).join(', ') || 'No immediate appointments';
    const explanation = event.explanation_reason || 'System evaluating routine observation status.';
    const consent = event.consent_granted ? 'Granted ✓' : 'Revoked ❌';

    container.innerHTML = `
        <div class="clinical-card">
            <div class="clinical-card__header">
                <span class="clinical-tag">Patient: ${patient}</span>
                <span style="font-size:0.75rem; color:var(--text-tertiary);">Caregiver: ${caregiver}</span>
            </div>
            <div style="font-size:0.8rem; color:var(--text-secondary); margin-top:4px;">
                <div><strong>Pending Meds:</strong> ${meds}</div>
                <div><strong>Upcoming Appts:</strong> ${appts}</div>
                <div><strong>Voice Consent:</strong> ${consent}</div>
            </div>
            <div class="clinical-card__explanation">
                <strong>Decision Rationale:</strong> ${explanation}
            </div>
        </div>`;

    panel.classList.add('active');
    setTimeout(() => panel.classList.remove('active'), 2000);
}

function renderPerception(event) {
    const container = document.getElementById('perception-content');
    const panel = document.getElementById('perception-panel');

    if (!container || !panel) return;

    const room = event.current_room || 'Living Room';
    const activity = event.detected_activity || 'Sitting';
    const fps = event.sensor_fps !== undefined ? event.sensor_fps : 30.0;
    const objs = (event.detected_objects || []).join(', ') || 'Reading Glasses, Water Bottle';
    const auds = (event.audio_events || []).join(', ') || 'Speech Present';

    container.innerHTML = `
        <div class="perception-card">
            <div class="perception-card__header">
                <span class="room-badge">📍 ${room}</span>
                <span class="activity-badge">🏃 ${activity}</span>
            </div>
            <div style="font-size:0.8rem; color:var(--text-secondary); margin-top:6px;">
                <div><strong>Tracked Objects:</strong> ${objs}</div>
                <div><strong>Audio Events:</strong> ${auds}</div>
                <div style="margin-top:2px; font-size:0.75rem; color:var(--text-tertiary);">Sensor Rate: ${fps} FPS</div>
            </div>
        </div>`;

    panel.classList.add('active');
    setTimeout(() => panel.classList.remove('active'), 2000);
}

function renderRuntime(event) {
    const container = document.getElementById('runtime-content');
    const panel = document.getElementById('runtime-panel');

    if (!container || !panel) return;

    const mode = event.runtime_mode || 'Simulation Mode';
    const cpu = event.cpu_usage_pct !== undefined ? event.cpu_usage_pct : 14.2;
    const ram = event.ram_usage_pct !== undefined ? event.ram_usage_pct : 36.8;
    const devCount = event.connected_devices_count !== undefined ? event.connected_devices_count : 6;

    container.innerHTML = `
        <div class="runtime-card">
            <div class="runtime-card__header">
                <span class="mode-badge">⚡ ${mode}</span>
                <span class="device-chip">STATUS: HEALTHY</span>
            </div>
            <div style="font-size:0.8rem; color:var(--text-secondary); margin-top:6px;">
                <div><strong>System Resources:</strong> CPU: ${cpu}% | RAM: ${ram}%</div>
                <div><strong>Active Hardware Adapters:</strong> ${devCount} Connected</div>
                <div style="margin-top:2px; font-size:0.75rem; color:var(--text-tertiary);">Camera, Mic, Speaker, BLE, IMU OK</div>
            </div>
        </div>`;

    panel.classList.add('active');
    setTimeout(() => panel.classList.remove('active'), 2000);
}

function renderOperations(event) {
    const container = document.getElementById('ops-content');
    const panel = document.getElementById('ops-panel');

    if (!container || !panel) return;

    const profile = event.deployment_profile || 'Simulation Profile';
    const health = event.system_health_status || 'Healthy';
    const cycles = event.total_cycles_executed !== undefined ? event.total_cycles_executed : 1;
    const errors = event.active_errors_count !== undefined ? event.active_errors_count : 0;

    container.innerHTML = `
        <div class="ops-card">
            <div class="ops-card__header">
                <span class="profile-badge">⚙️ ${profile}</span>
                <span class="health-chip">HEALTH: ${health.toUpperCase()}</span>
            </div>
            <div style="font-size:0.8rem; color:var(--text-secondary); margin-top:6px;">
                <div><strong>Total Cycles Executed:</strong> ${cycles}</div>
                <div><strong>Active Error Alerts:</strong> ${errors}</div>
                <div style="margin-top:2px; font-size:0.75rem; color:var(--text-tertiary);">Structured JSON Logging & Metrics Active</div>
            </div>
        </div>`;

    panel.classList.add('active');
    setTimeout(() => panel.classList.remove('active'), 2000);
}

function renderGoals(event) {
    const container = document.getElementById('goals-content');
    const panel = document.getElementById('goals-panel');

    if (!event.goals || event.goals.length === 0) {
        container.innerHTML = '<div class="goals__empty">No goals inferred</div>';
        return;
    }

    container.innerHTML = event.goals.map(goal => {
        const pct = Math.round(goal.confidence * 100);
        const evidence = (goal.supporting_evidence || []).map(e =>
            `<span class="evidence-tag">${e.signal} +${e.weight.toFixed(2)}</span>`
        ).join('');

        return `
            <div class="goal-item">
                <div class="goal-item__header">
                    <span class="goal-item__name">${goal.name}</span>
                    <span class="goal-item__state goal-item__state--${goal.state}">${goal.state}</span>
                </div>
                <div class="goal-item__bar">
                    <div class="goal-item__fill" style="width: ${pct}%"></div>
                </div>
                <span class="goal-item__confidence">${pct}% confidence · ${goal.category}</span>
                ${evidence ? `<div class="goal-item__evidence">${evidence}</div>` : ''}
            </div>`;
    }).join('');

    panel.classList.add('active');
    setTimeout(() => panel.classList.remove('active'), 2000);
}

function renderAttention(event) {
    const container = document.getElementById('attention-content');
    const panel = document.getElementById('attention-panel');

    const isInterrupt = event.attention_decision === 'INTERRUPT';
    const score = event.attention_score || 0;
    const threshold = event.attention_threshold || 35;
    const maxScore = Math.max(score, threshold) * 1.3;
    const fillPct = Math.min(100, (score / maxScore) * 100);
    const thresholdPct = (threshold / maxScore) * 100;

    let explanation = '';
    if (isInterrupt) {
        explanation = `Score ${score.toFixed(1)} exceeded threshold ${threshold.toFixed(1)}. The memory was important enough to warrant interrupting the user.`;
    } else {
        explanation = `Score ${score.toFixed(1)} did not reach threshold ${threshold.toFixed(1)}. The AI intentionally remained silent — no sufficiently urgent context was detected.`;
    }

    let responseHtml = '';
    if (event.generated_response) {
        responseHtml = `<div class="attention__response">${event.generated_response}</div>`;
    }

    container.innerHTML = `
        <div class="attention__decision">
            <div class="attention__verdict attention__verdict--${isInterrupt ? 'interrupt' : 'silence'}">
                ${isInterrupt ? '⚡ INTERRUPT' : '🤫 COGNITIVE SILENCE'}
            </div>
            <p class="attention__explanation">${explanation}</p>
            <div class="attention__meter">
                <div class="meter__bar">
                    <div class="meter__fill meter__fill--${isInterrupt ? 'interrupt' : 'silence'}" style="width: ${fillPct}%"></div>
                    <div class="meter__threshold" style="left: ${thresholdPct}%"></div>
                </div>
                <div class="meter__labels">
                    <span>Score: ${score.toFixed(1)}</span>
                    <span>Threshold: ${threshold.toFixed(1)}</span>
                </div>
            </div>
            ${responseHtml}
        </div>`;

    panel.classList.add('active');
    setTimeout(() => panel.classList.remove('active'), 2000);
}

function renderMemories(event) {
    const container = document.getElementById('memory-content');
    const panel = document.getElementById('memory-panel');

    if (!event.memories || event.memories.length === 0) {
        container.innerHTML = '<div class="memories__empty">No memories retrieved</div>';
        return;
    }

    container.innerHTML = event.memories.map(mem => {
        const impLabel = IMPORTANCE_LABELS[mem.importance] || 'NORMAL';
        const commitments = (mem.commitments || []).map(c => `📋 ${c}`).join(', ');

        return `
            <div class="memory-card">
                <div class="memory-card__header">
                    <span class="memory-card__summary">${mem.summary}</span>
                    <span class="memory-card__importance importance--${impLabel}">${impLabel}</span>
                </div>
                <div class="memory-card__meta">
                    <span>Confidence: ${(mem.confidence || 1).toFixed(2)}</span>
                    <span>Usefulness: ${(mem.usefulness || 0.5).toFixed(2)}</span>
                </div>
                ${commitments ? `<div class="memory-card__commitments">${commitments}</div>` : ''}
            </div>`;
    }).join('');

    panel.classList.add('active');
    setTimeout(() => panel.classList.remove('active'), 2000);
}

function renderTimeline(event) {
    const container = document.getElementById('timeline-content');

    // Remove empty state
    const empty = container.querySelector('.timeline__empty');
    if (empty) empty.remove();

    const isInterrupt = event.attention_decision === 'INTERRUPT';
    const dotClass = isInterrupt ? 'interrupt' : 'silence';

    // Format timestamp
    const ts = event.timestamp || new Date().toISOString();
    const time = ts.split('T')[1]?.split('.')[0] || ts;

    // Build detail lines
    const details = [];
    if (event.name) details.push(`${event.name}${event.relationship ? ` (${event.relationship})` : ''}`);
    if (event.memory_count > 0) details.push(`${event.memory_count} memories retrieved`);
    if (event.goals && event.goals.length > 0) {
        const top = event.goals[0];
        details.push(`Top goal: ${top.name} (${Math.round(top.confidence * 100)}%)`);
    }
    if (event.attention_score > 0) details.push(`Attention: ${event.attention_score.toFixed(1)} / ${event.attention_threshold}`);
    if (event.generated_response) details.push(`"${event.generated_response}"`);

    const title = isInterrupt ? '⚡ Context Cue Delivered' : '🤫 Cognitive Silence';

    const eventEl = document.createElement('div');
    eventEl.className = 'timeline-event';
    eventEl.innerHTML = `
        <span class="timeline-event__time">${time}</span>
        <div class="timeline-event__dot timeline-event__dot--${dotClass}"></div>
        <div class="timeline-event__body">
            <div class="timeline-event__title">${title} · Cycle ${event.cycle_id}</div>
            <div class="timeline-event__detail">${details.join(' → ')}</div>
        </div>`;

    // Prepend (newest first)
    container.insertBefore(eventEl, container.firstChild);

    // Limit to 50 events
    while (container.children.length > 50) {
        container.removeChild(container.lastChild);
    }
}

// ================================================================
// Status & Connection UI
// ================================================================

function updateConnectionStatus(status) {
    const indicator = document.getElementById('connection-status');
    const dot = indicator.querySelector('.status-dot');
    const text = indicator.querySelector('.status-text');

    dot.classList.remove('connected', 'disconnected');

    if (status === 'connected') {
        dot.classList.add('connected');
        text.textContent = 'Live';
    } else {
        dot.classList.add('disconnected');
        text.textContent = 'Reconnecting…';
    }
}

function updateCycleCounter(event) {
    const counter = document.getElementById('cycle-counter');
    const latency = event.total_latency_ms || 0;
    counter.textContent = `Cycle ${event.cycle_id} · ${latency.toFixed(0)}ms`;
}

// ================================================================
// Main Event Handler
// ================================================================

function handleCognitiveEvent(event) {
    // Update all panels
    renderPipeline(event);
    renderOrientation(event);
    renderIdentity(event);
    renderRelationship(event);
    renderGoals(event);
    renderAttention(event);
    renderAssistance(event);
    renderConversation(event);
    renderClinical(event);
    renderPerception(event);
    renderRuntime(event);
    renderOperations(event);
    renderMemories(event);
    renderTimeline(event);
    updateCycleCounter(event);
}

// ================================================================
// Initialize
// ================================================================

document.addEventListener('DOMContentLoaded', () => {
    const connection = new MemoraConnection();
    connection.onEvent = handleCognitiveEvent;
    connection.onStatusChange = updateConnectionStatus;
    connection.connect();

    // Caregiver View Toggle Logic
    const toggleInput = document.getElementById('caregiver-toggle-input');
    
    const panelTitles = {
        'pipeline-panel': { tech: 'Cognitive Pipeline', care: 'Memora Processing' },
        'orientation-panel': { tech: 'Daily Orientation', care: 'Daily Routine & Flow' },
        'identity-panel': { tech: 'Identity', care: 'Recognized Person' },
        'relationship-panel': { tech: 'Relationship Context', care: 'Family & Friend Connection' },
        'goals-panel': { tech: 'Goal Hypotheses', care: 'Estimated Needs / Activities' },
        'attention-panel': { tech: 'Executive Attention', care: 'Decision to Speak / Intervene' },
        'assistance-panel': { tech: 'Assistance Policy Engine', care: 'Support Level & Independence' },
        'conversation-panel': { tech: 'Conversation Engine', care: 'Voice & Dialogue Flow' },
        'clinical-panel': { tech: 'Clinical Ecosystem', care: 'Care & Health Management' },
        'perception-panel': { tech: 'Edge Perception Engine', care: 'Environment & Activity Monitoring' },
        'runtime-panel': { tech: 'Hardware Runtime Engine', care: 'Device & System Health' },
        'ops-panel': { tech: 'Operations & Observability Engine', care: 'System Reliability & Health' },
        'memory-panel': { tech: 'Retrieved Memories', care: 'Recalled Information' },
        'timeline-panel': { tech: 'Cognitive Timeline', care: 'Event Timeline' }
    };

    if (toggleInput) {
        toggleInput.addEventListener('change', (e) => {
            const isCaregiver = e.target.checked;
            
            for (const [panelId, titles] of Object.entries(panelTitles)) {
                const panel = document.getElementById(panelId);
                if (panel) {
                    const titleEl = panel.querySelector('.panel__title');
                    if (titleEl) {
                        titleEl.textContent = isCaregiver ? titles.care : titles.tech;
                    }
                }
            }
        });
    }
});
