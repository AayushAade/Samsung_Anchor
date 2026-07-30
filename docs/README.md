# MEMORA (Samsung Anchor) — Official Engineering Documentation Suite (RC1)

**Release Candidate**: RC1 (Samsung Solve for Tomorrow Final Build)  
**Target Repository**: `Samsung_Anchor`  
**License**: Proprietary / Open Source Candidate  

---

## Suite Navigation & Folder Structure

```
docs/
├── README.md                                     # Master Index & Executive Overview
├── architecture/
│   ├── system_architecture.md                   # System Architecture & Multi-Modal Data Flow
│   └── modules_and_ai_design.md                 # Subsystem Deep Dives & AI Design
├── clinical/
│   └── clinical_design.md                       # Dementia Care Principles & Database Schema
├── developer/
│   └── api_and_developer_guide.md               # API Reference, Developer Onboarding & Performance
├── deployment/
│   └── deployment_and_security.md               # Deployment, Security, Privacy & Live Demo Guide
├── whitepapers/
│   └── technical_and_clinical_whitepapers.md    # Technical, Architecture & Clinical Whitepapers
├── competition/
│   └── judge_qa_100.md                          # 100 Samsung Judge Q&A Preparation Manual
└── appendix/
    └── appendices.md                            # Glossary, Class Index & State Diagrams
```

---

## Document Metadata Matrix

| Document | File Path | Purpose | Target Audience | Prerequisite Knowledge |
| :--- | :--- | :--- | :--- | :--- |
| **Master Index** | [docs/README.md](file:///Users/siddhant_patil/Projects/Samsung_Anchor/docs/README.md) | Executive summary, vision, problem statement, and repository map. | Judges, Investors, Executives | None |
| **System Architecture** | [docs/architecture/system_architecture.md](file:///Users/siddhant_patil/Projects/Samsung_Anchor/docs/architecture/system_architecture.md) | High-level, layered, component, and runtime data flow diagrams. | Solution Architects, Core Engineers | Distributed Systems, Async Queues |
| **Modules & AI Design** | [docs/architecture/modules_and_ai_design.md](file:///Users/siddhant_patil/Projects/Samsung_Anchor/docs/architecture/modules_and_ai_design.md) | In-depth technical specification of all 21 system modules. | AI Engineers, Software Developers | Python, Computer Vision, FAISS |
| **Clinical Design** | [docs/clinical/clinical_design.md](file:///Users/siddhant_patil/Projects/Samsung_Anchor/docs/clinical/clinical_design.md) | Validation Therapy, Supportive Silence, Patient State, and DB Schema. | Clinicians, Caregivers, Engineers | Dementia Care, SQLite ORM |
| **API & Dev Guide** | [docs/developer/api_and_developer_guide.md](file:///Users/siddhant_patil/Projects/Samsung_Anchor/docs/developer/api_and_developer_guide.md) | Public Python APIs, CLI, WebSocket streams, and Onboarding. | Software Engineers, QA Leads | Python 3.11, Pytest, WebSockets |
| **Deployment & Security** | [docs/deployment/deployment_and_security.md](file:///Users/siddhant_patil/Projects/Samsung_Anchor/docs/deployment/deployment_and_security.md) | Installation, Dockerization, Privacy, Security, and Live Demo Guide. | DevOps, Operators, Demo Leads | Linux, Docker, Hardware HAL |
| **Whitepapers** | [docs/whitepapers/technical_and_clinical_whitepapers.md](file:///Users/siddhant_patil/Projects/Samsung_Anchor/docs/whitepapers/technical_and_clinical_whitepapers.md) | Formal technical, architectural, and clinical whitepapers. | Judges, AI Researchers | Computer Vision, Healthcare AI |
| **Judge Q&A Manual** | [docs/competition/judge_qa_100.md](file:///Users/siddhant_patil/Projects/Samsung_Anchor/docs/competition/judge_qa_100.md) | 100 comprehensive judge questions and evidence-backed answers. | Competition Team, Presenters | Complete MEMORA System Context |
| **Appendices** | [docs/appendix/appendices.md](file:///Users/siddhant_patil/Projects/Samsung_Anchor/docs/appendix/appendices.md) | Glossary, Class index, Sequence diagrams, and State machines. | Engineers, Maintainers | UML, Code Navigation |

---

## PART 1 — EXECUTIVE DOCUMENTATION

### 1. Executive Summary
MEMORA (Samsung Anchor) is an edge-first, multimodal cognitive assistance platform engineered specifically to support individuals living with Mild Cognitive Impairment (MCI), Alzheimer's Disease, and related dementias. 

Unlike generic commercial voice assistants (e.g. Amazon Alexa, Google Assistant)—which rely on active wake-words, high-latency cloud processing, and rigid command syntaxes—MEMORA operates as a **passive, ambient cognitive anchor**. Installed on local edge hardware (such as a smart display or edge robot), MEMORA continuously perceives the physical living environment through edge visual processing, real-time speech recognition, spatial tracking, and local vector memory.

Key System Attributes:
- **Zero Cloud Latency & Total Privacy**: Performs face recognition, object tracking, and care policy evaluations locally without sending personal video or audio streams to external servers.
- **Clinically Grounded Care Policies**: Implements established dementia care frameworks including **Validation Therapy**, **One-Step Guidance**, **Supportive Silence**, and **Emergency Escalation**.
- **Honest Episodic Memory**: Stores visual memories of misplaced personal items (e.g., reading glasses, walking cane, medication bottles) without synthesizing or hallucinating locations.
- **Transparent Decision Tracing**: Generates real-time, human-auditable clinical decision traces (`ClinicalDecisionTrace`) for every system interaction, visible on an interactive web dashboard (`http://localhost:8765`).

---

### 2. Project Vision, Mission & Impact

#### Mission Statement
To empower individuals with dementia to maintain independence and dignity in their home environments, while alleviating emotional burnout for family caregivers through transparent, clinically grounded edge AI.

#### Problem Statement
Over 55 million people worldwide live with dementia, a number projected to reach 139 million by 2050. The early and middle stages of dementia are characterized by:
1. **Spatial Disorientation**: Forgetting where essential personal items (keys, glasses, cane) are placed.
2. **Time-Space Disorientation**: Asking repetitive questions regarding time, schedule, or location.
3. **Anxiety & Emotional Agitation**: Becoming overwhelmed by complex multi-step instructions or argumentative corrections.
4. **Caregiver Burnout**: Family members spending hours daily repeating identical answers and monitoring safety.

Generic smart home systems fail because they demand active cognitive recall (remembering wake words), lack persistent visual memory, and frequently correct or argue with disoriented users.

#### Target Users & Stakeholders
1. **Primary Beneficiaries**: Individuals diagnosed with MCI, early-to-moderate Alzheimer's Disease, or vascular dementia living at home.
2. **Secondary Users**: Family caregivers and professional home-health aides seeking real-time observability into patient emotional state and routine completion.
3. **Tertiary Users**: Clinicians and geriatric care managers auditing long-term cognitive stability and episode logs.

---

### 3. Verification & Operational Modes

MEMORA explicit operational modes:
- **`--simulation` Mode**: Runs synthetic frame generators and mock audio streams. Used for automated testing, CI/CD pipelines, and hardware-free demonstrations.
- **`--live-hardware` Mode**: Activates physical OpenCV camera acquisition (`index 0`), PyAudio microphone listening, and local native text-to-speech engines.

At startup, MEMORA explicitly prints its operational mode banner and subsystem status report.
