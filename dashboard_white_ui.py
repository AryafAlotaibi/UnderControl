import html

import pandas as pd
import streamlit as st


# These aliases are only for displaying the uploaded table. The backend continues
# to receive the original dataframe and keeps its own schema mapping unchanged.
DISPLAY_ALIASES = {
    "issue_id": ("issue_id", "Issue id", "Task ID"),
    "issue_key": ("issue_key", "Issue key", "Task key"),
    "text": ("text", "Summary", "Task name", "Title", "Description"),
    "project_key": ("project_key", "Project key"),
    "project_name": ("project_name", "Project name", "Project"),
    "type": ("type", "Issue Type", "Task type"),
    "priority": ("priority", "Priority"),
    "status": ("status", "Status", "Task status"),
    "resolution": ("resolution", "Resolution"),
    "assignee_id": ("assignee_id", "Custom field (Assignee_ID)", "Assignee"),
    "creation_date": ("creation_date", "Created", "Creation date"),
    "due_date": ("due_date", "Due date", "Deadline"),
    "resolution_date": ("resolution_date", "Resolved", "Resolution date"),
    "story_point": ("story_point", "Story points", "Story Points", "Custom field (Story Points)"),
    "resolution_time_minutes": ("resolution_time_minutes",),
}


def populated(df, column):
    if column not in df:
        return pd.Series(False, index=df.index)
    values = df[column].astype("string").str.strip()
    return (values.notna() & ~values.str.lower().isin(["", "nan", "none", "null", "nat"])).fillna(False)


def prepare_dashboard_data(user_df):
    """Read common Jira/standard headings for presentation; keep raw data intact."""
    lookup = {str(c).strip().casefold(): c for c in user_df.columns}
    frame = pd.DataFrame(index=user_df.index)
    for target, aliases in DISPLAY_ALIASES.items():
        for alias in aliases:
            source = lookup.get(alias.casefold())
            if source is not None and populated(user_df, source).any():
                frame[target] = user_df[source].copy()
                break
    for column in ("creation_date", "due_date", "resolution_date"):
        if column in frame:
            frame[column] = pd.to_datetime(frame[column], errors="coerce", format="mixed", utc=True).dt.tz_convert(None)
    for column in ("story_point", "resolution_time_minutes"):
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    for column in ("status", "priority", "type", "assignee_id", "project_name", "project_key"):
        if column in frame:
            frame[column] = frame[column].astype("string").str.strip()
    return frame


def display_values(df, field):
    if field not in df:
        return pd.Series("Not provided", index=df.index, dtype="string")
    return df[field].astype("string").str.strip().where(populated(df, field), "Not provided")


RISK_PILL_STYLES = {
    "low": ("#15803D", "#ECFDF5", "#A7F3D0"),
    "medium": ("#B45309", "#FFFBEB", "#FDE68A"),
    "high": ("#B91C1C", "#FEF2F2", "#FECACA"),
}
CONFIDENCE_PILL_STYLES = {
    "high": ("#1D4ED8", "#EFF6FF", "#BFDBFE"),
    "medium": ("#6D28D9", "#F5F3FF", "#DDD6FE"),
    "low": ("#475569", "#F1F5F9", "#E2E8F0"),
}
DEFAULT_PILL_STYLE = ("#475569", "#F1F5F9", "#E2E8F0")

APPROACH_LABELS = {
    "direct_blocker_removal": "Direct blocker removal",
    "capacity_reallocation": "Capacity reallocation",
    "schedule_containment": "Schedule containment",
    "parallel_mitigation": "Parallel mitigation",
}


def _pill(label, value, styles):
    fg, bg, border = styles.get(str(value).lower(), DEFAULT_PILL_STYLE)
    text = f"{label}: {str(value).title()}"
    return (
        f'<span class="sim-pill" style="color:{fg};background:{bg};border-color:{border}">'
        f'{html.escape(text)}</span>'
    )


def metric_card(label, value, note):
    unavailable = value is None or (isinstance(value, float) and pd.isna(value))
    value_text = "Not available" if unavailable else str(value)
    size = "font-size:19px" if unavailable else ""
    st.markdown(
        f'<div class="stat-card"><div class="stat-label">{html.escape(label)}</div>'
        f'<div class="stat-value" style="{size}">{html.escape(value_text)}</div>'
        f'<div class="stat-source">{html.escape(note)}</div></div>', unsafe_allow_html=True
    )


