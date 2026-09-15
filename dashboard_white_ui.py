import html

import pandas as pd
import streamlit as st

from analysis.project_analyzer import ProjectAnalyzer


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


def render_dashboard_ui(analysis_output=None, project_df=None, project_metrics=None, source_name=None) -> None:
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
    @media(max-width:760px) { .command-deck { grid-template-columns:minmax(0,1fr) 150px; } .signal-orbit { display:block; transform:scale(.74); transform-origin:right center; } .command-copy { padding:25px; } }
    @media(max-width:580px) { .command-deck { grid-template-columns:1fr; } .signal-orbit { display:none; } }
    @media(max-width:760px) { .block-container { padding:20px 18px 52px; } .dashboard-title { font-size:26px; } .issue-head,.issue-row { grid-template-columns:1.15fr .9fr .9fr; } .issue-head > :nth-child(n+4),.issue-row > :nth-child(n+4) { display:none; } }
</style>
""",
        unsafe_allow_html=True,
    )

    if st.button("← Upload another file", key="dashboard_back"):
        for key in ("analysis_output", "project_dataframe", "project_metrics", "analyzed_filename"):
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
    # Analysis notes are displayed exactly as returned by the Analysis Agent.
    # The dashboard does not create analytical warnings or infer missing evidence.
    warnings = analysis_output.get("data_warnings") or []
    delay = analysis_output.get("estimated_delay_days")
    if warnings:
        st.warning("Analysis Agent notes")
        with st.expander("Analysis Agent notes", expanded=True):
            for warning in warnings:
                st.write("• " + str(warning))

    st.markdown('<div class="section-name">Analysis of the full uploaded project</div>', unsafe_allow_html=True)
    signals = (project_metrics or {}).get("schedule_signals", analysis_output.get("schedule_signals") or {})
    has_status = populated(project_df, "status").any()
    has_resolution = any(populated(project_df, c).any() for c in ("status", "resolution", "resolution_date"))
    overview = [
        ("Estimated delay", None if delay is None else f"{delay:g} days", "Evidence-based estimate"),
        ("Blocked tasks", signals.get("blocked_tasks") if has_status else None, "Based on known statuses"),
        ("Overdue tasks", signals.get("overdue_tasks") if has_resolution and populated(project_df, "due_date").any() else None, "Unresolved tasks past their due date"),
        ("High-priority unfinished", signals.get("unfinished_high_priority_tasks") if has_resolution and populated(project_df, "priority").any() else None, "High, Highest, Critical or Blocker"),
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
        metrics = ProjectAnalyzer().prepare_project(filtered)["metrics"]
        known_resolution = any(populated(filtered, c).any() for c in ("status", "resolution", "resolution_date"))
        resolution = metrics.get("average_resolution_time_minutes")
        points = pd.to_numeric(filtered["story_point"], errors="coerce") if "story_point" in filtered else pd.Series(dtype=float)
        point_total = points.sum(min_count=1)
        stats = [
            ("Total issues", len(filtered), "Tasks matching your filters"),
            ("Resolved work", metrics.get("resolved_issues") if known_resolution else None, "Known completion signals"),
            ("Avg. resolution time", None if resolution is None else f"{resolution:,.0f} min", "Recorded resolution duration"),
            ("Story points", None if pd.isna(point_total) else f"{point_total:,.1f}", "Sum of available estimates"),
        ]
        for column, (label, value, note) in zip(st.columns(4), stats):
            with column:
                metric_card(label, value, note)
        for container, field, title, color in zip(st.columns(2), ("status", "priority"), ("Issue status", "Priority mix"), ("#4B88F5", "#8B5CF6")):
            with container:
                render_distribution(filtered, field, title, color)
        for container, field, title, color in zip(st.columns(2), ("type", "assignee_id"), ("Issue types", "Tasks per assignee"), ("#20BDAA", "#4B88F5")):
            with container:
                render_distribution(filtered, field, title, color)
        st.markdown('<div class="section-name">Issue register</div>', unsafe_allow_html=True)
        labels = {"issue_key": "Issue", "issue_id": "ID", "text": "Task details", "type": "Type", "priority": "Priority", "status": "Status", "assignee_id": "Assignee", "creation_date": "Created", "due_date": "Due", "resolution_date": "Resolved", "story_point": "Story points"}
        columns = [c for c in labels if c in filtered and populated(filtered, c).any()]
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
            st.write(root.get("summary", ""))
            st.write(root.get("explanation", ""))
        else:
            st.write("Not provided by the Analysis Agent.")

    tabs = st.tabs(["Bottlenecks", "Critical tasks", "Dependencies", "Workload", "Evidence"])
    with tabs[0]:
        rows = analysis_output.get("bottlenecks") or []
        if not rows:
            st.write("Not provided by the Analysis Agent.")
        for item in rows:
            with st.expander(f"{item.get('task_id', 'Task')} · {item.get('summary', '')}", expanded=True):
                st.write(item.get("reason", ""))
                st.write("Impact: " + item.get("impact", "Not available"))
    with tabs[1]:
        rows = analysis_output.get("critical_tasks") or []
        if rows:
            st.dataframe(pd.DataFrame(rows).rename(columns={"task_id": "Task", "reason": "Why it matters"}), hide_index=True, use_container_width=True)
        else:
            st.write("Not provided by the Analysis Agent.")
    with tabs[2]:
        rows = analysis_output.get("dependencies") or []
        if rows:
            st.dataframe(pd.DataFrame(rows).rename(columns={"blocked_task": "Blocked task", "depends_on": "Depends on", "impact": "Impact", "affected_tasks": "Affected tasks"}), hide_index=True, use_container_width=True)
        else:
            st.write("Not provided by the Analysis Agent.")
    with tabs[3]:
        rows = analysis_output.get("workload_signals") or []
        for item in rows:
            st.write(f"Assignee {item.get('assignee') or 'unavailable'}: {item.get('issue', '')}")
        if not rows:
            st.write("Not provided by the Analysis Agent.")
    with tabs[4]:
        rows = analysis_output.get("evidence") or []
        for item in rows:
            st.write(f"• {item}")
        if not rows:
            st.write("Not provided by the Analysis Agent.")
