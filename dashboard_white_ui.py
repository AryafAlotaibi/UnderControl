import streamlit as st


def render_dashboard_ui() -> None:
    """White visual dashboard shell based on the retained TAWOS fields only."""
    st.markdown(
        """
<style>
    .stApp { background: #F8FAFE; }
    header { visibility: hidden; }
    .block-container { max-width: 1480px; padding: 24px 36px 72px; }
    .uc-nav { display:flex; align-items:center; justify-content:space-between; padding:16px 2px 25px; }
    .uc-identity { display:flex; align-items:center; gap:10px; color:#16223B; font-size:14px; font-weight:800; letter-spacing:-.02em; }
    .uc-mark { display:grid; place-items:center; width:30px; height:30px; border-radius:10px; background:linear-gradient(140deg,#377DF5,#7157DF); color:#FFF; font-size:15px; box-shadow:0 7px 14px rgba(55,125,245,.22); }
    .uc-breadcrumb { color:#9AA9BD; font-size:12px; font-weight:650; }
    .eyebrow { color:#5C78AC; font-size:11px; font-weight:800; letter-spacing:.13em; text-transform:uppercase; }
    .dashboard-title { margin:6px 0 5px; color:#14203A; font-size:32px; font-weight:780; letter-spacing:-.055em; }
    .dashboard-subtitle { color:#7B8BA2; font-size:13px; margin-bottom:22px; }
    .preview-label { display:inline-flex; align-items:center; gap:6px; padding:6px 9px; background:#EFF5FF; color:#5A77A5; border:1px solid #DBE8FB; border-radius:99px; font-size:10px; font-weight:750; }
    .preview-label::before { content:""; width:6px; height:6px; border-radius:50%; background:#4F8AF7; }
    .stat-card { min-height:128px; padding:18px; box-sizing:border-box; background:#FFF; border:1px solid #E5ECF7; border-radius:16px; box-shadow:0 10px 24px rgba(27,55,97,.045); overflow:hidden; position:relative; }
    .stat-card::after { content:""; position:absolute; width:80px; height:80px; right:-25px; bottom:-39px; border-radius:50%; background:radial-gradient(circle,rgba(89,137,248,.12),transparent 68%); }
    .stat-label { color:#74849C; font-size:11px; font-weight:700; }
    .stat-value { margin-top:10px; color:#16223B; font-size:28px; font-weight:790; letter-spacing:-.06em; }
    .stat-source { margin-top:7px; color:#A0AEC1; font-size:10px; }
    .section-name { margin:29px 0 12px; color:#182641; font-size:16px; font-weight:760; letter-spacing:-.025em; }
    .widget { height:100%; min-height:280px; box-sizing:border-box; padding:19px; background:#FFF; border:1px solid #E5ECF7; border-radius:16px; box-shadow:0 10px 24px rgba(27,55,97,.04); }
    .widget-head { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:16px; }
    .widget-title { color:#273751; font-size:13px; font-weight:760; }
    .widget-note { color:#9AA9BC; font-size:10px; margin-top:4px; }
    .field-chip { padding:5px 7px; background:#F3F7FC; border-radius:7px; color:#7F91AA; font-size:9px; font-weight:700; }
    .legend { display:flex; gap:13px; color:#8796AA; font-size:10px; margin-top:7px; }
    .legend i { display:inline-block; width:6px; height:6px; margin-right:4px; border-radius:50%; }
    .priority-row { display:grid; grid-template-columns:72px 1fr 24px; align-items:center; gap:10px; margin:14px 0; }
    .priority-name { color:#60718A; font-size:11px; font-weight:650; }
    .priority-track { height:8px; overflow:hidden; background:#F0F4FA; border-radius:99px; }
    .priority-fill { height:100%; border-radius:99px; }
    .priority-value { color:#A2AFBE; font-size:10px; text-align:right; }
    .type-list { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:18px; }
    .type-item { display:flex; align-items:center; gap:8px; padding:10px; border:1px solid #EDF1F7; border-radius:10px; color:#60718A; font-size:11px; font-weight:650; }
    .type-dot { width:8px; height:8px; border-radius:3px; flex:0 0 auto; }
    .issue-shell { overflow:hidden; background:#FFF; border:1px solid #E5ECF7; border-radius:16px; box-shadow:0 10px 24px rgba(27,55,97,.04); }
    .issue-head,.issue-row { display:grid; grid-template-columns:1.2fr .8fr .9fr .9fr .9fr 1fr; align-items:center; gap:12px; }
    .issue-head { padding:13px 18px; background:#FBFCFF; color:#8A99AC; font-size:9px; font-weight:800; letter-spacing:.05em; text-transform:uppercase; }
    .issue-row { padding:15px 18px; border-top:1px solid #EEF2F7; }
    .skeleton { display:block; height:8px; border-radius:99px; background:linear-gradient(90deg,#EDF2F7 0%,#F8FAFD 48%,#EDF2F7 100%); }
    .soft-tag { width:62%; height:17px; border-radius:6px; background:#F2F6FC; }
    div[data-testid="stSelectbox"] label { color:#6D7E96; font-size:11px; font-weight:700; }
    div[data-testid="stSelectbox"] > div > div { background:#FFF; border-color:#E1EAF5; border-radius:10px; }
    .command-deck { position:relative; display:grid; grid-template-columns:1.18fr .82fr; min-height:185px; margin:20px 0 24px; overflow:hidden; background:linear-gradient(125deg,#152342 0%,#253D78 58%,#4A3C91 100%); border-radius:20px; box-shadow:0 22px 38px rgba(29,49,96,.16); }
    .command-deck::before { content:""; position:absolute; inset:0; opacity:.38; background-image:linear-gradient(rgba(255,255,255,.12) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.12) 1px,transparent 1px); background-size:28px 28px; mask-image:linear-gradient(90deg,#000,transparent 82%); }
    .command-copy { position:relative; z-index:1; align-self:center; padding:29px 31px; }
    .command-eyebrow { color:#9EC1FF; font-size:10px; font-weight:800; letter-spacing:.14em; }
    .command-title { max-width:390px; margin:8px 0 8px; color:#FFF; font-size:23px; font-weight:760; letter-spacing:-.04em; line-height:1.15; }
    .command-text { max-width:400px; color:#C4D3F4; font-size:12px; line-height:1.6; }
    .command-tags { display:flex; flex-wrap:wrap; gap:7px; margin-top:15px; }
    .command-tags span { padding:5px 8px; border:1px solid rgba(210,226,255,.22); background:rgba(255,255,255,.08); border-radius:99px; color:#E7F0FF; font-size:10px; font-weight:650; }
    .signal-orbit { position:relative; align-self:center; justify-self:center; width:145px; height:145px; z-index:1; }
    .signal-orbit::before,.signal-orbit::after { content:""; position:absolute; inset:10px; border:1px solid rgba(192,211,255,.24); border-radius:50%; }
    .signal-orbit::after { inset:30px; border-color:rgba(79,235,215,.45); box-shadow:0 0 28px rgba(72,203,255,.22); }
    .orbit-core { position:absolute; inset:48px; display:grid; place-items:center; border-radius:50%; background:linear-gradient(145deg,#63A4FF,#7A5BEE); color:#FFF; font-size:22px; box-shadow:0 0 0 10px rgba(135,114,255,.12),0 12px 27px rgba(16,25,61,.35); }
    .orbit-dot { position:absolute; display:block; width:9px; height:9px; border-radius:50%; box-shadow:0 0 0 4px rgba(255,255,255,.08); }
    .orbit-dot.one { top:9px; left:66px; background:#67E8F9; } .orbit-dot.two { top:69px; right:1px; background:#FDBA74; } .orbit-dot.three { bottom:12px; left:22px; background:#C4B5FD; }
    .signal-path { display:flex; align-items:center; gap:10px; margin:0 0 24px; padding:16px 18px; overflow-x:auto; border:1px solid #E4EAF5; border-radius:16px; background:linear-gradient(90deg,#FFF,#F6F9FF); box-shadow:0 10px 24px rgba(27,55,97,.035); }
    .path-label { flex:0 0 auto; margin-right:5px; color:#8492AD; font-size:9px; font-weight:800; letter-spacing:.1em; text-transform:uppercase; }
    .path-node { flex:0 0 auto; min-width:89px; padding:8px 10px; border-radius:11px; font-size:11px; font-weight:800; text-align:center; }
    .path-node small { display:block; margin-top:3px; font-size:9px; font-weight:600; opacity:.68; }
    .path-node.one { background:#EAF1FF; color:#2854AD; } .path-node.two { background:#F1EBFF; color:#6A43BB; } .path-node.three { background:#E9FBF7; color:#168270; } .path-node.four { background:#FFF4DF; color:#A96211; }
    .path-link { flex:0 0 23px; height:2px; position:relative; background:linear-gradient(90deg,#9BB8EF,#C7B1F4); } .path-link:after { content:""; position:absolute; right:-1px; top:-3px; width:7px; height:7px; border-top:2px solid #A18AD9; border-right:2px solid #A18AD9; transform:rotate(45deg); }
    .stat-card::before { content:""; position:absolute; top:0; left:0; width:48px; height:4px; border-radius:0 0 8px 0; background:#6A78E8; }
    .mini-spark { display:flex; align-items:end; gap:3px; height:25px; margin-top:-31px; margin-left:auto; width:max-content; }
    .mini-spark span { display:block; width:4px; border-radius:8px; background:#6B7BE9; opacity:.4; } .mini-spark span:nth-child(2),.mini-spark span:nth-child(5) { opacity:.65; } .mini-spark span:nth-child(4) { opacity:1; }
    .control-label { display:flex; align-items:center; gap:8px; margin:3px 0 3px; color:#5F718B; font-size:11px; font-weight:800; letter-spacing:.1em; text-transform:uppercase; }
    .control-label::before { content:""; width:22px; height:1px; background:#A9C4EE; }
    .stat-card { border-top:3px solid transparent; background:linear-gradient(#FFF,#FFF) padding-box,linear-gradient(90deg,#4B88F5,#8B5CF6,#2DD4BF) border-box; }
    .widget:first-child { border-top:3px solid #4E8CF6; }
    @media(max-width:760px) { .command-deck { grid-template-columns:minmax(0,1fr) 150px; } .signal-orbit { display:block; transform:scale(.74); transform-origin:right center; } .command-copy { padding:25px; } }
    @media(max-width:580px) { .command-deck { grid-template-columns:1fr; } .signal-orbit { display:none; } }
    @media(max-width:760px) { .block-container { padding:20px 18px 52px; } .dashboard-title { font-size:26px; } .issue-head,.issue-row { grid-template-columns:1.15fr .9fr .9fr; } .issue-head > :nth-child(n+4),.issue-row > :nth-child(n+4) { display:none; } }
</style>
""",
        unsafe_allow_html=True,
    )

    st.link_button("← Back to upload", url="?view=upload")
    st.markdown('<div class="uc-nav"><div class="uc-identity"><span class="uc-mark">⌁</span>UNDER CONTROL</div><div class="uc-breadcrumb">Workspace / Project dashboard</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">ISSUE INTELLIGENCE</div>', unsafe_allow_html=True)
    st.markdown('<div class="dashboard-title">Turn issue history into clear direction.</div>', unsafe_allow_html=True)
    st.markdown('<div class="dashboard-subtitle">Project work, priority, delivery timing, and issue flow — arranged in one focused view.</div>', unsafe_allow_html=True)
    st.markdown('<span class="preview-label">Dashboard layout preview</span>', unsafe_allow_html=True)
    st.markdown(
        '<div class="command-deck">'
        '<div class="command-copy"><div class="command-eyebrow">PROJECT COMMAND CENTER</div>'
        '<div class="command-title">Follow the work. Catch friction early.</div>'
        '<div class="command-text">One visual home for projects, issues, priority, timing, and story points — built around your Jira structure.</div>'
        '<div class="command-tags"><span>Projects</span><span>Issue flow</span><span>Priority</span><span>Delivery time</span></div></div>'
        '<div class="signal-orbit"><span class="orbit-dot one"></span><span class="orbit-dot two"></span><span class="orbit-dot three"></span><div class="orbit-core">⌁</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="signal-path"><span class="path-label">Issue path</span>'
        '<div class="path-node one">Project<small>project_key</small></div><span class="path-link"></span>'
        '<div class="path-node two">Issue<small>issue_key</small></div><span class="path-link"></span>'
        '<div class="path-node three">Status<small>status</small></div><span class="path-link"></span>'
        '<div class="path-node four">Resolution<small>resolution</small></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="control-label">Dashboard controls</div>', unsafe_allow_html=True)

    first_filter, second_filter, third_filter = st.columns([1.25, 1, 1])
    with first_filter:
        st.selectbox("Project", ["Choose a project"], disabled=True)
    with second_filter:
        st.selectbox("Issue status", ["All statuses"], disabled=True)
    with third_filter:
        st.selectbox("Priority", ["All priorities"], disabled=True)

    metrics = st.columns(4)
    stat_definitions = [
        ("Total issues", "issue_id · issue_key"),
        ("Resolved work", "status · resolution"),
        ("Resolution time", "resolution_time_minutes"),
        ("Story points", "story_point"),
    ]
    for column, (label, source) in zip(metrics, stat_definitions):
        with column:
            st.markdown(f'<div class="stat-card"><div class="stat-label">{label}</div><div class="stat-value">—</div><div class="stat-source">{source}</div><div class="mini-spark"><span style="height:35%"></span><span style="height:56%"></span><span style="height:43%"></span><span style="height:84%"></span><span style="height:64%"></span></div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-name">Delivery signals</div>', unsafe_allow_html=True)
    flow_column, priority_column = st.columns([1.62, 1], gap="large")
    with flow_column:
        st.markdown(
            '''<div class="widget"><div class="widget-head"><div><div class="widget-title">Issue lifecycle</div><div class="widget-note">From creation to resolution</div></div><span class="field-chip">creation_date · resolution_date</span></div>
            <svg viewBox="0 0 720 180" width="100%" height="178" role="img" aria-label="Issue flow visual placeholder"><defs><linearGradient id="blueArea" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#4B88F5" stop-opacity=".22"/><stop offset="1" stop-color="#4B88F5" stop-opacity="0"/></linearGradient><linearGradient id="violetArea" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#8B5CF6" stop-opacity=".16"/><stop offset="1" stop-color="#8B5CF6" stop-opacity="0"/></linearGradient></defs><g stroke="#EDF1F7" stroke-width="1"><line x1="0" x2="720" y1="25" y2="25"/><line x1="0" x2="720" y1="75" y2="75"/><line x1="0" x2="720" y1="125" y2="125"/></g><path d="M0 125 C64 114 80 92 139 96 S216 57 277 71 S361 43 424 55 S520 35 570 54 S665 33 720 42 L720 180 L0 180Z" fill="url(#blueArea)"/><path d="M0 125 C64 114 80 92 139 96 S216 57 277 71 S361 43 424 55 S520 35 570 54 S665 33 720 42" fill="none" stroke="#4687F5" stroke-width="3"/><path d="M0 147 C61 140 97 148 146 129 S224 132 280 115 S365 133 431 106 S530 121 588 93 S666 112 720 97 L720 180 L0 180Z" fill="url(#violetArea)"/><path d="M0 147 C61 140 97 148 146 129 S224 132 280 115 S365 133 431 106 S530 121 588 93 S666 112 720 97" fill="none" stroke="#8B5CF6" stroke-width="3"/></svg><div class="legend"><span><i style="background:#4687F5"></i>Created</span><span><i style="background:#8B5CF6"></i>Resolved</span></div></div>''',
            unsafe_allow_html=True,
        )
    with priority_column:
        st.markdown(
            '''<div class="widget"><div class="widget-head"><div><div class="widget-title">Priority mix</div><div class="widget-note">Issue severity distribution</div></div><span class="field-chip">priority</span></div>
            <div class="priority-row"><span class="priority-name">Blocker</span><span class="priority-track"><span class="priority-fill" style="display:block;width:30%;background:#FB7185"></span></span><span class="priority-value">—</span></div>
            <div class="priority-row"><span class="priority-name">Critical</span><span class="priority-track"><span class="priority-fill" style="display:block;width:48%;background:#F59E0B"></span></span><span class="priority-value">—</span></div>
            <div class="priority-row"><span class="priority-name">Major</span><span class="priority-track"><span class="priority-fill" style="display:block;width:76%;background:#5B8DF5"></span></span><span class="priority-value">—</span></div>
            <div class="priority-row"><span class="priority-name">Minor</span><span class="priority-track"><span class="priority-fill" style="display:block;width:57%;background:#2DD4BF"></span></span><span class="priority-value">—</span></div></div>''',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-name">Work context</div>', unsafe_allow_html=True)
    type_column, context_column = st.columns([1, 1], gap="large")
    with type_column:
        st.markdown('<div class="widget"><div class="widget-head"><div><div class="widget-title">Issue types</div><div class="widget-note">How work is categorised</div></div><span class="field-chip">type</span></div><div class="type-list"><div class="type-item"><span class="type-dot" style="background:#4F8AF7"></span>Bug</div><div class="type-item"><span class="type-dot" style="background:#8B5CF6"></span>Story</div><div class="type-item"><span class="type-dot" style="background:#2DD4BF"></span>Task</div><div class="type-item"><span class="type-dot" style="background:#FB9A5B"></span>Improvement</div></div></div>', unsafe_allow_html=True)
    with context_column:
        st.markdown('<div class="widget"><div class="widget-head"><div><div class="widget-title">Project identifiers</div><div class="widget-note">Identifiers and work detail</div></div><span class="field-chip">project_key · text</span></div><div class="type-list"><div class="type-item"><span class="type-dot" style="background:#386FF0"></span>project_key</div><div class="type-item"><span class="type-dot" style="background:#7B61E6"></span>project_name</div><div class="type-item"><span class="type-dot" style="background:#20BDAA"></span>issue_key</div><div class="type-item"><span class="type-dot" style="background:#F2895B"></span>text</div></div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-name">Issue register</div>', unsafe_allow_html=True)
    table_head = '<div class="issue-head"><span>Issue key</span><span>Type</span><span>Priority</span><span>Status</span><span>Created</span><span>Story points</span></div>'
    table_row = '<div class="issue-row"><span class="skeleton"></span><span class="soft-tag"></span><span class="soft-tag"></span><span class="soft-tag"></span><span class="skeleton"></span><span class="skeleton"></span></div>'
    st.markdown(f'<div class="issue-shell">{table_head}{table_row}{table_row}{table_row}</div>', unsafe_allow_html=True)