def render_distribution(frame, field, title, color):
    with st.container(border=True):
        st.subheader(title)
        if not populated(frame, field).any():
            st.info("Not enough data to display this chart. Add " + title.lower() + " to your file.")
            return
        counts = display_values(frame, field).value_counts().rename_axis(title).rename("Tasks").reset_index()
        # A fixed, non-zoomable count axis keeps scroll gestures from panning
        # the plot into negative values or clipping the bars.
        maximum = int(counts["Tasks"].max())
        chart = {
            "height": max(200, min(len(counts) * 40, 800)),
            "encoding": {
                "y": {"field": title, "type": "nominal", "sort": "-x", "title": None,
                      "axis": {"labelLimit": 180}},
                "x": {"field": "Tasks", "type": "quantitative", "title": "Tasks",
                      "scale": {"domain": [0, maximum + max(1, maximum * 0.15)], "nice": False, "zero": True},
                      "axis": {"format": "d", "tickMinStep": 1}},
                "tooltip": [{"field": title, "type": "nominal"},
                            {"field": "Tasks", "type": "quantitative", "format": "d"}],
            },
            "layer": [
                {"mark": {"type": "bar", "color": color, "cornerRadiusEnd": 4, "size": 25}},
                {"mark": {"type": "text", "align": "left", "dx": 6, "color": "#273751"},
                 "encoding": {"text": {"field": "Tasks", "type": "quantitative", "format": "d"}}},
            ],
            "background": "#FFFFFF", "config": {"view": {"stroke": None}, "axis": {"labelColor": "#60718A", "titleColor": "#60718A", "gridColor": "#E5ECF7", "domain": False, "labelFontSize": 12}},
        }
        st.vega_lite_chart(counts, chart, width="stretch", theme=None, key=f"distribution_{field}")


