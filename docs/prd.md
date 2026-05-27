# AfroLete Product Requirements Document

**Version:** 1.0.0
**Date:** January 2026
**Classification:** Product Specification
**Status:** Development Ready

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Vision & Strategy](#2-product-vision--strategy)
3. [Tenant Architecture & Organization Model](#3-tenant-architecture--organization-model)
4. [User Personas & Stakeholder Analysis](#4-user-personas--stakeholder-analysis)
5. [Player Profile & Identity Management](#5-player-profile--identity-management)
6. [Performance Metrics & Analytics](#6-performance-metrics--analytics)
7. [AI-Powered Data Ingestion](#7-ai-powered-data-ingestion)
8. [Training & Coaching System](#8-training--coaching-system)
9. [Competition Management](#9-competition-management)
10. [Communications & Parental Consent](#10-communications--parental-consent)
11. [User Interface & Experience Design](#11-user-interface--experience-design)
12. [Reporting & Intelligence](#12-reporting--intelligence)
13. [Security, Privacy & Compliance](#13-security-privacy--compliance)
14. [Integration Ecosystem](#14-integration-ecosystem)
15. [Technical Architecture](#15-technical-architecture)
16. [Data Model](#16-data-model)
17. [Non-Functional Requirements](#17-non-functional-requirements)
18. [Development Phases & Roadmap](#18-development-phases--roadmap)
19. [Success Metrics](#19-success-metrics)
20. [Appendices](#20-appendices)

---

## 1. Executive Summary

### 1.1 Product Overview

AfroLete is a comprehensive, multi-tenant sports management platform designed to transform how clubs, schools, associations, and teams manage athletic programs. The platform provides end-to-end capabilities for player management, performance analytics, competition administration, and AI-driven coaching—all within a stunning, intuitive interface that requires zero training to use effectively.

### 1.2 Core Value Proposition

| Stakeholder | Pain Point | AfroLete Solution |
|-------------|------------|-------------------|
| **Clubs & Teams** | Fragmented player data, manual performance tracking | Unified player profiles with AI-driven performance insights |
| **Schools** | Compliance burden, parent communication overhead | Automated consent workflows, integrated parental engagement |
| **Associations** | Complex competition logistics, inconsistent reporting | AI-optimized scheduling, standardized analytics |
| **Coaches** | Time-intensive performance analysis | Automated video analysis, AI-generated training plans |
| **Parents** | Lack of visibility into child's development | Real-time progress dashboards, transparent communication |
| **Players** | Limited feedback on performance improvement | Personalized metrics, goal tracking, achievement recognition |

### 1.3 Key Differentiators

1. **AI-First Performance Analysis**: Automatic extraction of performance metrics from video, audio narration, and text evaluations
2. **Adaptive Training Intelligence**: Machine learning models that generate personalized training plans based on performance patterns
3. **Zero-Training Interface**: Ergonomic design so intuitive that users understand immediately what actions to take
4. **Multi-Sport Flexibility**: Configurable metrics and workflows for any sport—football, basketball, athletics, rugby, swimming, and more
5. **Parental Consent Automation**: Streamlined permission workflows for minor athletes with full audit trails

---

## 2. Product Vision & Strategy

### 2.1 Vision Statement

*To become the global standard for athlete development by creating an AI-powered ecosystem that transforms raw athletic potential into measurable achievement, while fostering meaningful connections between athletes, coaches, families, and sporting communities.*

### 2.2 Mission

Empower every athlete—from grassroots beginners to elite competitors—with world-class performance analytics and coaching intelligence previously available only to professional organizations.

### 2.3 Strategic Objectives

| Objective | Target | Timeframe |
|-----------|--------|-----------|
| Platform adoption | 10,000 active organizations | 24 months |
| Active athlete profiles | 500,000 players | 24 months |
| Performance data points ingested | 50M monthly | 18 months |
| Training plan accuracy | >85% improvement correlation | 12 months |
| User satisfaction (NPS) | >70 | Ongoing |

### 2.4 Target Markets

**Primary Markets:**
- Youth sports clubs (ages 6-18)
- Secondary schools with athletic programs
- Amateur sports associations
- Community sports leagues

**Secondary Markets:**
- University/college athletics
- Semi-professional clubs
- National sports federations
- Elite athlete academies

### 2.5 Business Model

| Revenue Stream | Description | Pricing Approach |
|----------------|-------------|------------------|
| **Subscription** | Tiered plans by organization size | Per-athlete/month |
| **AI Analysis Credits** | Video/audio processing | Pay-per-use |
| **Competition Management** | Tournament/league hosting | Per-event fee |
| **Premium Reports** | Advanced analytics packages | Add-on pricing |
| **API Access** | Third-party integrations | Developer tiers |

---

## 3. Tenant Architecture & Organization Model

### 3.1 Tenant Types

AfroLete operates on a hierarchical multi-tenant architecture supporting diverse organizational structures:

#### 3.1.1 Clubs

Independent sports organizations with one or more teams.

**Attributes:**
- Organization name, registration details, logo/branding
- Physical address(es) and facilities
- Contact information and administrators
- Membership structure and fee schedules
- Equipment inventory
- Sponsorship relationships

**Capabilities:**
- Manage multiple teams across multiple sports
- Define membership tiers and pricing
- Track club-wide performance metrics
- Coordinate internal competitions
- Manage club finances and budgets

#### 3.1.2 Schools

Educational institutions with athletic programs.

**Attributes:**
- Institution name and type (primary, secondary, university)
- Accreditation and compliance requirements
- Academic calendar integration
- Faculty/staff athletic coordinators
- Facility sharing arrangements

**Capabilities:**
- Integrate with academic schedules
- Enforce eligibility requirements (academic standing, age)
- Coordinate with physical education curriculum
- Manage inter-school competitions
- Generate compliance reports

#### 3.1.3 Associations

Governing bodies that oversee multiple clubs/schools.

**Attributes:**
- Governing jurisdiction (regional, national, international)
- Member organization registry
- Rulebook and regulations
- Sanctioning authority
- Official recognition credentials

**Capabilities:**
- Define sport-specific rules and regulations
- Certify coaches and officials
- Sanction competitions and leagues
- Aggregate statistics across members
- Manage referee/official assignments

#### 3.1.4 Teams

The fundamental competitive unit within any organization.

**Attributes:**
- Team name and sport discipline
- Age group/division classification
- Roster of players
- Coaching staff assignments
- Home venue/training ground
- Team colors and identity

**Capabilities:**
- Manage player roster and positions
- Record training sessions and matches
- Track team-level performance metrics
- Coordinate schedules and fixtures
- Communicate with team members

### 3.2 Organizational Hierarchy

```
Association (optional)
    └── Club / School (primary tenant)
            ├── Sport Program (e.g., Football, Basketball)
            │       ├── Team (e.g., U-14 Boys)
            │       │       ├── Players
            │       │       ├── Coaching Staff
            │       │       └── Support Staff
            │       └── Team (e.g., U-16 Girls)
            │               └── ...
            └── Sport Program (e.g., Athletics)
                    └── Squad/Group (e.g., Sprinters)
                            └── ...
```

### 3.3 Group Structures

Within organizations, flexible grouping allows for:

**Training Groups:**
- Skill-based groupings (e.g., advanced, intermediate, beginner)
- Position-specific groups (e.g., goalkeepers, strikers)
- Conditioning groups (e.g., strength, endurance)

**Administrative Groups:**
- Age cohorts
- Gender classifications
- Academic year groups
- Membership tiers

**Competition Groups:**
- League divisions
- Tournament pools
- Playoff brackets

### 3.4 Inter-Organizational Relationships

**Club-to-Club:**
- Fixture scheduling
- Player transfers
- Friendly match arrangements
- Shared facility bookings

**School-to-School:**
- Inter-school leagues
- District/regional championships
- Athletic scholarship networks

**Association Oversight:**
- Member club registration
- Competition sanctioning
- Rule enforcement
- Statistics aggregation

---

## 4. User Personas & Stakeholder Analysis

### 4.1 Primary Personas

#### 4.1.1 Coach Carlos

**Profile:**
- Age: 35-55
- Role: Head Coach / Technical Director
- Technical proficiency: Moderate
- Primary devices: Tablet (field), Desktop (planning)

**Goals:**
- Maximize athlete development with limited time
- Make data-driven training decisions
- Communicate effectively with parents
- Track progress across the season

**Pain Points:**
- Too much administrative overhead
- Difficulty analyzing video footage
- Inconsistent performance tracking
- Scattered communication channels

**Key Features Needed:**
- One-click video upload with automatic analysis
- AI-generated training recommendations
- Visual performance dashboards
- Integrated messaging with parents

---

#### 4.1.2 Player Patricia (Adult)

**Profile:**
- Age: 18+
- Role: Competitive athlete
- Technical proficiency: High (mobile-native)
- Primary devices: Smartphone

**Goals:**
- Track personal improvement
- Understand strengths and weaknesses
- Access training schedules
- Connect with teammates

**Pain Points:**
- Lack of personalized feedback
- No historical performance data
- Missing training sessions due to poor communication
- Limited visibility into selection criteria

**Key Features Needed:**
- Personal performance dashboard
- Goal setting and achievement tracking
- Push notifications for schedules
- Self-assessment submission

---

#### 4.1.3 Parent Priya

**Profile:**
- Age: 30-50
- Role: Parent/Guardian of minor athlete
- Technical proficiency: Varies widely
- Primary devices: Smartphone

**Goals:**
- Monitor child's safety and well-being
- Track development and progress
- Manage administrative requirements
- Stay informed about schedules

**Pain Points:**
- Drowning in permission slips and forms
- Missing important communications
- No insight into training quality
- Unclear about payment obligations

**Key Features Needed:**
- Digital consent and permission management
- Real-time schedule updates
- Progress reports and highlights
- Secure payment portal

---

#### 4.1.4 Administrator Alex

**Profile:**
- Age: 25-60
- Role: Club Manager / Sports Coordinator
- Technical proficiency: Moderate to high
- Primary devices: Desktop, Tablet

**Goals:**
- Streamline operations
- Ensure compliance and safety
- Manage finances effectively
- Grow organization membership

**Pain Points:**
- Manual data entry and duplication
- Complex scheduling logistics
- Compliance documentation burden
- Fragmented systems and spreadsheets

**Key Features Needed:**
- Bulk registration and data import
- Automated scheduling with conflict detection
- Compliance dashboard and audit trails
- Financial reporting and invoicing

---

#### 4.1.5 Young Player Yusuf (Minor)

**Profile:**
- Age: 8-17
- Role: Youth athlete
- Technical proficiency: Native digital user
- Primary devices: Smartphone (parent-supervised)

**Goals:**
- Improve at their sport
- Earn recognition and achievements
- Have fun while competing
- Connect with teammates

**Pain Points:**
- Abstract feedback hard to understand
- No sense of progress
- Boring or repetitive drills
- Feeling overlooked in large groups

**Key Features Needed:**
- Gamified progress with badges/achievements
- Simple, visual performance feedback
- Fun challenges and goals
- Team social features

---

### 4.2 Secondary Personas

#### 4.2.1 Medical Staff Maria

**Goals:** Track athlete health, prevent injuries, manage return-to-play protocols
**Key Features:** Health record access, injury logging, clearance workflows

#### 4.2.2 Scout Samuel

**Goals:** Identify talent, compare athletes, track prospects
**Key Features:** Search and filter players, comparative analytics, watchlists

#### 4.2.3 Referee Raymond

**Goals:** Access assignments, report match results, review incidents
**Key Features:** Assignment calendar, scoring interface, incident reporting

#### 4.2.4 Sponsor Sandra

**Goals:** Track brand exposure, measure engagement, manage sponsorships
**Key Features:** Exposure analytics, branded content placement, ROI dashboards

#### 4.2.5 Federation Official Flora

**Goals:** Ensure compliance, aggregate statistics, govern competitions
**Key Features:** Cross-organization reporting, rule enforcement, sanctioning tools

---

### 4.3 Stakeholder Priority Matrix

| Stakeholder | Influence | Interest | Engagement Strategy |
|-------------|-----------|----------|---------------------|
| Coaches | High | High | Partner closely, co-design features |
| Parents | Medium | High | Keep informed, streamline experience |
| Players | Low | High | Engage through gamification, social |
| Administrators | High | High | Partner closely, automate workflows |
| Medical Staff | Medium | Medium | Integrate health workflows |
| Associations | High | Medium | Standard compliance, reporting |
| Sponsors | Medium | Low | Provide exposure metrics |

---

## 5. Player Profile & Identity Management

### 5.1 Profile Overview

Every athlete in AfroLete has a comprehensive profile that serves as the single source of truth for their identity, history, and development journey.

### 5.2 Profile Components

#### 5.2.1 Identity Information

**Core Identity:**
| Field | Description | Validation |
|-------|-------------|------------|
| Full Legal Name | As appears on official documents | Required, 2-100 chars |
| Preferred Name | Name used in day-to-day interactions | Optional |
| Date of Birth | For age verification and grouping | Required, verified |
| Gender | Male/Female/Non-binary/Prefer not to say | Required for competition |
| Nationality | Country of citizenship | Required |
| National ID Number | For official verification | Optional, encrypted |
| Photo | Recent headshot for identification | Required, face detection validated |

**Contact Information:**
| Field | Description | Access Control |
|-------|-------------|----------------|
| Email Address | Primary electronic contact | Visible to coaches, admins |
| Phone Number | Emergency and direct contact | Visible to coaches, admins |
| Physical Address | Home address | Visible to admins only |
| Emergency Contact | Next of kin details | Visible to coaches, medical, admins |

**For Minor Athletes (additional):**
| Field | Description | Notes |
|-------|-------------|-------|
| Parent/Guardian 1 | Primary guardian contact | Required for <18 |
| Parent/Guardian 2 | Secondary guardian contact | Optional |
| Guardian Relationship | Parent/Guardian/Other | Dropdown selection |
| Custody Arrangements | Special notes if applicable | Confidential |

---

#### 5.2.2 Physical Attributes

**Biometric Data:**
| Attribute | Unit | Update Frequency |
|-----------|------|------------------|
| Height | cm | Quarterly |
| Weight | kg | Monthly |
| Wingspan | cm | Annually |
| Foot Size | EU/UK/US | Annually |
| Dominant Hand | Left/Right/Ambidextrous | Once |
| Dominant Foot | Left/Right/Both | Once |
| Body Fat % | Percentage | Monthly (optional) |
| Resting Heart Rate | BPM | Monthly (optional) |

**Physical Assessments:**
| Assessment | Metrics | Frequency |
|------------|---------|-----------|
| Speed Tests | 10m, 40m, 100m times | Monthly |
| Endurance | VO2 max estimate, beep test level | Quarterly |
| Strength | Bench, squat, deadlift (age-appropriate) | Monthly |
| Flexibility | Sit-and-reach, specific joints | Monthly |
| Agility | T-test, Illinois test times | Monthly |
| Jump Tests | Vertical leap, broad jump | Monthly |

---

#### 5.2.3 Athletic History

**Experience Record:**
| Element | Description |
|---------|-------------|
| Sports Played | List of all sports with start dates |
| Primary Position(s) | Current position(s) in primary sport |
| Previous Clubs/Schools | Historical affiliations with dates |
| Highest Level Achieved | Recreational/Club/Regional/National/International |
| Notable Achievements | Titles, records, representative honors |
| Training Background | Formal coaching, camps attended |

**Affiliation Timeline:**
```
[Start Date] ─── Organization Name (Sport, Role) ─── [End Date]
     │
     ├── Performance highlights during tenure
     ├── Competitions participated
     └── Skills developed
```

---

#### 5.2.4 Health Records

**Medical Profile:**
| Component | Description | Access Control |
|-----------|-------------|----------------|
| Blood Type | For emergency medical situations | Medical + Admin |
| Allergies | Food, medication, environmental | Medical + Coaches |
| Chronic Conditions | Asthma, diabetes, etc. | Medical + Coaches |
| Medications | Current prescriptions | Medical only |
| Dietary Requirements | Vegetarian, halal, allergies | Coaches + Catering |

**Injury History:**
| Field | Description |
|-------|-------------|
| Injury Type | Classification (muscle, bone, ligament, etc.) |
| Body Part | Specific anatomical location |
| Severity | Grade 1-3 or custom scale |
| Date Occurred | When injury happened |
| Mechanism | How it occurred |
| Treatment | Medical intervention received |
| Recovery Timeline | Expected and actual return dates |
| Clearance Status | Medical clearance for activity |

**Vaccination & Medical Clearances:**
| Document | Validity | Verification |
|----------|----------|--------------|
| Annual Physical | 12 months | Physician signature |
| Concussion Baseline | 24 months | Certified provider |
| Cardiac Screening | Per regulations | Cardiologist clearance |
| Vaccinations | As required | Health authority records |

---

#### 5.2.5 Membership Information

**Current Membership:**
| Field | Description |
|-------|-------------|
| Membership ID | Unique identifier within organization |
| Membership Type | Full/Associate/Trial/Guest |
| Start Date | When membership began |
| Expiry Date | When renewal required |
| Status | Active/Suspended/Expired/Cancelled |
| Payment Status | Paid/Partial/Overdue |

**Membership Benefits:**
- Access to facilities
- Training session allocations
- Competition eligibility
- Equipment provision
- Insurance coverage

**Registration Documents:**
| Document | Purpose | Status |
|----------|---------|--------|
| Registration Form | Official enrollment | Required |
| Photo Release | Media usage consent | Required for minors |
| Code of Conduct | Behavioral agreement | Required |
| Medical Release | Emergency treatment consent | Required for minors |
| Liability Waiver | Risk acknowledgment | Required |

---

#### 5.2.6 Next of Kin & Emergency Contacts

**Primary Emergency Contact:**
| Field | Description |
|-------|-------------|
| Full Name | Contact's legal name |
| Relationship | Parent/Guardian/Spouse/Sibling/Other |
| Phone (Primary) | Mobile number |
| Phone (Alternative) | Home or work number |
| Email | Electronic contact |
| Address | If different from player |

**Secondary Emergency Contact:**
| Field | Description |
|-------|-------------|
| Full Name | Backup contact name |
| Relationship | Relationship to player |
| Phone | Contact number |
| Authorization Level | Full/Medical Only/None |

**Emergency Protocols:**
- Order of contact priority
- Medical decision authority
- Pickup authorization (for minors)
- Communication preferences

---

### 5.3 Profile Lifecycle

```
Registration          Activation           Active                  Transition
    │                     │                   │                        │
    ▼                     ▼                   │                        ▼
┌─────────┐         ┌──────────┐             │              ┌─────────────────┐
│ Draft   │────────▶│ Pending  │─────────────┼─────────────▶│ Transfer/Alumni │
│ Profile │         │ Approval │             │              │ Archive/Inactive │
└─────────┘         └──────────┘             │              └─────────────────┘
                          │                   │
                          ▼                   │
                    ┌──────────┐              │
                    │ Verified │──────────────┘
                    │  Active  │
                    └──────────┘
                          │
                          ▼
                    ┌──────────┐
                    │ Ongoing  │
                    │ Updates  │
                    └──────────┘
```

**Draft:** Initial information entry, incomplete
**Pending Approval:** Awaiting verification (documents, payment, consent)
**Verified Active:** Fully enrolled, eligible for all activities
**Updates:** Continuous enrichment with performance data, assessments
**Transfer:** Moving to different organization
**Alumni:** Former member, historical record preserved
**Inactive:** Dormant membership, data retained per policy

---

### 5.4 Self-Registration Flow

Players and parents can self-register through a guided onboarding:

1. **Account Creation** → Email/phone verification
2. **Organization Search** → Find and select club/school
3. **Profile Entry** → Basic identity information
4. **Document Upload** → Required forms and photos
5. **Consent Submission** → Guardian approval (if minor)
6. **Payment** → Membership fees (if applicable)
7. **Verification** → Admin review and approval
8. **Welcome** → Onboarding to platform features

---

## 6. Performance Metrics & Analytics

### 6.1 Metrics Philosophy

AfroLete captures performance data at multiple levels of granularity, from individual technical actions to season-long trends. The system is designed to:

- **Capture Everything**: Record every measurable aspect of training and competition
- **Surface Insights**: Transform raw data into actionable coaching intelligence
- **Track Progress**: Show improvement over time, not just snapshots
- **Enable Comparison**: Benchmark against peers, norms, and personal bests

### 6.2 Metric Categories

#### 6.2.1 Physical Performance Metrics

**Speed & Acceleration:**
| Metric | Description | Unit | Collection Method |
|--------|-------------|------|-------------------|
| Top Speed | Maximum velocity achieved | m/s or km/h | GPS, video analysis |
| Acceleration | Rate of speed increase | m/s² | GPS, timing gates |
| Sprint Times | Fixed distance performance | seconds | Timing gates, video |
| Speed Endurance | Ability to maintain speed | % decay | Repeated sprint tests |

**Endurance & Conditioning:**
| Metric | Description | Unit | Collection Method |
|--------|-------------|------|-------------------|
| Distance Covered | Total ground covered | meters | GPS tracking |
| High-Intensity Distance | Distance above threshold | meters | GPS with zones |
| Work Rate | Activity per time period | m/min | GPS tracking |
| Recovery Time | Return to baseline HR | seconds | Heart rate monitor |
| VO2 Max Estimate | Aerobic capacity | ml/kg/min | Field tests |

**Strength & Power:**
| Metric | Description | Unit | Collection Method |
|--------|-------------|------|-------------------|
| Vertical Jump | Explosive leg power | cm | Jump mat, video |
| Throwing Distance | Upper body power | meters | Measured throw |
| Change of Direction | Agility metric | seconds | Timed test |
| Force Production | Peak force output | Newtons | Force plate |

---

#### 6.2.2 Technical/Skill Metrics (Sport-Specific)

**Football/Soccer:**
| Metric | Description |
|--------|-------------|
| Pass Completion % | Successful passes / total passes |
| Pass Accuracy by Type | Short/medium/long/through ball success |
| Touches per Game | Ball contact frequency |
| Dribble Success Rate | Successful take-ons / attempts |
| Shot Accuracy | Shots on target / total shots |
| Expected Goals (xG) | Shot quality based on position |
| Tackle Success Rate | Successful tackles / attempts |
| Aerial Duel Win % | Headers won / contested |

**Basketball:**
| Metric | Description |
|--------|-------------|
| Points per Game | Scoring average |
| Field Goal % | Made shots / attempted |
| 3-Point % | Three-pointers made / attempted |
| Free Throw % | Free throws made / attempted |
| Rebounds per Game | Total rebounds |
| Assists per Game | Passes leading to scores |
| Steals & Blocks | Defensive plays |
| Player Efficiency Rating | Composite performance |

**Athletics (Track & Field):**
| Metric | Description |
|--------|-------------|
| Personal Best | Best recorded performance |
| Season Best | Best in current season |
| Consistency Index | Variation in performances |
| Reaction Time | Start response (sprints) |
| Split Times | Intermediate times in race |
| Technical Scores | Form evaluation (jumps, throws) |

**Rugby:**
| Metric | Description |
|--------|-------------|
| Tackles Made/Missed | Defensive effectiveness |
| Carry Meters | Ground gained with ball |
| Offloads | Passes in contact |
| Lineout Success % | Set piece accuracy |
| Scrum Success % | Scrum outcomes |
| Turnovers Won/Lost | Possession changes |

---

#### 6.2.3 Tactical Metrics

**Positioning & Movement:**
| Metric | Description |
|--------|-------------|
| Heat Map | Spatial distribution of activity |
| Average Position | Mean location during play |
| Zone Coverage | Time spent in different areas |
| Movement Patterns | Common runs and routes |
| Off-Ball Runs | Movement without possession |

**Decision Making:**
| Metric | Description |
|--------|-------------|
| Decision Time | Speed of action selection |
| Option Selection | Chosen action vs. alternatives |
| Risk Assessment | Conservative vs. aggressive choices |
| Game Reading | Anticipation and positioning |

**Team Coordination:**
| Metric | Description |
|--------|-------------|
| Team Shape | Formation compactness |
| Press Intensity | Collective defensive actions |
| Passing Networks | Connection patterns |
| Combination Play | Linked actions with teammates |

---

#### 6.2.4 Psychological & Cognitive Metrics

**Mental Performance:**
| Metric | Description | Collection |
|--------|-------------|------------|
| Confidence Index | Self-reported confidence | Survey |
| Focus Rating | Concentration assessment | Coach observation |
| Resilience Score | Response to adversity | Behavioral analysis |
| Coachability | Receptiveness to feedback | Coach rating |
| Leadership Display | Team influence behaviors | Peer/coach rating |

**Game Intelligence:**
| Metric | Description | Collection |
|--------|-------------|------------|
| Situational Awareness | Environmental reading | Video review |
| Adaptive Thinking | Adjusting to changing conditions | Coach assessment |
| Communication | Verbal/non-verbal team coordination | Observation |

---

### 6.3 Metric Collection Methods

#### 6.3.1 Automated Collection

**Video Analysis (AI-Powered):**
- Player tracking and identification
- Action recognition (passes, shots, tackles)
- Biomechanical analysis (running form, shooting technique)
- Spatial mapping and heat generation

**Wearable Integration:**
- GPS trackers (Catapult, STATSports, Playertek)
- Heart rate monitors (Polar, Garmin)
- Accelerometers for impact detection
- Sleep and recovery trackers

**Timing Systems:**
- Electronic timing gates
- Pressure mats
- Photo finish systems

#### 6.3.2 Manual Collection

**Coach Evaluation:**
- Technical skill ratings (1-10 scales)
- Tactical understanding assessments
- Effort and attitude scores
- Match performance grades

**Self-Assessment:**
- Training session RPE (Rate of Perceived Exertion)
- Wellness questionnaires
- Goal achievement tracking
- Reflection journals

**Official Statistics:**
- Match scoresheets
- Competition results
- Official rankings

---

### 6.4 Performance Scoring System

AfroLete uses a unified scoring system to make diverse metrics comparable and understandable:

#### 6.4.1 AfroLete Score (ALS)

A composite performance score (0-100) calculated from weighted metrics:

```
ALS = (Physical × 0.25) + (Technical × 0.35) + (Tactical × 0.25) + (Mental × 0.15)
```

**Score Interpretation:**
| Range | Rating | Interpretation |
|-------|--------|----------------|
| 90-100 | Elite | Top 1% of peer group |
| 80-89 | Excellent | Top 10% performer |
| 70-79 | Good | Above average |
| 60-69 | Developing | Meeting expectations |
| 50-59 | Emerging | Room for growth |
| <50 | Foundation | Building basics |

#### 6.4.2 Improvement Index

Tracks rate of progress over time:

```
Improvement Index = (Current ALS - Baseline ALS) / Time Period
```

Displayed as:
- **Trending Up** (significant improvement)
- **Stable** (maintaining level)
- **Needs Attention** (declining or stagnant)

#### 6.4.3 Percentile Rankings

Compare athletes within:
- Same team
- Same age group
- Same position
- Regional cohort
- National norms (where available)

---

### 6.5 Analytics Dashboards

#### 6.5.1 Player Dashboard

**Overview Card:**
- Current ALS score with trend
- Recent activity summary
- Next training/match
- Key improvement areas

**Performance Graph:**
- Time-series of ALS and components
- Toggle between metrics
- Compare to personal best

**Radar Chart:**
- Multi-dimensional skill visualization
- Compare to position ideal
- Track changes over time

**Achievement Gallery:**
- Personal bests
- Milestones reached
- Badges earned

#### 6.5.2 Coach Dashboard

**Team Overview:**
- Squad average metrics
- Individual standouts
- Injury status
- Availability

**Comparison Tools:**
- Side-by-side player comparison
- Formation optimization
- Selection recommendations

**Training Effectiveness:**
- Session load tracking
- Periodization view
- Adaptation monitoring

#### 6.5.3 Organization Dashboard

**Program Health:**
- Enrollment trends
- Retention rates
- Performance distribution

**Competitive Results:**
- Win/loss records
- League standings
- Tournament progress

**Financial Metrics:**
- Revenue per athlete
- Cost per activity
- Outstanding balances

---

## 7. AI-Powered Data Ingestion

### 7.1 Overview

AfroLete's core innovation is the ability to ingest unstructured data (video, audio, text) and automatically extract meaningful performance metrics. This removes the burden of manual data entry and enables comprehensive analytics at scale.

### 7.2 Video Analysis Pipeline

#### 7.2.1 Video Input

**Supported Sources:**
| Source | Format | Max Duration | Max Resolution |
|--------|--------|--------------|----------------|
| Mobile Upload | MP4, MOV | 120 minutes | 4K |
| Webcam Stream | WebRTC | Live | 1080p |
| External URL | MP4, HLS | 180 minutes | 4K |
| Drone Footage | MP4 | 60 minutes | 4K |
| Broadcast Feed | RTMP | Live | 1080p |

**Upload Process:**
1. Select video file or stream source
2. Tag with metadata (date, event type, teams, players)
3. Choose analysis type (full match, training drill, highlight)
4. Submit for processing
5. Receive notification when complete

#### 7.2.2 Video Processing Pipeline

```
Input Video
     │
     ▼
┌─────────────┐
│ Preprocessing │ ← Stabilization, lens correction, quality enhancement
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Detection  │ ← Object detection (players, ball, goals/baskets)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Tracking   │ ← Multi-object tracking across frames
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Mapping    │ ← Homography to standard field coordinates
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Recognition │ ← Action classification (pass, shot, tackle)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Pose Est.  │ ← Biomechanical pose estimation
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Metrics    │ ← Calculate speed, distance, efficiency
└──────┬──────┘
       │
       ▼
Output: Structured Performance Data + Annotated Video
```

#### 7.2.3 Detection Models

**Qwen3-VL Multimodal Analysis (via Ollama):**

The platform uses Qwen3-VL, a state-of-the-art vision-language model, for comprehensive video analysis:

**Capabilities:**
- Players (with jersey number recognition via OCR)
- Ball/puck tracking (sport-specific)
- Field markings (for calibration and homography)
- Goals, baskets, boundaries detection
- Referees identification (for exclusion from player stats)
- Action classification with natural language descriptions

**Processing Approach:**
```python
# Frame-by-frame analysis with Qwen3-VL
async def analyze_frame(frame: bytes, context: dict) -> FrameAnalysis:
    prompt = f"""Analyze this sports frame:
    Sport: {context['sport']}
    Previous detections: {context['previous_frame']}

    Identify:
    1. All players with positions (x,y), jersey numbers if visible
    2. Ball/equipment position
    3. Current action being performed
    4. Player movements and directions
    """

    response = await ollama.generate(
        model="qwen3-vl:72b",
        prompt=prompt,
        images=[frame],
        options={"temperature": 0.1}  # Low temp for consistency
    )
    return parse_detection_response(response)
```

**Accuracy Targets:**
| Object | Detection Rate | False Positive Rate |
|--------|----------------|---------------------|
| Players | >95% | <2% |
| Ball | >90% | <5% |
| Field Lines | >98% | <1% |
| Actions | >85% | <10% |

#### 7.2.4 Tracking & Temporal Coherence

**Multi-Frame Tracking:**
- Qwen3-VL with temporal context (previous N frames)
- Player identity maintenance across occlusions
- Trajectory smoothing and interpolation
- Jersey number + appearance feature matching

**Output:**
- Player positions at configurable FPS (default 2-5 fps for efficiency)
- Movement trajectories
- Speed and acceleration vectors (derived)
- Distance traveled (accumulated)
- Action sequences with timestamps

#### 7.2.5 Action Recognition

**Detected Actions by Sport:**

| Football | Basketball | Athletics | Rugby |
|----------|------------|-----------|-------|
| Pass | Shot | Sprint start | Tackle |
| Shot | Rebound | Stride pattern | Carry |
| Tackle | Assist | Jump phase | Pass |
| Dribble | Steal | Release point | Ruck |
| Cross | Block | Landing | Lineout |
| Header | Turnover | Turn technique | Scrum |

**Classification Confidence:**
- Only actions with >80% confidence are recorded
- Lower-confidence actions flagged for human review

#### 7.2.6 Biomechanical Analysis

**Pose Estimation (17-point skeleton):**
- Joint positions (shoulders, elbows, wrists, hips, knees, ankles)
- Joint angles during movements
- Body alignment and posture
- Asymmetry detection

**Biomechanical Metrics:**
| Metric | Description | Use Case |
|--------|-------------|----------|
| Stride Length | Distance per step | Running efficiency |
| Stride Frequency | Steps per second | Cadence optimization |
| Knee Drive | Hip flexion angle | Sprint power |
| Arm Swing | Shoulder rotation | Balance and drive |
| Landing Mechanics | Joint angles at impact | Injury prevention |
| Throwing Angle | Release point analysis | Technique optimization |

---

### 7.3 Audio Narration Processing

#### 7.3.1 Use Case

Coaches can narrate training sessions or matches using voice recordings, and AfroLete will extract performance observations automatically.

**Example Narration:**
> "Kwame showed excellent positioning today, always finding space. His first touch needs work though—lost possession three times because of heavy touches. Scored two goals from inside the box, both with his right foot. Should practice left foot finishing."

**Extracted Data:**
| Metric | Value | Confidence |
|--------|-------|------------|
| Positioning rating | Excellent (8/10) | 92% |
| First touch rating | Needs work (5/10) | 88% |
| Possession lost | 3 | 95% |
| Goals scored | 2 | 98% |
| Shot locations | Inside box | 90% |
| Dominant foot | Right | 95% |
| Training recommendation | Left foot finishing | 87% |

#### 7.3.2 Audio Processing Pipeline

```
Audio Input (MP3, WAV, M4A)
        │
        ▼
┌─────────────────────┐
│ Azure Speech Services│ ← Real-time transcription with speaker diarization
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Azure OpenAI GPT-4o │ ← Entity extraction, sentiment, structured parsing
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Metric Mapping     │ ← Map observations to performance metrics
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Player Linking     │ ← Associate with player profiles via name matching
└─────────┬───────────┘
          │
          ▼
Output: Structured Observations + Recommendations
```

**Azure Speech Configuration:**
```typescript
const speechConfig = {
  endpoint: process.env.AZURE_SPEECH_ENDPOINT,
  subscriptionKey: process.env.AZURE_SPEECH_KEY,
  speechRecognitionLanguage: "en-US", // Multi-language support
  enableDiarization: true,  // Identify multiple speakers
  profanityOption: "raw",   // Keep original for accuracy
  outputFormat: "detailed"  // Include confidence scores
};
```

#### 7.3.3 Supported Languages

- English (all variants)
- French
- Spanish
- Portuguese
- Swahili
- Arabic
- Additional languages via configuration

---

### 7.4 Text Evaluation Processing

#### 7.4.1 Evaluation Forms

Structured and unstructured text evaluations are processed:

**Structured Input:**
```json
{
  "player_id": "abc123",
  "session_date": "2026-01-15",
  "evaluator": "Coach Maria",
  "ratings": {
    "technical_skill": 7,
    "tactical_awareness": 6,
    "physical_performance": 8,
    "mental_attitude": 9
  },
  "comments": "Strong session overall. Needs to communicate more with teammates during defensive transitions."
}
```

**Free-Form Input:**
> "Today's training with the U-14s went well. Emma was outstanding—best performance of the season. Her crossing accuracy has improved dramatically since we started the focused drill work. James struggled with the pressing exercises, seemed fatigued. Might need to check his sleep/recovery. Overall team shape in the 4-3-3 is coming together."

#### 7.4.2 Text Processing Capabilities

| Capability | Description |
|------------|-------------|
| Player Mention Detection | Identifies player names in text |
| Sentiment Analysis | Positive/negative/neutral observations |
| Metric Extraction | Quantitative values from text |
| Recommendation Extraction | Suggested actions and focus areas |
| Temporal Context | Associates observations with dates/events |

---

### 7.5 Data Quality & Verification

#### 7.5.1 Confidence Scoring

All AI-extracted data includes confidence scores:

| Confidence | Action |
|------------|--------|
| >90% | Automatically recorded |
| 70-90% | Recorded with review flag |
| <70% | Queued for human verification |

#### 7.5.2 Human-in-the-Loop

**Review Interface:**
- AI-highlighted video segments with proposed metrics
- One-click confirm or correct
- Bulk approval for high-confidence data
- Correction feedback improves models

#### 7.5.3 Data Provenance

Every metric includes:
- Source (video, audio, manual, wearable)
- Collection timestamp
- Processing model version
- Confidence score
- Human verification status

---

## 8. Training & Coaching System

### 8.1 AI-Powered Training Plan Generation

#### 8.1.1 Plan Generation Engine

AfroLete's AI analyzes player performance data to generate personalized training recommendations:

**Inputs:**
- Current performance metrics
- Historical improvement trends
- Identified weaknesses
- Upcoming competition schedule
- Available training time
- Physical readiness status

**Outputs:**
- Weekly training focus areas
- Specific drill recommendations
- Load management guidelines
- Recovery protocols
- Progress checkpoints

#### 8.1.2 Plan Components

**Macro Cycle (Season Plan):**
```
Pre-Season (8 weeks)
    │
    ├── Foundation Phase (3 weeks): Build base fitness
    ├── Development Phase (3 weeks): Technical focus
    └── Competition Prep (2 weeks): Match sharpness

Competition Season (24 weeks)
    │
    ├── Recurring weekly structure
    ├── Load management based on fixtures
    └── Targeted skill work around matches

Off-Season (8 weeks)
    │
    ├── Active Recovery (2 weeks)
    ├── Address Weaknesses (4 weeks)
    └── Pre-Pre-Season Build (2 weeks)
```

**Micro Cycle (Weekly Plan):**
| Day | Focus | Intensity | Duration |
|-----|-------|-----------|----------|
| Monday | Recovery + Light Technical | Low | 45 min |
| Tuesday | Tactical + Team Shape | Medium | 75 min |
| Wednesday | Physical Conditioning | High | 60 min |
| Thursday | Technical Skills | Medium | 60 min |
| Friday | Match Preparation | Low | 45 min |
| Saturday | **Match Day** | Competition | -- |
| Sunday | Rest | -- | -- |

#### 8.1.3 Drill Library

**Structure:**
- 500+ drills across 15+ sports
- Tagged by skill focus, age appropriateness, equipment needed
- Video demonstrations and coaching points
- Progression variants (easier/harder)

**Drill Recommendation Algorithm:**
```
For each identified weakness:
    1. Find drills targeting that skill
    2. Filter by age/level appropriateness
    3. Check equipment availability
    4. Avoid recent repetition (variety)
    5. Balance with other session objectives
    6. Rank by expected improvement impact
    7. Present top 3 options to coach
```

---

### 8.2 Session Planning Tools

#### 8.2.1 Session Builder

**Drag-and-Drop Interface:**
- Browse drill library
- Drag drills to session timeline
- Adjust duration and intensity
- Add custom notes and variations
- Preview total session load

**Session Template:**
```
┌─────────────────────────────────────────────┐
│ Session: Tuesday Technical Training          │
│ Date: 2026-01-21 | Duration: 75 min         │
├─────────────────────────────────────────────┤
│ Warm-Up (15 min)                            │
│   • Dynamic stretching                      │
│   • Rondos in small groups                  │
├─────────────────────────────────────────────┤
│ Technical Block (30 min)                    │
│   • Passing accuracy drill (15 min)         │
│   • First touch under pressure (15 min)     │
├─────────────────────────────────────────────┤
│ Game-Related Practice (20 min)              │
│   • 7v7 with focus on build-up play         │
├─────────────────────────────────────────────┤
│ Cool-Down (10 min)                          │
│   • Light jog and static stretching         │
├─────────────────────────────────────────────┤
│ Total Load Score: 72 (Medium-High)          │
└─────────────────────────────────────────────┘
```

#### 8.2.2 Load Management

**Acute:Chronic Workload Ratio:**
- Track weekly training load (duration × intensity)
- Calculate rolling 4-week chronic load
- Alert when acute:chronic ratio exceeds safe thresholds
- Prevent overtraining and injury risk

**Load Calculation:**
```
Session Load = Duration (min) × RPE (1-10)

Weekly Load = Σ Session Loads

Acute:Chronic Ratio = Current Week / 4-Week Average

Safe Zone: 0.8 - 1.3
Danger Zone: <0.8 or >1.5
```

---

### 8.3 Performance Feedback Loop

#### 8.3.1 Pre-Session

**Player Check-In:**
- Wellness questionnaire (sleep, energy, soreness)
- Availability confirmation
- Session objectives preview

**Coach Preparation:**
- Review AI-recommended focus areas
- Check player readiness scores
- Adjust session plan if needed

#### 8.3.2 During Session

**Live Capture:**
- Video recording (if enabled)
- Coach voice notes
- Real-time metrics (if wearables connected)

#### 8.3.3 Post-Session

**Data Collection:**
- Video upload and processing
- Player self-assessment (RPE, effort rating)
- Coach observations (text or audio)

**Analysis:**
- AI extraction of performance metrics
- Comparison to session objectives
- Update to player profiles and plans

**Feedback Delivery:**
- Automated summary to players
- Highlight clips with coaching points
- Progress toward goals updated

---

### 8.4 Coaching Resources

#### 8.4.1 Knowledge Base

**Content Library:**
- Coaching methodologies and philosophy
- Age-appropriate development guidelines
- Sport-specific technical guides
- Tactical frameworks and systems
- Sport psychology resources

#### 8.4.2 Coach Development

**Features:**
- Coaching certification tracking
- Professional development courses
- Peer coaching observations
- Mentor matching

#### 8.4.3 Playbook Builder

**Capabilities:**
- Visual play diagramming
- Animation of movements
- Assignment to players
- In-app sharing during matches

---

## 9. Competition Management

### 9.1 Competition Types

AfroLete supports comprehensive management of all competition formats:

#### 9.1.1 Matches (Individual Games)

**Match Types:**
- League fixture
- Cup/knockout match
- Friendly/exhibition
- Training match (internal)

**Match Record:**
| Field | Description |
|-------|-------------|
| Competition | Parent league/tournament |
| Home Team | Host team |
| Away Team | Visiting team |
| Date & Time | Scheduled kick-off |
| Venue | Location details |
| Officials | Referees assigned |
| Result | Final score |
| Statistics | Player and team stats |
| Events | Goals, cards, substitutions |

#### 9.1.2 Leagues

**League Configuration:**
| Setting | Options |
|---------|---------|
| Format | Round-robin (single/double), Swiss |
| Teams | Number of participants |
| Duration | Season dates |
| Match Rules | Points for win/draw/loss |
| Tiebreakers | Goal difference, head-to-head, etc. |
| Divisions | Promotion/relegation rules |

**League Table:**
| Pos | Team | P | W | D | L | GF | GA | GD | Pts |
|-----|------|---|---|---|---|----|----|----|----|
| 1 | Team A | 10 | 8 | 1 | 1 | 25 | 8 | +17 | 25 |
| 2 | Team B | 10 | 7 | 2 | 1 | 22 | 10 | +12 | 23 |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

#### 9.1.3 Tournaments

**Tournament Formats:**
| Format | Description | Use Case |
|--------|-------------|----------|
| Single Elimination | Lose once, out | Quick cup competitions |
| Double Elimination | Two losses to eliminate | Fairer knockout |
| Group + Knockout | Pool play then brackets | World Cup style |
| Swiss | Pair by performance | Chess-style pairing |
| Round Robin | Everyone plays everyone | Small field, comprehensive |

**Bracket Management:**
- Visual bracket display
- Automatic advancement
- Seeding configuration
- Bye handling

#### 9.1.4 Fixtures

**Fixture Generation:**
- AI-optimized scheduling
- Constraint handling:
  - Venue availability
  - Team availability
  - Travel distance minimization
  - Rest day requirements
  - Television/broadcast preferences

**Fixture Conflicts:**
- Automatic detection
- Resolution suggestions
- Manual override capability
- Notification to affected parties

---

### 9.2 Scheduling Engine

#### 9.2.1 Constraint-Based Optimization

The scheduling engine uses integer linear programming to optimize fixture allocation:

**Hard Constraints (Must Satisfy):**
- No team plays twice on same day
- Venue capacity limits
- Minimum rest between matches
- Competition rules compliance

**Soft Constraints (Optimize):**
- Minimize total travel distance
- Balance home/away sequences
- Avoid consecutive difficult opponents
- Respect preferred time slots

#### 9.2.2 Schedule Generation Process

```
Input Constraints
       │
       ▼
┌────────────────┐
│ Feasibility    │ ← Check if schedule is possible
│ Check          │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ Initial        │ ← Generate baseline schedule
│ Solution       │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ Optimization   │ ← Improve based on soft constraints
│ Loop           │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ Conflict       │ ← Identify remaining issues
│ Detection      │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ Manual         │ ← Human review and adjustment
│ Adjustment     │
└───────┬────────┘
        │
        ▼
Output: Finalized Schedule
```

#### 9.2.3 Rescheduling

**Triggers:**
- Weather cancellation
- Team withdrawal
- Venue unavailability
- COVID/health protocols

**Process:**
1. Identify affected matches
2. Find available alternative slots
3. Check constraint satisfaction
4. Propose options to administrators
5. Notify all parties of changes

---

### 9.3 Live Match Management

#### 9.3.1 Match Day Interface

**Pre-Match:**
- Team sheet submission
- Player eligibility verification
- Referee assignment confirmation
- Weather and venue check

**During Match:**
- Live scoring input
- Event logging (goals, cards, substitutions)
- Timer management
- Real-time statistics

**Post-Match:**
- Final score confirmation
- Match report submission
- Statistics finalization
- Media attachment (photos, video highlights)

#### 9.3.2 Scoring Interface

**Mobile-Optimized Design:**
```
┌─────────────────────────────────────┐
│     HOME        2 - 1      AWAY     │
│     Team A              Team B      │
├─────────────────────────────────────┤
│  ⏱️ 67:32    Half: 2nd              │
├─────────────────────────────────────┤
│ Quick Actions:                      │
│  [⚽ Goal]  [🟨 Card]  [🔄 Sub]     │
│  [⏸️ Pause] [📝 Note] [🏁 End]     │
├─────────────────────────────────────┤
│ Match Events:                       │
│  65' 🟨 J. Smith (Team A)           │
│  54' ⚽ A. Jones (Team B)           │
│  32' ⚽ K. Brown (Team A)           │
│  11' ⚽ K. Brown (Team A)           │
└─────────────────────────────────────┘
```

#### 9.3.3 Live Streaming Integration

**Capabilities:**
- Embed live score widget in streams
- Push notifications for events
- Real-time statistics overlay
- Social media auto-posting

---

### 9.4 Results & Standings

#### 9.4.1 Automatic Updates

- League tables update instantly on result entry
- Qualification scenarios calculated
- Playoff pictures generated
- Records and streaks tracked

#### 9.4.2 Statistics Aggregation

**Individual Statistics:**
- Goals/points scored
- Assists
- Clean sheets (goalkeepers)
- Minutes played
- Cards received
- Match ratings

**Team Statistics:**
- Win/loss/draw record
- Goals for/against
- Home vs. away performance
- Form (last 5 matches)
- Head-to-head records

---

### 9.5 Official Management

#### 9.5.1 Referee Assignment

**Assignment Factors:**
- Certification level
- Availability
- Travel distance
- Conflict of interest checks
- Fair distribution of matches

#### 9.5.2 Official Portal

**Features:**
- Assignment calendar
- Match acceptance/decline
- Travel expense submission
- Match report submission
- Availability management

---

## 10. Communications & Parental Consent

### 10.1 Communication System

#### 10.1.1 Message Types

| Type | Purpose | Recipients | Urgency |
|------|---------|------------|---------|
| Announcement | General information | Group/team | Normal |
| Alert | Time-sensitive updates | Individuals/groups | High |
| Reminder | Upcoming events | Affected parties | Normal |
| Request | Action required | Individuals | High |
| Report | Performance updates | Players/parents | Normal |

#### 10.1.2 Communication Channels

**In-App Messaging:**
- Direct messages (1:1)
- Group conversations (team chat)
- Broadcast messages (one-to-many)
- Read receipts and delivery confirmation

**Push Notifications:**
- Mobile app alerts
- Configurable preferences
- Smart timing (respects quiet hours)
- Action buttons for quick response

**Email:**
- Scheduled digests
- Important announcements
- Formal communications
- Document delivery

**SMS (Optional Integration):**
- Emergency alerts
- Last-minute changes
- Confirmation codes

#### 10.1.3 Communication Templates

**Pre-Built Templates:**
- Training session reminder
- Match day information
- Schedule change notification
- Payment reminder
- Welcome message
- Season end summary

**Template Variables:**
```
Hello {player.first_name},

This is a reminder that {team.name} has a {event.type}
on {event.date} at {event.time}.

Location: {venue.name}
Address: {venue.address}

Please confirm your attendance: {attendance_link}

{coach.name}
```

---

### 10.2 Parental Consent Framework

#### 10.2.1 Consent Types

| Consent | Description | Validity | Renewal |
|---------|-------------|----------|---------|
| Registration | General participation consent | Annual | Season start |
| Medical | Emergency treatment authorization | Annual | Season start |
| Photo/Video | Media capture and usage | Annual | Season start |
| Travel | Away matches and trips | Per-event | As needed |
| Competition | Specific tournament entry | Per-event | As needed |
| Data Processing | GDPR/privacy consent | Ongoing | Policy change |

#### 10.2.2 Consent Workflow

**Digital Consent Process:**
```
Coach/Admin Creates Request
           │
           ▼
    ┌──────────────┐
    │ Request Sent │ ← Email/push to parent
    │ to Parent    │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Parent       │ ← Reviews details
    │ Reviews      │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Digital      │ ← E-signature capture
    │ Signature    │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Confirmation │ ← Stored with timestamp
    │ Recorded     │
    └──────┬───────┘
           │
           ▼
    Athlete Eligible for Activity
```

#### 10.2.3 Consent Request Interface

**Parent View:**
```
┌─────────────────────────────────────────────┐
│ 📋 Consent Request                          │
├─────────────────────────────────────────────┤
│ From: Riverside Football Club               │
│ Regarding: Emma Johnson                     │
│ Type: Travel Permission                     │
├─────────────────────────────────────────────┤
│ Details:                                    │
│                                             │
│ We request permission for Emma to travel    │
│ with the U-14 Girls team to the Regional    │
│ Championship on February 15-16, 2026.       │
│                                             │
│ Destination: Nairobi Sports Complex         │
│ Departure: Feb 15, 6:00 AM                  │
│ Return: Feb 16, 8:00 PM                     │
│ Transport: Club minibus                     │
│ Supervision: 3 coaches, 2 parents           │
│                                             │
│ Emergency Contact During Trip:              │
│ Coach Maria: +254 XXX XXX XXX               │
│                                             │
│ [View Full Itinerary]                       │
├─────────────────────────────────────────────┤
│ ☐ I have read and understood the above      │
│                                             │
│ Signature: ____________________             │
│                                             │
│ [✓ Approve]           [✗ Decline]           │
└─────────────────────────────────────────────┘
```

#### 10.2.4 Consent Status Tracking

**Dashboard View:**
| Player | Registration | Medical | Photo | Travel (Feb 15) |
|--------|--------------|---------|-------|-----------------|
| Emma J. | ✅ Approved | ✅ Approved | ✅ Approved | ⏳ Pending |
| James K. | ✅ Approved | ✅ Approved | ❌ Declined | ✅ Approved |
| Sarah L. | ✅ Approved | ⏳ Pending | ✅ Approved | ⏳ Pending |

**Automated Reminders:**
- First request: Immediate
- First reminder: 3 days before deadline
- Urgent reminder: 1 day before deadline
- Escalation: Flag to administrator

---

### 10.3 Communication Policies

#### 10.3.1 Minor Protection

**Safeguarding Rules:**
- Coaches cannot message minors directly
- All communications CC parent/guardian
- No private 1:1 video calls with minors
- Message history retained for audit

#### 10.3.2 Communication Preferences

**Parent Settings:**
| Preference | Options |
|------------|---------|
| Notification frequency | Immediate / Daily digest / Weekly |
| Channel preference | App / Email / SMS / All |
| Language | Select from available |
| Quiet hours | No notifications between X-Y |
| Emergency override | Always allow urgent alerts |

---

### 10.4 Parent Portal

#### 10.4.1 Dashboard

**Key Information:**
- Child's upcoming schedule
- Recent performance highlights
- Outstanding consent requests
- Payment status
- Team announcements

#### 10.4.2 Features

| Feature | Description |
|---------|-------------|
| Schedule View | All events for child |
| Progress Reports | Performance summaries |
| Photo Gallery | Team and event photos |
| Attendance History | Participation record |
| Payment Management | Invoices and receipts |
| Consent Center | Manage all permissions |
| Communication Hub | Messages and announcements |

---

## 11. User Interface & Experience Design

### 11.1 Design Philosophy

#### 11.1.1 Core Principles

**Zero-Training Design:**
Every interface element must be immediately understandable. Users should never need instructions to:
- Navigate to key functions
- Complete common tasks
- Understand data visualizations
- Respond to notifications

**Fitts's Law Optimization:**
Minimize movement time by:
- Enlarging frequent action targets
- Placing related elements close together
- Reducing navigation depth
- Using predictive positioning

**Progressive Disclosure:**
- Show essential information first
- Reveal complexity on demand
- Don't overwhelm with options
- Guide users through workflows

#### 11.1.2 Visual Design Language

**Color System:**
| Color | Usage | Meaning |
|-------|-------|---------|
| Primary Blue | Actions, links | Interaction |
| Success Green | Positive metrics, confirmations | Good/improvement |
| Warning Amber | Attention needed | Caution |
| Error Red | Problems, declines | Issue/warning |
| Neutral Gray | Secondary content | Information |
| Background White | Canvas | Clean space |

**Typography:**
- Primary: Inter (clean, readable at all sizes)
- Headers: Bold, clear hierarchy
- Body: Regular weight, generous line height
- Data: Monospace for numbers and stats

**Iconography:**
- Consistent icon library (Lucide/Phosphor)
- Always paired with labels for clarity
- Sport-specific icons (ball, goal, etc.)
- Status indicators (check, warning, etc.)

---

### 11.2 Platform-Specific Design

#### 11.2.1 Mobile App (Primary Interface)

**Design Approach:** Mobile-first, optimized for on-the-go usage

**Navigation Structure:**
```
Bottom Tab Bar:
┌─────┬─────┬─────┬─────┬─────┐
│Home │Teams│Events│ Stats │Profile│
└─────┴─────┴─────┴─────┴─────┘
```

**Screen Types:**
| Screen | Purpose | Key Elements |
|--------|---------|--------------|
| Home | Dashboard overview | Today's schedule, alerts, quick stats |
| Team | Team management | Roster, schedule, communication |
| Events | Calendar and fixtures | Day/week/month views, event details |
| Stats | Performance analytics | Player/team metrics, trends |
| Profile | Account management | Settings, notifications, support |

**Mobile Optimizations:**
- Large tap targets (minimum 44pt)
- Swipe gestures for common actions
- Pull-to-refresh
- Offline capability for key features
- Camera integration for video capture

#### 11.2.2 Web Application

**Design Approach:** Full-featured dashboard for administration

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│ Header: Logo | Search | Notifications | Profile        │
├─────────┬───────────────────────────────────────────────┤
│         │                                               │
│ Side    │        Main Content Area                      │
│ Nav     │                                               │
│         │                                               │
│ • Home  │   ┌─────────────────────────────────────┐     │
│ • Teams │   │  Cards / Tables / Charts            │     │
│ • Players│   │                                     │     │
│ • Events│   └─────────────────────────────────────┘     │
│ • Reports│                                              │
│ • Settings│                                             │
│         │                                               │
└─────────┴───────────────────────────────────────────────┘
```

**Web-Specific Features:**
- Keyboard shortcuts for power users
- Multi-window workflows
- Drag-and-drop interfaces
- Advanced data tables with sorting/filtering
- Export capabilities (PDF, CSV, Excel)

#### 11.2.3 Tablet Interface

**Design Approach:** Hybrid mobile/desktop experience

**Use Cases:**
- Field-side performance review
- Match day management
- Session planning
- Registration check-in

**Adaptations:**
- Two-pane layouts where appropriate
- Optimized for touch and keyboard
- Landscape orientation support
- Quick access toolbar

---

### 11.3 Key Interfaces

#### 11.3.1 Dashboard (Home)

**Components:**
```
┌───────────────────────────────────────────────────┐
│ Welcome, Coach Carlos!              [🔔 3 alerts] │
├───────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────────────┐   │
│ │ Today           │ │ Quick Stats             │   │
│ │                 │ │                         │   │
│ │ 🏃 Training 4PM │ │ Team: U-14 Boys         │   │
│ │ 📍 Main Field   │ │ Players: 18 (16 active) │   │
│ │ 👥 16 confirmed │ │ Season W/L: 8-2         │   │
│ │                 │ │ Next match: Sat vs City │   │
│ └─────────────────┘ └─────────────────────────┘   │
│                                                   │
│ ┌─────────────────────────────────────────────┐   │
│ │ Recent Activity                             │   │
│ │                                             │   │
│ │ • 📹 Video analysis ready: Training Jan 14  │   │
│ │ • ✅ 2 consent forms approved               │   │
│ │ • ⚠️ 3 players missing medical clearance   │   │
│ │ • 💬 5 new messages                         │   │
│ └─────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────┘
```

#### 11.3.2 Player Profile View

**Layout:**
```
┌────────────────────────────────────────────────────────┐
│ ← Back to Team                                         │
├────────────────────────────────────────────────────────┤
│ ┌──────────┐  Kwame Mensah           #10              │
│ │  [Photo] │  Position: Forward                       │
│ │          │  Age: 14 | U-14 Boys                     │
│ └──────────┘  Status: ✅ Active & Eligible            │
├────────────────────────────────────────────────────────┤
│ [Overview] [Performance] [History] [Health] [Admin]   │
├────────────────────────────────────────────────────────┤
│                                                        │
│ AfroLete Score: 78 ↑ (+3 this month)                  │
│                                                        │
│ ┌─────────────────────────────────────────────────┐   │
│ │    [Radar Chart: Skills vs Position Average]    │   │
│ │         Speed ●                                  │   │
│ │              ╲                                   │   │
│ │   Passing ●───●───● Shooting                    │   │
│ │              ╱                                   │   │
│ │        Defending                                │   │
│ └─────────────────────────────────────────────────┘   │
│                                                        │
│ Strengths: Speed, Work Rate, Finishing                │
│ Development Areas: Passing accuracy, Left foot        │
│                                                        │
│ [View Detailed Analytics] [Generate Training Plan]    │
└────────────────────────────────────────────────────────┘
```

#### 11.3.3 Video Analysis Review

**Interface:**
```
┌────────────────────────────────────────────────────────┐
│ Video Analysis: Training Session Jan 14, 2026         │
├────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────┐  │
│ │                                                  │  │
│ │            [Video Player with Overlays]          │  │
│ │                                                  │  │
│ │    [Player tracking dots and trails shown]       │  │
│ │                                                  │  │
│ └──────────────────────────────────────────────────┘  │
│ ⏮️  ⏪  [▶️ Play]  ⏩  ⏭️     🔊 Volume    ⛶ Full      │
│ ────────────●───────────────────────── 12:45 / 45:00  │
├────────────────────────────────────────────────────────┤
│ AI Detected Events:                                    │
│                                                        │
│ ┌────────────────────────────────────────────────┐    │
│ │ 05:32 ⚽ Goal: Kwame Mensah (assisted by James) │    │
│ │ 12:45 📈 Sprint: Emma - 7.2 m/s (new PB!)      │    │
│ │ 18:20 ⚠️ Heavy touch: Kwame (possession lost)  │    │
│ │ 24:10 ✨ Great pass: Sarah (15m, accurate)     │    │
│ └────────────────────────────────────────────────┘    │
│                                                        │
│ [✅ Confirm All] [Review Flagged] [Export Report]     │
└────────────────────────────────────────────────────────┘
```

---

### 11.4 Accessibility

#### 11.4.1 WCAG 2.1 AA Compliance

**Requirements Met:**
- Color contrast ratios ≥4.5:1
- All interactive elements keyboard accessible
- Screen reader compatibility
- Focus indicators visible
- Text resizable to 200%

#### 11.4.2 Accessibility Features

| Feature | Implementation |
|---------|----------------|
| Screen Reader Support | ARIA labels on all elements |
| Color Blind Mode | Alternative color schemes |
| Font Size Control | Adjustable text sizing |
| High Contrast Mode | Enhanced visibility option |
| Reduced Motion | Respects system preferences |
| Keyboard Navigation | Full functionality without mouse |

---

### 11.5 Responsive Behavior

**Breakpoints:**
| Breakpoint | Width | Target Device |
|------------|-------|---------------|
| Mobile S | 320px | Small phones |
| Mobile | 375px | Standard phones |
| Mobile L | 428px | Large phones |
| Tablet | 768px | Tablets portrait |
| Tablet L | 1024px | Tablets landscape |
| Desktop | 1280px | Laptops |
| Desktop L | 1536px | Large monitors |

---

## 12. Reporting & Intelligence

### 12.1 Report Categories

#### 12.1.1 Performance Reports

**Individual Player Report:**
- Current performance metrics (all categories)
- Trend analysis (improvement/decline)
- Comparison to benchmarks
- Recommended development areas
- Training plan compliance

**Team Performance Report:**
- Aggregate team statistics
- Position group analysis
- Formation effectiveness
- Competitive results summary

**Competition Report:**
- Match-by-match breakdown
- Player ratings and contributions
- Tactical analysis
- Opposition scouting notes

#### 12.1.2 Administrative Reports

**Membership Report:**
- Active/inactive members
- Registration trends
- Renewal rates
- Demographics breakdown

**Financial Report:**
- Revenue by category
- Outstanding payments
- Expense tracking
- Budget vs. actual

**Compliance Report:**
- Consent status summary
- Safeguarding compliance
- Certification status (coaches)
- Incident log

#### 12.1.3 Operational Reports

**Attendance Report:**
- Training attendance rates
- Match availability
- Absence patterns
- Communication effectiveness

**Facility Utilization:**
- Booking frequency
- Peak usage times
- Maintenance schedule
- Capacity optimization

---

### 12.2 Report Generation

#### 12.2.1 On-Demand Reports

**Generation Interface:**
1. Select report type
2. Choose parameters (date range, players, teams)
3. Select output format (PDF, Excel, online)
4. Generate and download/share

#### 12.2.2 Scheduled Reports

**Automation Options:**
| Frequency | Use Case | Example |
|-----------|----------|---------|
| Daily | Activity summary | Yesterday's training recap |
| Weekly | Performance digest | Weekly stats summary |
| Monthly | Management report | Board update package |
| Quarterly | Strategic review | Season progress analysis |
| On-trigger | Event-based | Match report after game |

#### 12.2.3 Report Delivery

**Channels:**
- In-app viewing
- PDF download
- Email delivery
- Shared link (time-limited)
- API access (for integrations)

---

### 12.3 AI-Generated Insights

#### 12.3.1 Automated Observations (Azure OpenAI)

The platform uses Azure OpenAI GPT-4o to continuously analyze data and generate actionable insights:

**Insight Generation Pipeline:**
```typescript
async function generatePlayerInsights(playerId: string): Promise<Insight[]> {
  const metrics = await getRecentMetrics(playerId, { days: 30 });
  const benchmarks = await getPeerBenchmarks(playerId);

  const response = await azureOpenAI.chat.completions.create({
    model: "gpt-4o",
    messages: [{
      role: "system",
      content: `You are a sports analytics expert. Generate 3-5 actionable
                insights based on the player's performance data. Be specific,
                cite numbers, and compare to benchmarks where relevant.`
    }, {
      role: "user",
      content: JSON.stringify({ metrics, benchmarks })
    }],
    response_format: { type: "json_schema", ... }
  });

  return parseInsightsResponse(response);
}
```

**Performance Insights:**
> "Emma's sprint speed has improved 8% over the last 4 weeks, placing her in the top 10% of U-14 girls nationally."

**Risk Alerts:**
> "James's acute:chronic workload ratio is 1.6, indicating elevated injury risk. Consider reducing training load this week."

**Pattern Detection:**
> "Team performance drops 15% in the final 20 minutes of matches. Recommend enhanced conditioning focus."

#### 12.3.2 Predictive Analytics

**Injury Risk Prediction:**
- Combines workload, sleep, wellness, and historical data
- XGBoost model trained on historical injury data
- Generates daily risk scores per player (0-100)
- Triggers alerts when thresholds exceeded (>70 = warning, >85 = high risk)

**Performance Forecasting:**
- Azure OpenAI analyzes training patterns and projects future metrics
- Models "what-if" scenarios for training changes
- Generates weekly forecast reports

**Talent Identification:**
- Embeddings-based similarity search (pgvector + text-embedding-3-large)
- Flags players with exceptional improvement trajectories
- Identifies hidden potential based on metric combinations

---

### 12.4 Visualization Tools

#### 12.4.1 Chart Types

| Chart | Use Case |
|-------|----------|
| Line Graph | Trends over time |
| Bar Chart | Comparison between entities |
| Radar Chart | Multi-dimensional skill profiles |
| Heat Map | Spatial distribution |
| Scatter Plot | Correlation analysis |
| Pie/Donut | Composition breakdown |
| Gauge | Single metric against target |

#### 12.4.2 Interactive Dashboards

**Features:**
- Drag-and-drop widget arrangement
- Drill-down capability
- Filter and segment controls
- Export and share options
- Real-time data refresh

---

## 13. Security, Privacy & Compliance

### 13.1 Security Architecture

#### 13.1.1 Authentication & Authorization

**Authentication:**
- Email/password with strength requirements
- Multi-factor authentication (SMS, authenticator app)
- Social login (Google, Apple) for convenience
- Single sign-on (SSO) for enterprise tenants
- Passwordless options (magic link, biometric)

**Authorization (RBAC):**
| Role | Permissions |
|------|-------------|
| Owner | Full organization control |
| Administrator | User management, settings, reports |
| Coach | Team management, player data, scheduling |
| Player (Adult) | Personal profile, team view |
| Player (Minor) | Limited personal view |
| Parent | Child's data, consent management |
| Viewer | Read-only access to assigned content |

**Permission Granularity:**
- Organization level
- Team level
- Player level
- Data category level

#### 13.1.2 Data Protection

**Encryption:**
| State | Method |
|-------|--------|
| In Transit | TLS 1.3 minimum |
| At Rest | AES-256-GCM |
| Backups | Encrypted with separate keys |
| Sensitive Fields | Additional field-level encryption |

**Sensitive Data Handling:**
- Medical records: Encrypted, restricted access
- Financial data: PCI-DSS compliance
- Minor data: Enhanced protection per COPPA/GDPR-K

#### 13.1.3 Infrastructure Security

**Architecture:**
- Zero-trust network model
- Web Application Firewall (WAF)
- DDoS protection
- Intrusion detection systems
- Regular penetration testing

**Access Control:**
- Principle of least privilege
- Service-to-service mTLS
- Secrets management (Vault)
- Audit logging for all access

---

### 13.2 Privacy Framework

#### 13.2.1 Data Minimization

**Principles:**
- Collect only necessary data
- Define retention periods
- Automatic data purging
- Anonymization for analytics

#### 13.2.2 Privacy by Design

**Implementation:**
- Privacy impact assessments for features
- Default privacy settings favor user
- Clear consent mechanisms
- Transparent data usage explanations

#### 13.2.3 User Rights

| Right | Implementation |
|-------|----------------|
| Access | Data export in portable format |
| Rectification | Self-service profile editing |
| Erasure | Account deletion with data removal |
| Restriction | Pause data processing |
| Portability | Standard format export |
| Objection | Opt-out of specific processing |

---

### 13.3 Compliance Requirements

#### 13.3.1 Regulatory Compliance

| Regulation | Applicability | Key Requirements |
|------------|---------------|------------------|
| GDPR | EU users | Consent, data rights, DPO |
| CCPA/CPRA | California users | Disclosure, opt-out |
| COPPA | US children <13 | Parental consent, data limits |
| FERPA | US schools | Educational record protection |
| POPIA | South Africa | Lawful processing, security |
| PDPA | Various countries | Local data protection |

#### 13.3.2 Industry Standards

| Standard | Purpose | Implementation |
|----------|---------|----------------|
| SOC 2 Type II | Security & availability | Annual audit |
| ISO 27001 | Information security | Certification |
| PCI-DSS | Payment data | Compliant payment processing |

#### 13.3.3 Safeguarding

**Child Protection:**
- Background check tracking for staff
- Two-adult rule enforcement for communications
- Incident reporting system
- Training compliance tracking

---

### 13.4 Audit & Compliance Tools

#### 13.4.1 Audit Logging

**Logged Events:**
- Authentication attempts (success/failure)
- Data access (who, what, when)
- Data modifications
- Permission changes
- Consent updates
- Export/download actions

**Log Retention:**
- Security logs: 2 years
- Access logs: 1 year
- Compliance logs: 7 years

#### 13.4.2 Compliance Dashboard

**Features:**
- Consent status overview
- Outstanding compliance items
- Certification tracking
- Audit report generation
- Risk assessment tools

---

## 14. Integration Ecosystem

### 14.1 Integration Categories

#### 14.1.1 Wearable & Performance Devices

| Provider | Data Types | Sync Method |
|----------|------------|-------------|
| Catapult | GPS, accelerometer, heart rate | Real-time API |
| STATSports | Position, speed, workload | Batch sync |
| Polar | Heart rate, HRV, sleep | Daily sync |
| Garmin | Activity, sleep, stress | OAuth API |
| Whoop | Strain, recovery, sleep | Daily sync |
| Apple Watch | Activity, heart rate | HealthKit |

#### 14.1.2 Video Platforms

| Provider | Integration Type | Features |
|----------|-----------------|----------|
| Hudl | Import/export | Video sharing, analysis import |
| Veo | Camera integration | Automatic upload |
| Pixellot | AI camera | Stream ingestion |
| YouTube | Export | Highlight sharing |

#### 14.1.3 Communication Tools

| Provider | Integration Type |
|----------|-----------------|
| Slack | Notifications, alerts |
| Microsoft Teams | SSO, notifications |
| WhatsApp Business | Message delivery |
| Twilio | SMS notifications |

#### 14.1.4 Financial Systems

| Provider | Integration Type |
|----------|-----------------|
| Stripe | Payment processing |
| PayPal | Alternative payments |
| QuickBooks | Accounting sync |
| Xero | Accounting sync |

#### 14.1.5 School Systems

| Provider | Integration Type |
|----------|-----------------|
| PowerSchool | Student roster sync |
| Canvas | LMS integration |
| Google Classroom | Schedule sync |
| ClassDojo | Parent communication |

---

### 14.2 API Platform

#### 14.2.1 REST API

**Specification:**
- OpenAPI 3.1 documented
- JSON request/response
- OAuth 2.0 authentication
- Rate limiting per tier
- Versioned endpoints

**Endpoint Categories:**
```
/api/v1/
    ├── organizations/
    ├── teams/
    ├── players/
    ├── events/
    ├── competitions/
    ├── performance/
    ├── media/
    └── reports/
```

#### 14.2.2 GraphQL API

**Features:**
- Flexible queries
- Real-time subscriptions
- Introspection
- Batched requests

#### 14.2.3 Webhooks

**Available Events:**
- Player created/updated
- Event scheduled/changed
- Match result recorded
- Consent status changed
- Performance threshold triggered

**Webhook Configuration:**
- Custom endpoint URLs
- Event filtering
- Retry logic
- Signature verification

---

### 14.3 Data Import/Export

#### 14.3.1 Import Capabilities

**Supported Formats:**
| Format | Use Case |
|--------|----------|
| CSV | Bulk player import |
| Excel | Roster management |
| JSON | API data transfer |
| XML | Legacy system migration |
| vCard | Contact import |
| iCal | Calendar import |

**Import Wizard:**
1. Upload file
2. Map columns to fields
3. Preview and validate
4. Handle duplicates
5. Execute import
6. Review results

#### 14.3.2 Export Capabilities

**Export Options:**
- Full data export (GDPR compliance)
- Selective report export
- Scheduled exports
- API-based extraction

---

## 15. Technical Architecture

### 15.1 System Overview

**Portable VM Architecture (Docker Compose)**

```
┌────────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                   │
│   Next.js Web │ React Native Mobile │ PWA │ Wearable Integrations     │
└─────────────────────────────┬──────────────────────────────────────────┘
                              │ HTTPS
                              │
┌─────────────────────────────▼──────────────────────────────────────────┐
│              VM: Azure / Linode / DigitalOcean / Hetzner              │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                    TRAEFIK (Reverse Proxy + SSL)                 │ │
│  │                   Auto Let's Encrypt certificates                │ │
│  └──────────────────────────────┬───────────────────────────────────┘ │
│                                 │                                     │
│  ┌──────────────────────────────▼───────────────────────────────────┐ │
│  │                    NEXT.JS 15 APPLICATION                        │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │ │
│  │  │   Auth   │ │  Teams   │ │  Events  │ │ Analytics│            │ │
│  │  │(NextAuth)│ │  Routes  │ │  Routes  │ │  Routes  │            │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘            │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │ │
│  │  │  Media   │ │  Comms   │ │ Payment  │ │ Reports  │            │ │
│  │  │ Upload   │ │WebSocket │ │ (Stripe) │ │   API    │            │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘            │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                 │                                     │
│         ┌───────────────────────┼───────────────────────┐             │
│         │                       │                       │             │
│  ┌──────▼──────┐  ┌────────────▼────────────┐  ┌──────▼──────┐       │
│  │   PYTHON    │  │       WORKER            │  │   OLLAMA    │       │
│  │ AI SERVICE  │  │   (Background Jobs)     │  │  (Qwen3-VL) │       │
│  │  (FastAPI)  │  │   Video processing      │  │    [GPU]    │       │
│  └──────┬──────┘  └────────────┬────────────┘  └──────┬──────┘       │
│         │                      │                      │               │
│  ┌──────▼──────────────────────▼──────────────────────▼──────┐       │
│  │                     DATA LAYER (Containers)               │       │
│  │  ┌─────────────┐  ┌─────────┐  ┌──────────────┐          │       │
│  │  │ PostgreSQL  │  │  Redis  │  │    MinIO     │          │       │
│  │  │   16 +      │  │ 7       │  │(S3-compatible)│          │       │
│  │  │ TimescaleDB │  │ Cache + │  │   Object     │          │       │
│  │  │ + pgvector  │  │ BullMQ  │  │   Storage    │          │       │
│  │  └─────────────┘  └─────────┘  └──────────────┘          │       │
│  └───────────────────────────────────────────────────────────┘       │
└──────────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┴────────────────────┐
         │ External APIs (Provider-Agnostic)       │
         ▼                                         ▼
┌─────────────────┐                    ┌─────────────────┐
│  AZURE OPENAI   │                    │ AZURE SPEECH    │
│  (LLM API)      │                    │ (Audio API)     │
│  • GPT-4o       │                    │ • Transcription │
│  • GPT-4o-mini  │                    │ • Speaker ID    │
│  • Embeddings   │                    │                 │
└─────────────────┘                    └─────────────────┘
```

**Key Portability Features:**
- All core services run in Docker containers
- MinIO provides S3-compatible storage (works like AWS S3 or Linode Object Storage)
- PostgreSQL with extensions runs in container (no managed service lock-in)
- External APIs (Azure OpenAI) accessible from any network
- Single `docker-compose.yml` deploys entire stack
- Migration = copy data + update DNS

### 15.2 Technology Stack

#### 15.2.1 Frontend Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | **Next.js 15** | Full-stack React framework |
| Runtime | Node.js 22 LTS | JavaScript execution |
| Styling | Tailwind CSS 4 | Utility-first styling |
| State | Zustand + TanStack Query | Client state + server state |
| Forms | React Hook Form + Zod | Form handling + validation |
| UI Components | Radix UI + custom | Accessible primitives |
| Charts | Recharts | Data visualization |
| Maps | Mapbox GL | Venue and location mapping |

#### 15.2.2 Backend Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | **Next.js API Routes** + **Python/FastAPI** (AI services) | API layer |
| Database | **PostgreSQL 16** | Primary data store |
| ORM | Drizzle ORM | Type-safe database access |
| Time-Series | TimescaleDB (PostgreSQL extension) | Performance metrics |
| Cache | Redis 7 | Session, real-time, queues |
| Search | PostgreSQL full-text + pg_trgm | Search functionality |
| File Storage | Azure Blob Storage | Media and documents |
| Queue | BullMQ (Redis) | Background job processing |

#### 15.2.3 AI/ML Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| LLM Inference | **Azure OpenAI** (GPT-4o, GPT-4o-mini) | Text generation, analysis |
| Vision/Video Analysis | **Ollama + Qwen3-VL** (self-hosted) | Player detection, action recognition |
| Speech-to-Text | Azure Speech Services | Audio transcription |
| Embeddings | Azure OpenAI (text-embedding-3-large) | Semantic search |
| Vector Store | pgvector (PostgreSQL extension) | Embedding storage |

#### 15.2.4 Core Services

| Service | Purpose | Technology | Database |
|---------|---------|------------|----------|
| Identity | Auth, users, orgs | Next.js + NextAuth.js | PostgreSQL |
| Teams | Teams, players, rosters | Next.js API Routes | PostgreSQL |
| Events | Schedules, competitions | Next.js API Routes | PostgreSQL |
| Analytics | Metrics, reports | Next.js + Python | TimescaleDB |
| Media | Video, images, files | Next.js + Python | Azure Blob + PostgreSQL |
| Communications | Messaging, notifications | Next.js API Routes | PostgreSQL + Redis |
| Payment | Billing, subscriptions | Next.js + Stripe SDK | PostgreSQL |
| AI | ML models, inference | Python/FastAPI | pgvector |

#### 15.2.2 Supporting Services

| Service | Purpose |
|---------|---------|
| Video Processor | Async video analysis pipeline |
| Notification Sender | Push/email/SMS delivery |
| Report Generator | PDF/Excel generation |
| Scheduler | Cron and event-triggered jobs |
| Search | Full-text and semantic search |

---

### 15.3 Data Architecture

#### 15.3.1 Primary Database (PostgreSQL)

**Schema Organization:**
```
├── identity_schema/
│   ├── users
│   ├── organizations
│   ├── memberships
│   └── permissions
├── teams_schema/
│   ├── teams
│   ├── players
│   ├── rosters
│   └── staff
├── events_schema/
│   ├── events
│   ├── competitions
│   ├── fixtures
│   └── results
├── performance_schema/
│   ├── metrics
│   ├── assessments
│   └── goals
└── communications_schema/
    ├── messages
    ├── notifications
    └── consents
```

#### 15.3.2 Time-Series Database (TimescaleDB)

**Purpose:** High-volume performance metrics

**Data Types:**
- GPS coordinates (30fps)
- Heart rate readings
- Accelerometer data
- Speed/distance metrics

**Retention:**
- Raw data: 90 days
- Aggregated (minute): 1 year
- Aggregated (hour): 5 years
- Aggregated (day): Forever

#### 15.3.3 Object Storage (S3/Blob)

**Content Types:**
| Type | Retention | Access Pattern |
|------|-----------|----------------|
| Videos (raw) | 90 days | Write once, read rarely |
| Videos (processed) | 2 years | Read frequently |
| Images | Forever | Read frequently |
| Documents | Forever | Read rarely |
| Exports | 7 days | Download once |

#### 15.3.4 Cache Layer (Redis)

**Use Cases:**
- Session storage
- Real-time metrics
- Rate limiting counters
- Pub/sub for live updates
- Job queues

---

### 15.4 AI/ML Infrastructure

#### 15.4.1 Model Inventory

| Model | Purpose | Provider/Framework | Deployment |
|-------|---------|-------------------|------------|
| **Qwen3-VL** | Player detection, tracking, action recognition | Ollama (self-hosted) | On-premise GPU server |
| Pose Estimation | Body joint positions | Qwen3-VL / MediaPipe | Ollama + fallback |
| Video Analysis | Match/training analysis | Qwen3-VL multimodal | Ollama cluster |
| **GPT-4o** | NLP extraction, report generation, coaching insights | Azure OpenAI | API |
| **GPT-4o-mini** | High-volume text processing, classification | Azure OpenAI | API |
| Speech-to-Text | Transcribe audio narration | Azure Speech Services | API |
| Text Embeddings | Semantic search, similarity | Azure OpenAI (text-embedding-3-large) | API |
| Injury Prediction | Risk assessment | XGBoost/scikit-learn | Python service |

#### 15.4.2 AI Provider Configuration

**Azure OpenAI Setup:**
```yaml
azure_openai:
  endpoint: https://<resource>.openai.azure.com/
  api_version: "2024-08-01-preview"
  deployments:
    gpt4o:
      model: gpt-4o
      use_cases: [coaching_insights, report_generation, complex_analysis]
      max_tokens: 16384
    gpt4o_mini:
      model: gpt-4o-mini
      use_cases: [text_classification, entity_extraction, high_volume]
      max_tokens: 4096
    embeddings:
      model: text-embedding-3-large
      dimensions: 3072
      use_cases: [semantic_search, player_similarity]
  rate_limits:
    gpt4o: 60_000 TPM
    gpt4o_mini: 200_000 TPM
```

**Ollama + Qwen3-VL Setup:**
```yaml
ollama:
  host: http://gpu-server:11434
  models:
    qwen3_vl:
      name: qwen3-vl:72b
      context_length: 32768
      use_cases: [video_frame_analysis, player_detection, action_recognition]
      gpu_layers: all
  scaling:
    replicas: 3
    load_balancing: round_robin
    health_check: /api/health
```

#### 15.4.3 Processing Pipeline

```
Video Upload (Next.js → MinIO S3)
              │
              ▼
    Job Queue (BullMQ/Redis)
              │
              ▼
    Frame Extraction Worker
              │
              ▼
    Ollama Qwen3-VL (GPU)
              │
     ┌────────┼────────┐
     │        │        │
     ▼        ▼        ▼
  Frame 1  Frame 2  Frame N  (parallel processing)
     │        │        │
     └────────┼────────┘
              │
              ▼
    Results Aggregation
              │
     ┌────────┴────────┐
     │                 │
     ▼                 ▼
 Metrics DB      Azure OpenAI
 (PostgreSQL)    (Insights Gen)
     │                 │
     └────────┬────────┘
              │
              ▼
    Notification Service
              │
              ▼
    User Dashboard Update
```

**Processing Flow Details:**
1. Video uploaded to MinIO (S3-compatible object storage)
2. Upload triggers BullMQ job
3. Worker extracts keyframes (2-5 fps based on action density)
4. Frames sent to Ollama cluster in batches
5. Qwen3-VL analyzes each frame for players, ball, actions
6. Results aggregated and cross-referenced across frames
7. Metrics stored in PostgreSQL/TimescaleDB
8. Azure OpenAI generates natural language insights
9. User notified when processing complete

---

### 15.5 Infrastructure

#### 15.5.1 Deployment Philosophy

**Portable VM-Based Architecture:**

AfroLete runs on a single VM (or small cluster) using Docker Compose, ensuring full portability across cloud providers:

| Principle | Implementation |
|-----------|----------------|
| **Cloud Agnostic** | No vendor-specific managed services for core functionality |
| **Self-Contained** | All services run in Docker containers |
| **Single VM Capable** | Can run entire stack on one powerful VM |
| **Horizontally Scalable** | Can split to multiple VMs when needed |
| **Easy Migration** | Move to Linode, DigitalOcean, Hetzner, or on-premise with minimal changes |

**External Dependencies (API-based, provider-agnostic):**
- Azure OpenAI (LLM inference) - accessible from any network
- Azure Speech Services (audio transcription) - accessible from any network

#### 15.5.2 VM Specifications

**Primary Application Server:**
| Component | Minimum | Recommended | Production |
|-----------|---------|-------------|------------|
| vCPUs | 4 | 8 | 16 |
| RAM | 16 GB | 32 GB | 64 GB |
| Storage | 100 GB SSD | 250 GB SSD | 500 GB NVMe |
| Network | 1 Gbps | 2 Gbps | 5 Gbps |

**GPU Server (for Ollama/Qwen3-VL) - Optional Separate VM:**
| Component | Specification |
|-----------|---------------|
| GPU | NVIDIA RTX 4090 (24GB) or A100 (40GB+) |
| vCPUs | 8+ |
| RAM | 32 GB+ |
| Storage | 200 GB SSD |

**Azure VM Recommendations:**
- App Server: Standard_D8s_v5 (8 vCPU, 32GB RAM) - ~$280/month
- GPU Server: Standard_NC24ads_A100_v4 - varies by availability

**Linode Equivalent:**
- App Server: Dedicated 32GB (8 vCPU, 32GB RAM) - ~$192/month
- GPU Server: Use external GPU provider (Lambda Labs, RunPod) or on-premise

#### 15.5.3 Docker Compose Architecture

**Production Stack (`docker-compose.prod.yml`):**
```yaml
version: "3.9"

services:
  # ===================
  # REVERSE PROXY & SSL
  # ===================
  traefik:
    image: traefik:v3.0
    container_name: afrolete-proxy
    command:
      - "--api.dashboard=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
      - "--certificatesresolvers.letsencrypt.acme.email=${ACME_EMAIL}"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - traefik-certs:/letsencrypt
    networks:
      - afrolete-network
    restart: unless-stopped

  # ===================
  # NEXT.JS APPLICATION
  # ===================
  web:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    container_name: afrolete-web
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://afrolete:${DB_PASSWORD}@postgres:5432/afrolete
      - REDIS_URL=redis://redis:6379
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
      - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
      - OLLAMA_BASE_URL=http://ollama:11434
      - S3_ENDPOINT=http://minio:9000
      - S3_ACCESS_KEY=${S3_ACCESS_KEY}
      - S3_SECRET_KEY=${S3_SECRET_KEY}
      - S3_BUCKET=afrolete-media
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.web.rule=Host(`${DOMAIN}`)"
      - "traefik.http.routers.web.entrypoints=websecure"
      - "traefik.http.routers.web.tls.certresolver=letsencrypt"
      - "traefik.http.services.web.loadbalancer.server.port=3000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - afrolete-network
    restart: unless-stopped

  # ===================
  # PYTHON AI SERVICE
  # ===================
  ai-service:
    build:
      context: ./services/ai
      dockerfile: Dockerfile
    container_name: afrolete-ai
    environment:
      - DATABASE_URL=postgresql://afrolete:${DB_PASSWORD}@postgres:5432/afrolete
      - REDIS_URL=redis://redis:6379
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
      - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - postgres
      - redis
    networks:
      - afrolete-network
    restart: unless-stopped

  # ===================
  # DATABASE (PostgreSQL + TimescaleDB + pgvector)
  # ===================
  postgres:
    image: timescale/timescaledb-ha:pg16
    container_name: afrolete-db
    environment:
      - POSTGRES_USER=afrolete
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=afrolete
    volumes:
      - postgres-data:/home/postgres/pgdata
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "127.0.0.1:5432:5432"
    networks:
      - afrolete-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U afrolete"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ===================
  # CACHE & JOB QUEUE
  # ===================
  redis:
    image: redis:7-alpine
    container_name: afrolete-redis
    command: redis-server --appendonly yes --maxmemory 1gb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
    networks:
      - afrolete-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ===================
  # BACKGROUND WORKER
  # ===================
  worker:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    container_name: afrolete-worker
    command: node dist/worker.js
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://afrolete:${DB_PASSWORD}@postgres:5432/afrolete
      - REDIS_URL=redis://redis:6379
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
      - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
      - OLLAMA_BASE_URL=http://ollama:11434
      - S3_ENDPOINT=http://minio:9000
      - S3_ACCESS_KEY=${S3_ACCESS_KEY}
      - S3_SECRET_KEY=${S3_SECRET_KEY}
    depends_on:
      - postgres
      - redis
    networks:
      - afrolete-network
    restart: unless-stopped

  # ===================
  # OBJECT STORAGE (S3-Compatible)
  # ===================
  minio:
    image: minio/minio:latest
    container_name: afrolete-minio
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=${S3_ACCESS_KEY}
      - MINIO_ROOT_PASSWORD=${S3_SECRET_KEY}
    volumes:
      - minio-data:/data
    ports:
      - "127.0.0.1:9000:9000"
      - "127.0.0.1:9001:9001"
    networks:
      - afrolete-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  # ===================
  # OLLAMA (Vision AI) - GPU Required
  # ===================
  ollama:
    image: ollama/ollama:latest
    container_name: afrolete-ollama
    volumes:
      - ollama-data:/root/.ollama
    ports:
      - "127.0.0.1:11434:11434"
    networks:
      - afrolete-network
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

networks:
  afrolete-network:
    driver: bridge

volumes:
  postgres-data:
  redis-data:
  minio-data:
  ollama-data:
  traefik-certs:
```

#### 15.5.4 Database Initialization

**`scripts/init-db.sql`:**
```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";
-- TimescaleDB pre-installed in timescale/timescaledb-ha image

-- Performance tuning for 32GB RAM VM
ALTER SYSTEM SET shared_buffers = '8GB';
ALTER SYSTEM SET effective_cache_size = '24GB';
ALTER SYSTEM SET maintenance_work_mem = '2GB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '64MB';
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET work_mem = '128MB';
ALTER SYSTEM SET max_worker_processes = 8;
ALTER SYSTEM SET max_parallel_workers_per_gather = 4;
ALTER SYSTEM SET max_parallel_workers = 8;
```

#### 15.5.5 Environment Configuration

**`.env.production` template:**
```bash
# Domain & SSL
DOMAIN=app.afrolete.com
ACME_EMAIL=admin@afrolete.com

# Database
DB_PASSWORD=<generate-strong-password>

# Object Storage (MinIO - works identically to AWS S3 or Linode Object Storage)
S3_ACCESS_KEY=<generate-access-key>
S3_SECRET_KEY=<generate-secret-key>
S3_BUCKET=afrolete-media

# Azure OpenAI (external API - works from any provider)
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<api-key>
AZURE_SPEECH_KEY=<speech-key>
AZURE_SPEECH_REGION=westeurope

# Application Secrets
NEXTAUTH_SECRET=<generate-random-secret>
NEXTAUTH_URL=https://app.afrolete.com
```

#### 15.5.6 Deployment Commands

**Initial Setup:**
```bash
# 1. Clone repository
git clone https://github.com/afrolete/platform.git
cd platform

# 2. Create environment file
cp .env.example .env.production
# Edit .env.production with your values

# 3. Start services
docker compose -f docker-compose.prod.yml up -d

# 4. Run database migrations
docker compose -f docker-compose.prod.yml exec web npm run db:migrate

# 5. Pull Ollama model (requires GPU)
docker compose -f docker-compose.prod.yml exec ollama ollama pull qwen2.5-vl:7b

# 6. Create initial MinIO bucket
docker compose -f docker-compose.prod.yml exec minio mc mb /data/afrolete-media
```

**Daily Operations:**
```bash
# View logs
docker compose -f docker-compose.prod.yml logs -f web

# Restart service
docker compose -f docker-compose.prod.yml restart web

# Update deployment
git pull
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

#### 15.5.7 Migration: Azure to Linode

**Step-by-Step Migration:**

```bash
# === ON AZURE VM ===
# 1. Create database backup
docker compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U afrolete afrolete | gzip > backup.sql.gz

# 2. Create MinIO backup
docker compose -f docker-compose.prod.yml exec minio \
  mc mirror /data/afrolete-media /backup/

# === ON LINODE VM ===
# 3. Set up new VM (same Docker Compose setup)
# 4. Copy backup files
scp azure-vm:backup.sql.gz .
scp -r azure-vm:/backup/afrolete-media ./media-backup/

# 5. Start services (without web yet)
docker compose -f docker-compose.prod.yml up -d postgres redis minio

# 6. Restore database
gunzip -c backup.sql.gz | docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U afrolete afrolete

# 7. Restore media files
docker compose -f docker-compose.prod.yml exec minio \
  mc mirror /backup/afrolete-media /data/afrolete-media

# 8. Start remaining services
docker compose -f docker-compose.prod.yml up -d

# 9. Update DNS to point to Linode IP

# 10. Verify and decommission Azure VM after 7 days
```

**What Changes Between Providers:**
| Component | Azure | Linode | Change Required |
|-----------|-------|--------|-----------------|
| VM | Azure VM | Linode Dedicated | IP address only |
| Docker | Same | Same | None |
| PostgreSQL | Container | Container | None |
| Redis | Container | Container | None |
| MinIO | Container | Container | None |
| Ollama | Container | Container | None |
| Azure OpenAI | API | API | None (external) |
| DNS | Update A record | Update A record | IP address |

#### 15.5.8 Backup Strategy

**Automated Backups (`/etc/cron.d/afrolete-backup`):**
```bash
# Daily database backup at 2 AM
0 2 * * * root /opt/afrolete/scripts/backup-db.sh

# Weekly full backup at 3 AM Sunday
0 3 * * 0 root /opt/afrolete/scripts/backup-full.sh
```

**`scripts/backup-db.sh`:**
```bash
#!/bin/bash
set -e
BACKUP_DIR="/backups/db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
docker compose -f /opt/afrolete/docker-compose.prod.yml exec -T postgres \
  pg_dump -U afrolete afrolete | gzip > "$BACKUP_DIR/afrolete_${TIMESTAMP}.sql.gz"

# Keep last 14 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +14 -delete
```

#### 15.5.9 GPU Options for Ollama

**Option A: Same VM with GPU (Azure NC-series)**
```yaml
# Add to docker-compose.prod.yml ollama service
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

**Option B: Separate GPU Server**
```bash
# On GPU server
OLLAMA_HOST=0.0.0.0 ollama serve

# In .env.production on app server
OLLAMA_BASE_URL=http://<gpu-server-ip>:11434
```

**Option C: External GPU Provider (Lambda Labs, RunPod)**
```bash
# Run Ollama on rented GPU instance
# Expose via private network or Tailscale
OLLAMA_BASE_URL=https://your-runpod-instance.runpod.io
```

**Option D: CPU-Only Mode (Development/Testing)**
```bash
# Remove GPU reservation, use smaller model
ollama pull qwen2.5-vl:7b  # Runs on CPU, slower but works
```

---

## 16. Data Model

### 16.1 Core Entities

#### 16.1.1 Organization

```
Organization {
    id: UUID (PK)
    name: String
    type: Enum [CLUB, SCHOOL, ASSOCIATION, TEAM]
    parent_org_id: UUID (FK, nullable)
    settings: JSONB
    branding: JSONB
    subscription_tier: Enum
    created_at: Timestamp
    updated_at: Timestamp
    status: Enum [ACTIVE, SUSPENDED, ARCHIVED]
}
```

#### 16.1.2 User

```
User {
    id: UUID (PK)
    email: String (unique)
    phone: String (unique, nullable)
    password_hash: String
    first_name: String
    last_name: String
    date_of_birth: Date (nullable)
    avatar_url: String (nullable)
    settings: JSONB
    created_at: Timestamp
    last_login: Timestamp
    status: Enum [ACTIVE, SUSPENDED, PENDING]
}
```

#### 16.1.3 Player

```
Player {
    id: UUID (PK)
    user_id: UUID (FK)
    organization_id: UUID (FK)
    player_number: String (nullable)
    position: String (nullable)
    dominant_foot: Enum [LEFT, RIGHT, BOTH]
    dominant_hand: Enum [LEFT, RIGHT, BOTH]
    height_cm: Float (nullable)
    weight_kg: Float (nullable)
    medical_info: JSONB (encrypted)
    emergency_contacts: JSONB
    registration_date: Date
    status: Enum [ACTIVE, INJURED, INACTIVE]
}
```

#### 16.1.4 Team

```
Team {
    id: UUID (PK)
    organization_id: UUID (FK)
    name: String
    sport: String
    age_group: String (nullable)
    gender: Enum [MALE, FEMALE, MIXED]
    division: String (nullable)
    home_venue_id: UUID (FK, nullable)
    settings: JSONB
    created_at: Timestamp
    status: Enum [ACTIVE, ARCHIVED]
}
```

#### 16.1.5 Event

```
Event {
    id: UUID (PK)
    organization_id: UUID (FK)
    type: Enum [TRAINING, MATCH, MEETING, OTHER]
    title: String
    description: Text (nullable)
    start_time: Timestamp
    end_time: Timestamp
    venue_id: UUID (FK, nullable)
    recurring_rule: String (RRULE, nullable)
    metadata: JSONB
    created_by: UUID (FK)
    status: Enum [SCHEDULED, CANCELLED, COMPLETED]
}
```

#### 16.1.6 Performance Metric

```
PerformanceMetric {
    id: UUID (PK)
    player_id: UUID (FK)
    event_id: UUID (FK, nullable)
    metric_type: String
    value: Float
    unit: String
    source: Enum [VIDEO, WEARABLE, MANUAL, AUDIO]
    confidence: Float (nullable)
    recorded_at: Timestamp
    metadata: JSONB
}
```

#### 16.1.7 Consent

```
Consent {
    id: UUID (PK)
    player_id: UUID (FK)
    guardian_id: UUID (FK)
    consent_type: String
    status: Enum [PENDING, APPROVED, DECLINED, EXPIRED]
    requested_at: Timestamp
    responded_at: Timestamp (nullable)
    expires_at: Timestamp (nullable)
    signature: Text (nullable)
    metadata: JSONB
}
```

---

### 16.2 Relationship Diagram

```
                    ┌─────────────────┐
                    │  Organization   │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
    ┌─────▼─────┐     ┌─────▼─────┐     ┌─────▼─────┐
    │   Team    │     │   User    │     │   Event   │
    └─────┬─────┘     └─────┬─────┘     └─────┬─────┘
          │                 │                 │
          │           ┌─────▼─────┐           │
          └──────────▶│  Player   │◀──────────┘
                      └─────┬─────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
    ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐
    │  Metric   │    │  Consent  │    │   Media   │
    └───────────┘    └───────────┘    └───────────┘
```

---

## 17. Non-Functional Requirements

### 17.1 Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Page Load Time | <2 seconds | 95th percentile |
| API Response Time | <200ms | 95th percentile |
| Video Upload | <30s for 100MB | Median |
| Video Processing | <5 min per hour of video | Batch average |
| Real-time Updates | <500ms latency | WebSocket ping |
| Search Results | <1 second | 95th percentile |

### 17.2 Scalability

| Dimension | Target |
|-----------|--------|
| Concurrent Users | 100,000 |
| Total Users | 10 million |
| Organizations | 50,000 |
| Events per Day | 500,000 |
| Video Hours per Day | 10,000 |
| API Requests per Second | 10,000 |

### 17.3 Availability

| Metric | Target |
|--------|--------|
| Uptime SLA | 99.9% |
| Planned Maintenance Window | <4 hours/month |
| Recovery Time Objective (RTO) | <1 hour |
| Recovery Point Objective (RPO) | <15 minutes |

### 17.4 Reliability

| Requirement | Implementation |
|-------------|----------------|
| Data Durability | 99.999999999% (11 9s) |
| Backup Frequency | Hourly incremental, daily full |
| Backup Retention | 90 days |
| Geographic Redundancy | Multi-region active-passive |
| Disaster Recovery | Automated failover |

### 17.5 Localization

**Supported Languages (Initial):**
- English (default)
- French
- Spanish
- Portuguese
- Swahili
- Arabic

**Localization Scope:**
- UI text
- Error messages
- Email templates
- Documentation
- Date/time formats
- Number formats
- Currency handling

---

## 18. Development Phases & Roadmap

### 18.1 Phase 1: Foundation (Months 1-4)

**Objective:** Launch MVP with core multi-tenant capabilities

**Deliverables:**
- [ ] Organization and user management
- [ ] Basic player profiles
- [ ] Team creation and roster management
- [ ] Simple event scheduling
- [ ] Manual metric entry
- [ ] Basic reporting
- [ ] Mobile app (iOS, Android)
- [ ] Web admin dashboard

**Success Criteria:**
- 10 pilot organizations onboarded
- 500 active users
- System stability >99%

### 18.2 Phase 2: Performance Analytics (Months 5-8)

**Objective:** Deploy AI-powered performance analysis

**Deliverables:**
- [ ] Video upload and processing pipeline
- [ ] Player detection and tracking
- [ ] Basic action recognition
- [ ] Performance dashboards
- [ ] Trend analysis and visualization
- [ ] AfroLete Score calculation
- [ ] Wearable integrations (Garmin, Polar)

**Success Criteria:**
- 1,000 hours of video processed
- 85% accuracy on player detection
- 70% accuracy on action recognition

### 18.3 Phase 3: Intelligent Coaching (Months 9-12)

**Objective:** Enable AI-driven training recommendations

**Deliverables:**
- [ ] Audio narration processing
- [ ] Text evaluation parsing
- [ ] Training plan generation engine
- [ ] Drill library with 200+ drills
- [ ] Session planning tools
- [ ] Load management system
- [ ] Biomechanical analysis (pose estimation)

**Success Criteria:**
- 75% coach satisfaction with recommendations
- 20% improvement in training efficiency

### 18.4 Phase 4: Competition Excellence (Months 13-16)

**Objective:** Comprehensive competition management

**Deliverables:**
- [ ] League management
- [ ] Tournament brackets
- [ ] AI-optimized scheduling
- [ ] Live match scoring
- [ ] Real-time statistics
- [ ] Official/referee portal
- [ ] Broadcasting integrations

**Success Criteria:**
- 100 leagues/tournaments managed
- <5 minute schedule generation for 500 events

### 18.5 Phase 5: Ecosystem Expansion (Months 17-24)

**Objective:** Platform maturity and market expansion

**Deliverables:**
- [ ] API marketplace
- [ ] Third-party app ecosystem
- [ ] Advanced predictive analytics
- [ ] Multi-language support
- [ ] Enterprise SSO
- [ ] Advanced compliance tools
- [ ] White-label capabilities

**Success Criteria:**
- 10,000 organizations
- 500,000 active users
- 20 third-party integrations

---

## 19. Success Metrics

### 19.1 Business Metrics

| Metric | Year 1 Target | Year 2 Target |
|--------|---------------|---------------|
| Monthly Active Users | 50,000 | 500,000 |
| Paying Organizations | 500 | 5,000 |
| Monthly Recurring Revenue | $50,000 | $500,000 |
| Net Revenue Retention | >100% | >110% |
| Customer Acquisition Cost | <$500 | <$300 |
| Lifetime Value | >$3,000 | >$5,000 |

### 19.2 Product Metrics

| Metric | Target |
|--------|--------|
| Daily Active Users / Monthly Active Users | >40% |
| Feature Adoption Rate | >60% of core features |
| Time to First Value | <10 minutes |
| User Onboarding Completion | >80% |
| Net Promoter Score | >50 |

### 19.3 Technical Metrics

| Metric | Target |
|--------|--------|
| System Uptime | 99.9% |
| Mean Time to Recovery | <30 minutes |
| Deployment Frequency | Daily |
| Change Failure Rate | <5% |
| API Error Rate | <0.1% |

### 19.4 AI Performance Metrics

| Metric | Target |
|--------|--------|
| Player Detection Accuracy | >95% |
| Ball Tracking Accuracy | >90% |
| Action Classification Accuracy | >85% |
| Speech Transcription WER | <10% |
| Training Plan Satisfaction | >75% |

---

## 20. Appendices

### 20.1 Glossary

| Term | Definition |
|------|------------|
| **ALS** | AfroLete Score - composite performance rating |
| **Acute:Chronic** | Training load ratio for injury prevention |
| **xG** | Expected Goals - shot quality metric |
| **Homography** | Geometric transformation for field mapping |
| **RPE** | Rate of Perceived Exertion - subjective effort scale |
| **VO2 Max** | Maximum oxygen uptake - aerobic capacity |
| **HRV** | Heart Rate Variability - recovery indicator |
| **NIL** | Name, Image, Likeness - athlete monetization |

### 20.2 Sport-Specific Metric Configurations

#### Football (Soccer)
```yaml
metrics:
  technical:
    - pass_completion_rate
    - shot_accuracy
    - dribble_success_rate
    - aerial_duel_win_rate
    - tackle_success_rate
  physical:
    - total_distance
    - sprint_distance
    - top_speed
    - sprint_count
    - high_intensity_runs
  tactical:
    - position_heat_map
    - pressing_actions
    - recoveries
    - interceptions
```

#### Basketball
```yaml
metrics:
  offensive:
    - points_per_game
    - field_goal_percentage
    - three_point_percentage
    - free_throw_percentage
    - assists
    - turnovers
  defensive:
    - rebounds
    - steals
    - blocks
    - defensive_rating
  physical:
    - vertical_leap
    - court_coverage
    - sprint_speed
```

#### Athletics (Track & Field)
```yaml
metrics:
  sprints:
    - reaction_time
    - split_times
    - top_speed
    - deceleration_rate
  distance:
    - pace_per_kilometer
    - split_consistency
    - finishing_kick
  field_events:
    - technique_score
    - approach_speed
    - release_angle
    - release_velocity
```

### 20.3 Consent Form Templates

#### General Registration Consent
```markdown
# Player Registration Consent Form

I, [Guardian Name], parent/guardian of [Player Name], hereby:

1. **Authorize participation** in athletic activities organized by [Organization Name]
2. **Acknowledge risks** inherent in sports participation
3. **Grant permission** for emergency medical treatment if required
4. **Confirm accuracy** of provided information

Signature: ________________________
Date: ________________________
```

#### Photo/Video Release
```markdown
# Media Release Consent

I authorize [Organization Name] to:

- Capture photographs and video of [Player Name]
- Use such media for:
  [ ] Internal training purposes
  [ ] Organization website and social media
  [ ] Promotional materials
  [ ] Media and press releases

This consent is valid until: [Date] or until withdrawn in writing.

Signature: ________________________
Date: ________________________
```

### 20.4 Integration API Examples

#### Player Retrieval
```json
GET /api/v1/players/abc-123-def

Response:
{
  "id": "abc-123-def",
  "user_id": "usr-456",
  "first_name": "Kwame",
  "last_name": "Mensah",
  "position": "Forward",
  "team": {
    "id": "team-789",
    "name": "U-14 Boys"
  },
  "metrics_summary": {
    "afrolete_score": 78,
    "trend": "improving",
    "last_updated": "2026-01-15T10:30:00Z"
  }
}
```

#### Performance Metric Submission
```json
POST /api/v1/metrics

Request:
{
  "player_id": "abc-123-def",
  "event_id": "evt-456",
  "metrics": [
    {
      "type": "sprint_speed",
      "value": 8.2,
      "unit": "m/s",
      "source": "wearable"
    },
    {
      "type": "distance_covered",
      "value": 5400,
      "unit": "m",
      "source": "wearable"
    }
  ]
}
```

### 20.5 References

1. Freeman, R.E. (1984). *Strategic Management: A Stakeholder Approach*
2. WCAG 2.1 Guidelines - https://www.w3.org/WAI/WCAG21/quickref/
3. GDPR Requirements - https://gdpr.eu/
4. COPPA Guidelines - https://www.ftc.gov/legal-library/browse/rules/childrens-online-privacy-protection-rule-coppa

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-17 | AfroLete Product Team | Initial comprehensive specification |

---

*This document serves as the authoritative specification for the AfroLete platform. All development efforts should align with the requirements outlined herein. Updates to this document require approval from the Product Lead and notification to all stakeholders.*