def render_dashboard_ui(analysis_output=None, simulation_output=None, project_df=None, project_metrics=None, source_name=None) -> None:
    """Display real uploaded task data and the unchanged backend analysis result."""
    st.markdown(
        """
<style>
    .stApp { background: #F8FAFE; color: #16223B; }
    .stApp h1,.stApp h2,.stApp h3 { color: #16223B; }
    div[data-testid="stSelectbox"] input, div[data-testid="stSelectbox"] span { color: #273751 !important; -webkit-text-fill-color: #273751; }
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
    .stat-card { height:128px; display:flex; flex-direction:column; margin-bottom:12px; }
    .stat-value { margin-top:10px; line-height:32px; flex-shrink:0; color:#16223B; font-size:28px; font-weight:790; letter-spacing:-.06em; }
    .stat-source { margin-top:auto; color:#A0AEC1; font-size:10px; }
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
    div[data-testid="stExpander"] { background:#FFFFFF; border:1px solid #E5ECF7 !important; border-radius:14px; overflow:hidden; margin-bottom:10px; }
    div[data-testid="stExpander"] summary { background:#F8FAFF !important; padding:12px 16px !important; }
    div[data-testid="stExpander"] summary span, div[data-testid="stExpander"] summary p { color:#182641 !important; font-weight:650 !important; }
    div[data-testid="stExpander"] summary svg { color:#5C78AC !important; fill:#5C78AC !important; }
    div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] { padding:14px 16px 16px; }
    .sim-intro { padding:16px 18px; margin:4px 0 20px; background:linear-gradient(90deg,#F5F9FF,#FFFFFF); border:1px solid #E1EAF7; border-left:4px solid #4B88F5; border-radius:14px; color:#334463; font-size:13.5px; line-height:1.65; }
    .scenario-card { position:relative; background:#FFFFFF; border:1px solid #E5ECF7; border-left:5px solid #94A3B8; border-radius:16px; padding:18px 20px; margin-bottom:16px; box-shadow:0 10px 24px rgba(27,55,97,.045); }
    .scenario-card.recommended { border-left-color:#2DD4BF; box-shadow:0 14px 30px rgba(45,212,191,.16); }
    .scenario-card-head { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; flex-wrap:wrap; margin-bottom:8px; }
    .scenario-name { color:#16223B; font-size:16px; font-weight:780; letter-spacing:-.02em; }
    .scenario-name .star { color:#F59E0B; margin-right:6px; }
    .scenario-approach { display:inline-block; margin-top:4px; color:#5C78AC; font-size:10.5px; font-weight:750; letter-spacing:.03em; text-transform:uppercase; }
    .scenario-pills { display:flex; gap:6px; flex-wrap:wrap; }
    .sim-pill { display:inline-flex; align-items:center; padding:3px 9px; border-radius:99px; font-size:10.5px; font-weight:750; border:1px solid; white-space:nowrap; }
    .scenario-basis { display:flex; gap:7px; align-items:flex-start; margin:10px 0 4px; padding:8px 11px; background:#F5F9FF; border:1px solid #DCE8FB; border-radius:10px; }
    .scenario-basis .basis-label { flex:0 0 auto; color:#2854AD; font-size:10px; font-weight:800; letter-spacing:.04em; text-transform:uppercase; }
    .scenario-basis .basis-text { color:#3C567F; font-size:12px; line-height:1.5; }
    .scenario-summary { color:#425068; font-size:13.5px; line-height:1.6; margin:6px 0 14px; }
    .scenario-actions-title { color:#8492AD; font-size:10px; font-weight:800; letter-spacing:.09em; text-transform:uppercase; margin-bottom:8px; }
    .action-row { display:flex; gap:10px; align-items:flex-start; padding:9px 0; border-top:1px solid #F0F4FA; }
    .action-row:first-of-type { border-top:none; }
    .action-tag { flex:0 0 auto; margin-top:1px; padding:3px 8px; background:#EEF2FF; color:#4338CA; border-radius:7px; font-size:9.5px; font-weight:800; text-transform:uppercase; letter-spacing:.03em; }
    .action-body { flex:1; min-width:0; }
    .action-desc { color:#334463; font-size:13px; line-height:1.55; }
    .action-targets { color:#8DA0BC; font-size:11px; margin-top:2px; }
    .scenario-tradeoffs { margin-top:14px; padding:11px 14px; background:#FFFBEB; border:1px solid #FDE68A; border-radius:11px; }
    .scenario-tradeoffs strong { color:#92400E; font-size:11px; text-transform:uppercase; letter-spacing:.06em; }
    .scenario-tradeoffs p { margin:5px 0 0; color:#78460D; font-size:12.5px; line-height:1.55; }
    .scenario-card details { margin-top:12px; }
    .scenario-card summary { cursor:pointer; color:#5C78AC; font-size:11.5px; font-weight:750; list-style:none; }
    .scenario-card summary::-webkit-details-marker { display:none; }
    .scenario-card summary::before { content:"▸ "; }
    .scenario-card details[open] summary::before { content:"▾ "; }
    .scenario-evidence { margin:8px 0 0; padding-left:0; list-style:none; }
    .scenario-evidence li { color:#6C7B96; font-size:12px; line-height:1.6; padding-left:14px; position:relative; margin-bottom:4px; }
    .scenario-evidence li::before { content:"•"; position:absolute; left:0; color:#B7C6E0; }
    .recommend-banner { display:flex; align-items:flex-start; gap:12px; margin:6px 0 18px; padding:16px 18px; background:linear-gradient(120deg,#ECFDF5,#F0FDFA); border:1px solid #A7F3D0; border-radius:16px; }
    .recommend-banner .rb-icon { flex:0 0 auto; width:34px; height:34px; display:grid; place-items:center; background:#16A34A; color:#FFF; border-radius:10px; font-size:16px; }
    .recommend-banner .rb-content strong { display:block; color:#065F46; font-size:13px; margin-bottom:3px; }
    .recommend-banner .rb-content span { color:#0F766E; font-size:12.5px; line-height:1.6; }
    @media(max-width:760px) { .command-deck { grid-template-columns:minmax(0,1fr) 150px; } .signal-orbit { display:block; transform:scale(.74); transform-origin:right center; } .command-copy { padding:25px; } }
    @media(max-width:580px) { .command-deck { grid-template-columns:1fr; } .signal-orbit { display:none; } }
    @media(max-width:760px) { .block-container { padding:20px 18px 52px; } .dashboard-title { font-size:26px; } .issue-head,.issue-row { grid-template-columns:1.15fr .9fr .9fr; } .issue-head > :nth-child(n+4),.issue-row > :nth-child(n+4) { display:none; } }
</style>
""",
        unsafe_allow_html=True,
    )

    if st.button("← Upload another file", key="dashboard_back"):
        for key in ("analysis_output", "simulation_output", "project_dataframe", "project_metrics", "analyzed_filename"):
            st.session_state.pop(key, None)
        st.session_state["uploader_version"] = st.session_state.get("uploader_version", 0) + 1
        for key in ("dashboard_project", "dashboard_status", "dashboard_priority"):
            st.session_state.pop(key, None)
        st.query_params["view"] = "upload"
        st.rerun()

    st.markdown('<div class="uc-nav"><div class="uc-identity"><span class="uc-mark">⌁</span>UNDER CONTROL</div><div class="uc-breadcrumb">Workspace / Project dashboard</div></div>', unsafe_allow_html=True)
    if not analysis_output or project_df is None or len(project_df) == 0:
        st.info("No complete dashboard is available in this session. Upload your project CSV and select Analyze Project to view its results.")
        return

    st.markdown('<div class="eyebrow">PROJECT OVERVIEW</div>', unsafe_allow_html=True)
    st.markdown('<div class="dashboard-title">Your project at a glance.</div>', unsafe_allow_html=True)
    st.caption(f"Source: {source_name or 'Uploaded project'} · {len(project_df):,} tasks analyzed")

    state = analysis_output.get("project_state")
    state_label = {"healthy": "Healthy", "delayed": "Delayed", "uncertain": "Not enough evidence to determine project health"}.get(state, "Project health unavailable")
    state_detail = {
        "healthy": "The analysis found evidence supporting a healthy project state.",
        "delayed": "The analysis found evidence of project delay. Review the supporting findings below.",
        "uncertain": "You can explore the available task data below. More information is needed to determine overall project health."
    }.get(state, "Review the available data and analysis limitations below.")
    st.markdown(
        '<div class="command-deck"><div class="command-copy">'
        '<div class="command-eyebrow">PROJECT HEALTH</div>'
        f'<div class="command-title">{html.escape(state_label)}</div>'
        f'<div class="command-text">{html.escape(state_detail)}</div>'
        f'<div class="command-tags"><span>Confidence: {html.escape(str(analysis_output.get("confidence", "Unavailable")).title())}</span></div>'
        '</div><div class="signal-orbit"><span class="orbit-dot one"></span><span class="orbit-dot two"></span><span class="orbit-dot three"></span><div class="orbit-core">⌁</div></div></div>',
        unsafe_allow_html=True,
    )
    # Analysis limitations come only from the Analysis Agent. The dashboard does
    # not invent analytical warnings from the uploaded CSV.
    warnings = list(analysis_output.get("data_warnings") or [])
    delay = analysis_output.get("estimated_delay_days")
    if warnings:
        st.warning("The Analysis Agent reported limitations in the available evidence.")
        with st.expander("Analysis Agent data warnings", expanded=True):
            for warning in dict.fromkeys(warnings):
                st.write("• " + str(warning))

    st.markdown('<div class="section-name">Analysis of the full uploaded project</div>', unsafe_allow_html=True)
    # These values are displayed exactly from the structured Analysis Agent output.
    signals = analysis_output.get("schedule_signals") or {}
    overview = [
        ("Estimated delay", None if delay is None else f"{delay:g} days", "Analysis Agent"),
        ("Blocked tasks", signals.get("blocked_tasks"), "Analysis Agent schedule signal"),
        ("Overdue tasks", signals.get("overdue_tasks"), "Analysis Agent schedule signal"),
        ("High-priority unfinished", signals.get("unfinished_high_priority_tasks"), "Analysis Agent schedule signal"),
    ]
    for column, (label, value, note) in zip(st.columns(4), overview):
        with column:
            metric_card(label, value, note)

    st.markdown('<div class="section-name">Explore tasks</div>', unsafe_allow_html=True)
    st.caption("Filters update the task cards, charts and register below. The analysis above and findings below describe the full upload.")
    filtered = project_df.copy()
    project_column = "project_name" if populated(filtered, "project_name").any() else "project_key"
    for container, field, label, key in zip(
        st.columns([1.25, 1, 1]),
        (project_column, "status", "priority"),
        ("Project", "Issue status", "Priority"),
        ("dashboard_project", "dashboard_status", "dashboard_priority"),
    ):
        with container:
            values = display_values(project_df, field)
            options = sorted(values.unique().tolist()) if populated(project_df, field).any() else []
            selected = st.selectbox(label, [None] + options, format_func=lambda value: "All" if value is None else value,
                                    key=key, disabled=not options)
            if selected is not None:
                filtered = filtered[display_values(filtered, field) == selected]

    if len(filtered) == 0:
        st.info("No tasks match these filters. Choose All to broaden your selection.")
    else:
        st.caption(f"{len(filtered):,} tasks match your filters")
        for container, field, title, color in zip(st.columns(2), ("status", "priority"), ("Issue status", "Priority mix"), ("#4B88F5", "#8B5CF6")):
            with container:
                render_distribution(filtered, field, title, color)
        render_distribution(filtered, "assignee_id", "Tasks per assignee", "#4B88F5")

        labels = {"issue_key": "Issue", "issue_id": "ID", "text": "Task details", "type": "Type", "priority": "Priority", "status": "Status", "assignee_id": "Assignee", "creation_date": "Created", "due_date": "Due", "resolution_date": "Resolved", "story_point": "Story points"}
        columns = [c for c in labels if c in filtered and populated(filtered, c).any()]
        with st.expander(f"View full issue register ({len(filtered):,} tasks)"):
            if columns:
                date_columns = {
                    labels[c]: st.column_config.DatetimeColumn(labels[c], format="YYYY-MM-DD")
                    for c in ("creation_date", "due_date", "resolution_date") if c in columns
                }
                st.dataframe(filtered[columns].rename(columns=labels), hide_index=True,
                             width="stretch", column_config=date_columns)
            else:
                st.info("Task details cannot be displayed with the column names supplied in this file.")

    st.markdown('<div class="section-name">Analysis findings · full upload</div>', unsafe_allow_html=True)
    root = analysis_output.get("root_cause")
    with st.container(border=True):
        st.subheader("Root cause")
        if root:
            category = root.get("category")
            if category:
                st.caption(f"Category: {category}")
            st.write(root.get("summary") or "Not provided by the Analysis Agent.")
            st.write(root.get("explanation") or "Not provided by the Analysis Agent.")
            affected = root.get("affected_tasks") or []
            st.write("Affected tasks: " + (", ".join(map(str, affected)) if affected else "Not provided by the Analysis Agent."))
        else:
            st.info("Not provided by the Analysis Agent.")

    tabs = st.tabs(["Bottlenecks", "Critical tasks", "Dependencies", "Workload"])
    with tabs[0]:
        rows = analysis_output.get("bottlenecks") or []
        if not rows:
            st.info("Not provided by the Analysis Agent.")
        for item in rows:
            task_id = item.get("task_id") or "Task"
            summary = item.get("summary") or ""
            with st.expander(f"{task_id} · {summary}".rstrip(" ·"), expanded=True):
                details = []
                if item.get("status"):
                    details.append(f"Status: {item['status']}")
                if item.get("priority"):
                    details.append(f"Priority: {item['priority']}")
                if item.get("assignee"):
                    details.append(f"Assignee: {item['assignee']}")
                if details:
                    st.caption(" · ".join(details))
                st.write("Reason: " + (item.get("reason") or "Not provided by the Analysis Agent."))
                st.write("Impact: " + (item.get("impact") or "Not provided by the Analysis Agent."))
                affected = item.get("affected_tasks") or []
                st.write("Affected tasks: " + (", ".join(map(str, affected)) if affected else "Not provided by the Analysis Agent."))
    with tabs[1]:
        rows = analysis_output.get("critical_tasks") or []
        if rows:
            st.dataframe(
                pd.DataFrame(rows).rename(columns={"task_id": "Task", "reason": "Why it matters"}),
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("Not provided by the Analysis Agent.")
    with tabs[2]:
        rows = analysis_output.get("dependencies") or []
        if rows:
            dependency_df = pd.DataFrame(rows).rename(columns={
                "blocked_task": "Blocked task",
                "depends_on": "Depends on",
                "impact": "Impact",
                "affected_tasks": "Affected tasks",
            })
            st.dataframe(dependency_df, hide_index=True, use_container_width=True)
        else:
            st.info("Not provided by the Analysis Agent.")
    with tabs[3]:
        rows = analysis_output.get("workload_signals") or []
        if not rows:
            st.info("Not provided by the Analysis Agent.")
        for item in rows:
            with st.container(border=True):
                st.write(f"Assignee: {item.get('assignee') or 'Not provided by the Analysis Agent.'}")
                st.write("Issue: " + (item.get("issue") or "Not provided by the Analysis Agent."))
                related = item.get("related_tasks") or []
                st.write("Related tasks: " + (", ".join(map(str, related)) if related else "Not provided by the Analysis Agent."))

    st.markdown('<div class="section-name">Recovery scenarios · Simulation Agent</div>', unsafe_allow_html=True)
    if not simulation_output:
        st.info("No simulation is available in this session.")
    else:
        baseline = simulation_output.get("baseline_summary")
        if baseline:
            st.markdown(f'<div class="sim-intro">{html.escape(baseline)}</div>', unsafe_allow_html=True)

        recommended = simulation_output.get("recommended_scenario")
        scenarios = simulation_output.get("scenarios") or []

        if not scenarios:
            st.info("Not provided by the Simulation Agent.")

        for scenario in scenarios:
            name = scenario.get("scenario_name") or "Scenario"
            is_recommended = bool(recommended) and name == recommended

            pills = ""
            risk = scenario.get("projected_risk")
            if risk:
                pills += _pill("Risk", risk, RISK_PILL_STYLES)
            confidence = scenario.get("confidence")
            if confidence:
                pills += _pill("Confidence", confidence, CONFIDENCE_PILL_STYLES)
            delay = scenario.get("projected_delay_days")
            if delay is not None:
                pills += _pill("Delay change", f"{delay:g} days", {})

            actions_html = ""
            for action in scenario.get("actions") or []:
                targets = ", ".join(action.get("target_tasks") or []) or "Not specified"
                action_type = action.get("action_type") or "action"
                description = action.get("description") or ""
                actions_html += (
                    '<div class="action-row">'
                    f'<span class="action-tag">{html.escape(action_type)}</span>'
                    '<div class="action-body">'
                    f'<div class="action-desc">{html.escape(description)}</div>'
                    f'<div class="action-targets">Targets: {html.escape(targets)}</div>'
                    '</div></div>'
                )

            evidence_html = ""
            evidence = scenario.get("supporting_evidence") or []
            if evidence:
                items = "".join(f"<li>{html.escape(str(item))}</li>" for item in evidence)
                evidence_html = f'<details><summary>Supporting evidence</summary><ul class="scenario-evidence">{items}</ul></details>'

            summary = scenario.get("summary") or ""
            tradeoffs = scenario.get("tradeoffs") or "Not provided by the Simulation Agent."
            star = '<span class="star">⭐</span>' if is_recommended else ""
            card_class = "scenario-card recommended" if is_recommended else "scenario-card"
            approach_label = APPROACH_LABELS.get(scenario.get("approach_type"), "")
            approach_html = f'<div class="scenario-approach">{html.escape(approach_label)}</div>' if approach_label else ""
            basis = scenario.get("basis")
            basis_html = (
                '<div class="scenario-basis"><span class="basis-label">Grounded in</span>'
                f'<span class="basis-text">{html.escape(basis)}</span></div>'
                if basis else ""
            )

            st.markdown(
                f'<div class="{card_class}">'
                '<div class="scenario-card-head">'
                f'<div><div class="scenario-name">{star}{html.escape(name)}</div>{approach_html}</div>'
                f'<div class="scenario-pills">{pills}</div>'
                '</div>'
                + basis_html
                + f'<div class="scenario-summary">{html.escape(summary)}</div>'
                + (
                    '<div class="scenario-actions-title">Recovery actions</div>'
                    f'<div class="scenario-actions">{actions_html}</div>'
                    if actions_html else ""
                )
                + '<div class="scenario-tradeoffs"><strong>Tradeoffs</strong>'
                f'<p>{html.escape(tradeoffs)}</p></div>'
                + evidence_html
                + '</div>',
                unsafe_allow_html=True,
            )

        if recommended:
            rationale = simulation_output.get("recommendation_rationale") or ""
            st.markdown(
                '<div class="recommend-banner">'
                '<div class="rb-icon">✓</div>'
                '<div class="rb-content">'
                f'<strong>Recommended scenario: {html.escape(recommended)}</strong>'
                f'<span>{html.escape(rationale)}</span>'
                '</div></div>',
                unsafe_allow_html=True,
            )

        assumptions = simulation_output.get("assumptions") or []
        if assumptions:
            with st.expander("Assumptions behind these scenarios"):
                for item in assumptions:
                    st.write(f"• {item}")

        sim_warnings = simulation_output.get("data_warnings") or []
        if sim_warnings:
            with st.expander("Simulation Agent data warnings"):
                for item in sim_warnings:
                    st.write(f"• {item}")