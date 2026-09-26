# import html

# import pandas as pd
# import streamlit as st

# from analysis.project_analyzer import ProjectAnalyzer


# # These aliases are only for displaying the uploaded table. The backend continues
# # to receive the original dataframe and keeps its own schema mapping unchanged.
# DISPLAY_ALIASES = {
#     "issue_id": ("issue_id", "Issue id", "Task ID"),
#     "issue_key": ("issue_key", "Issue key", "Task key"),
#     "text": ("text", "Summary", "Task name", "Title", "Description"),
#     "project_key": ("project_key", "Project key"),
#     "project_name": ("project_name", "Project name", "Project"),
#     "type": ("type", "Issue Type", "Task type"),
#     "priority": ("priority", "Priority"),
#     "status": ("status", "Status", "Task status"),
#     "resolution": ("resolution", "Resolution"),
#     "assignee_id": ("assignee_id", "Custom field (Assignee_ID)", "Assignee"),
#     "creation_date": ("creation_date", "Created", "Creation date"),
#     "due_date": ("due_date", "Due date", "Deadline"),
#     "resolution_date": ("resolution_date", "Resolved", "Resolution date"),
#     "story_point": ("story_point", "Story points", "Story Points", "Custom field (Story Points)"),
#     "resolution_time_minutes": ("resolution_time_minutes",),
# }


# def populated(df, column):
#     if column not in df:
#         return pd.Series(False, index=df.index)
#     values = df[column].astype("string").str.strip()
#     return (values.notna() & ~values.str.lower().isin(["", "nan", "none", "null", "nat"])).fillna(False)


# def prepare_dashboard_data(user_df):
#     """Read common Jira/standard headings for presentation; keep raw data intact."""
#     lookup = {str(c).strip().casefold(): c for c in user_df.columns}
#     frame = pd.DataFrame(index=user_df.index)
#     for target, aliases in DISPLAY_ALIASES.items():
#         for alias in aliases:
#             source = lookup.get(alias.casefold())
#             if source is not None and populated(user_df, source).any():
#                 frame[target] = user_df[source].copy()
#                 break
#     for column in ("creation_date", "due_date", "resolution_date"):
#         if column in frame:
#             frame[column] = pd.to_datetime(frame[column], errors="coerce", format="mixed", utc=True).dt.tz_convert(None)
#     for column in ("story_point", "resolution_time_minutes"):
#         if column in frame:
#             frame[column] = pd.to_numeric(frame[column], errors="coerce")
#     for column in ("status", "priority", "type", "assignee_id", "project_name", "project_key"):
#         if column in frame:
#             frame[column] = frame[column].astype("string").str.strip()
#     return frame


# def display_values(df, field):
#     if field not in df:
#         return pd.Series("Not provided", index=df.index, dtype="string")
#     return df[field].astype("string").str.strip().where(populated(df, field), "Not provided")


# def metric_card(label, value, note):
#     unavailable = value is None or (isinstance(value, float) and pd.isna(value))
#     value_text = "Not available" if unavailable else str(value)
#     size = "font-size:19px" if unavailable else ""
#     st.markdown(
#         f'<div class="stat-card"><div class="stat-label">{html.escape(label)}</div>'
#         f'<div class="stat-value" style="{size}">{html.escape(value_text)}</div>'
#         f'<div class="stat-source">{html.escape(note)}</div></div>', unsafe_allow_html=True
#     )


# def render_distribution(frame, field, title, color):
#     with st.container(border=True):
#         st.subheader(title)
#         if not populated(frame, field).any():
#             st.info("Not enough data to display this chart. Add " + title.lower() + " to your file.")
#             return
#         counts = display_values(frame, field).value_counts().rename_axis(title).rename("Tasks").reset_index()
#         # A fixed, non-zoomable count axis keeps scroll gestures from panning
#         # the plot into negative values or clipping the bars.
#         maximum = int(counts["Tasks"].max())
#         chart = {
#             "height": max(200, min(len(counts) * 40, 800)),
#             "encoding": {
#                 "y": {"field": title, "type": "nominal", "sort": "-x", "title": None,
#                       "axis": {"labelLimit": 180}},
#                 "x": {"field": "Tasks", "type": "quantitative", "title": "Tasks",
#                       "scale": {"domain": [0, maximum + max(1, maximum * 0.15)], "nice": False, "zero": True},
#                       "axis": {"format": "d", "tickMinStep": 1}},
#                 "tooltip": [{"field": title, "type": "nominal"},
#                             {"field": "Tasks", "type": "quantitative", "format": "d"}],
#             },
#             "layer": [
#                 {"mark": {"type": "bar", "color": color, "cornerRadiusEnd": 4, "size": 25}},
#                 {"mark": {"type": "text", "align": "left", "dx": 6, "color": "#273751"},
#                  "encoding": {"text": {"field": "Tasks", "type": "quantitative", "format": "d"}}},
#             ],
#             "background": "#FFFFFF", "config": {"view": {"stroke": None}, "axis": {"labelColor": "#60718A", "titleColor": "#60718A", "gridColor": "#E5ECF7", "domain": False, "labelFontSize": 12}},
#         }
#         st.vega_lite_chart(counts, chart, width="stretch", theme=None, key=f"distribution_{field}")


# def render_dashboard_ui(analysis_output=None, project_df=None, project_metrics=None, source_name=None, active_stage="analysis") -> None:
#     """Display real uploaded task data and the unchanged backend analysis result."""
#     st.markdown(
#         """
# <style>
#     .stApp { background: #F8FAFE; color: #16223B; }
#     .stApp h1,.stApp h2,.stApp h3 { color: #16223B; }
#     div[data-testid="stSelectbox"] input, div[data-testid="stSelectbox"] span { color: #273751 !important; -webkit-text-fill-color: #273751; }
#     header { visibility: hidden; }
#     .block-container { max-width: 1480px; padding: 24px 36px 72px; }
#     .uc-nav { display:flex; align-items:center; justify-content:space-between; padding:16px 2px 25px; }
#     .uc-identity { display:flex; align-items:center; gap:10px; color:#16223B; font-size:14px; font-weight:800; letter-spacing:-.02em; }
#     .uc-mark { display:grid; place-items:center; width:30px; height:30px; border-radius:10px; background:linear-gradient(140deg,#377DF5,#7157DF); color:#FFF; font-size:15px; box-shadow:0 7px 14px rgba(55,125,245,.22); }
#     .uc-breadcrumb { color:#9AA9BD; font-size:12px; font-weight:650; }
#     .eyebrow { color:#5C78AC; font-size:11px; font-weight:800; letter-spacing:.13em; text-transform:uppercase; }
#     .dashboard-title { margin:6px 0 5px; color:#14203A; font-size:32px; font-weight:780; letter-spacing:-.055em; }
#     .dashboard-subtitle { color:#7B8BA2; font-size:13px; margin-bottom:22px; }
#     .preview-label { display:inline-flex; align-items:center; gap:6px; padding:6px 9px; background:#EFF5FF; color:#5A77A5; border:1px solid #DBE8FB; border-radius:99px; font-size:10px; font-weight:750; }
#     .preview-label::before { content:""; width:6px; height:6px; border-radius:50%; background:#4F8AF7; }
#     .stat-card { min-height:128px; padding:18px; box-sizing:border-box; background:#FFF; border:1px solid #E5ECF7; border-radius:16px; box-shadow:0 10px 24px rgba(27,55,97,.045); overflow:hidden; position:relative; }
#     .stat-card::after { content:""; position:absolute; width:80px; height:80px; right:-25px; bottom:-39px; border-radius:50%; background:radial-gradient(circle,rgba(89,137,248,.12),transparent 68%); }
#     .stat-label { color:#74849C; font-size:11px; font-weight:700; }
#     .stat-card { height:128px; display:flex; flex-direction:column; margin-bottom:12px; }
#     .stat-value { margin-top:10px; line-height:32px; flex-shrink:0; color:#16223B; font-size:28px; font-weight:790; letter-spacing:-.06em; }
#     .stat-source { margin-top:auto; color:#A0AEC1; font-size:10px; }
#     .section-name { margin:29px 0 12px; color:#182641; font-size:16px; font-weight:760; letter-spacing:-.025em; }
#     .widget { height:100%; min-height:280px; box-sizing:border-box; padding:19px; background:#FFF; border:1px solid #E5ECF7; border-radius:16px; box-shadow:0 10px 24px rgba(27,55,97,.04); }
#     .widget-head { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:16px; }
#     .widget-title { color:#273751; font-size:13px; font-weight:760; }
#     .widget-note { color:#9AA9BC; font-size:10px; margin-top:4px; }
#     .field-chip { padding:5px 7px; background:#F3F7FC; border-radius:7px; color:#7F91AA; font-size:9px; font-weight:700; }
#     .legend { display:flex; gap:13px; color:#8796AA; font-size:10px; margin-top:7px; }
#     .legend i { display:inline-block; width:6px; height:6px; margin-right:4px; border-radius:50%; }
#     .priority-row { display:grid; grid-template-columns:72px 1fr 24px; align-items:center; gap:10px; margin:14px 0; }
#     .priority-name { color:#60718A; font-size:11px; font-weight:650; }
#     .priority-track { height:8px; overflow:hidden; background:#F0F4FA; border-radius:99px; }
#     .priority-fill { height:100%; border-radius:99px; }
#     .priority-value { color:#A2AFBE; font-size:10px; text-align:right; }
#     .type-list { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:18px; }
#     .type-item { display:flex; align-items:center; gap:8px; padding:10px; border:1px solid #EDF1F7; border-radius:10px; color:#60718A; font-size:11px; font-weight:650; }
#     .type-dot { width:8px; height:8px; border-radius:3px; flex:0 0 auto; }
#     .issue-shell { overflow:hidden; background:#FFF; border:1px solid #E5ECF7; border-radius:16px; box-shadow:0 10px 24px rgba(27,55,97,.04); }
#     .issue-head,.issue-row { display:grid; grid-template-columns:1.2fr .8fr .9fr .9fr .9fr 1fr; align-items:center; gap:12px; }
#     .issue-head { padding:13px 18px; background:#FBFCFF; color:#8A99AC; font-size:9px; font-weight:800; letter-spacing:.05em; text-transform:uppercase; }
#     .issue-row { padding:15px 18px; border-top:1px solid #EEF2F7; }
#     .skeleton { display:block; height:8px; border-radius:99px; background:linear-gradient(90deg,#EDF2F7 0%,#F8FAFD 48%,#EDF2F7 100%); }
#     .soft-tag { width:62%; height:17px; border-radius:6px; background:#F2F6FC; }
#     div[data-testid="stSelectbox"] label { color:#6D7E96; font-size:11px; font-weight:700; }
#     div[data-testid="stSelectbox"] > div > div { background:#FFF; border-color:#E1EAF5; border-radius:10px; }
#     .command-deck { position:relative; display:grid; grid-template-columns:1.18fr .82fr; min-height:185px; margin:20px 0 24px; overflow:hidden; background:linear-gradient(125deg,#152342 0%,#253D78 58%,#4A3C91 100%); border-radius:20px; box-shadow:0 22px 38px rgba(29,49,96,.16); }
#     .command-deck::before { content:""; position:absolute; inset:0; opacity:.38; background-image:linear-gradient(rgba(255,255,255,.12) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.12) 1px,transparent 1px); background-size:28px 28px; mask-image:linear-gradient(90deg,#000,transparent 82%); }
#     .command-copy { position:relative; z-index:1; align-self:center; padding:29px 31px; }
#     .command-eyebrow { color:#9EC1FF; font-size:10px; font-weight:800; letter-spacing:.14em; }
#     .command-title { max-width:390px; margin:8px 0 8px; color:#FFF; font-size:23px; font-weight:760; letter-spacing:-.04em; line-height:1.15; }
#     .command-text { max-width:400px; color:#C4D3F4; font-size:12px; line-height:1.6; }
#     .command-tags { display:flex; flex-wrap:wrap; gap:7px; margin-top:15px; }
#     .command-tags span { padding:5px 8px; border:1px solid rgba(210,226,255,.22); background:rgba(255,255,255,.08); border-radius:99px; color:#E7F0FF; font-size:10px; font-weight:650; }
#     .signal-orbit { position:relative; align-self:center; justify-self:center; width:145px; height:145px; z-index:1; }
#     .signal-orbit::before,.signal-orbit::after { content:""; position:absolute; inset:10px; border:1px solid rgba(192,211,255,.24); border-radius:50%; }
#     .signal-orbit::after { inset:30px; border-color:rgba(79,235,215,.45); box-shadow:0 0 28px rgba(72,203,255,.22); }
#     .orbit-core { position:absolute; inset:48px; display:grid; place-items:center; border-radius:50%; background:linear-gradient(145deg,#63A4FF,#7A5BEE); color:#FFF; font-size:22px; box-shadow:0 0 0 10px rgba(135,114,255,.12),0 12px 27px rgba(16,25,61,.35); }
#     .orbit-dot { position:absolute; display:block; width:9px; height:9px; border-radius:50%; box-shadow:0 0 0 4px rgba(255,255,255,.08); }
#     .orbit-dot.one { top:9px; left:66px; background:#67E8F9; } .orbit-dot.two { top:69px; right:1px; background:#FDBA74; } .orbit-dot.three { bottom:12px; left:22px; background:#C4B5FD; }
#     .signal-path { display:flex; align-items:center; gap:10px; margin:0 0 24px; padding:16px 18px; overflow-x:auto; border:1px solid #E4EAF5; border-radius:16px; background:linear-gradient(90deg,#FFF,#F6F9FF); box-shadow:0 10px 24px rgba(27,55,97,.035); }
#     .path-label { flex:0 0 auto; margin-right:5px; color:#8492AD; font-size:9px; font-weight:800; letter-spacing:.1em; text-transform:uppercase; }
#     .path-node { flex:0 0 auto; min-width:89px; padding:8px 10px; border-radius:11px; font-size:11px; font-weight:800; text-align:center; }
#     .path-node small { display:block; margin-top:3px; font-size:9px; font-weight:600; opacity:.68; }
#     .path-node.one { background:#EAF1FF; color:#2854AD; } .path-node.two { background:#F1EBFF; color:#6A43BB; } .path-node.three { background:#E9FBF7; color:#168270; } .path-node.four { background:#FFF4DF; color:#A96211; }
#     .path-link { flex:0 0 23px; height:2px; position:relative; background:linear-gradient(90deg,#9BB8EF,#C7B1F4); } .path-link:after { content:""; position:absolute; right:-1px; top:-3px; width:7px; height:7px; border-top:2px solid #A18AD9; border-right:2px solid #A18AD9; transform:rotate(45deg); }
#     .stat-card::before { content:""; position:absolute; top:0; left:0; width:48px; height:4px; border-radius:0 0 8px 0; background:#6A78E8; }
#     .mini-spark { display:flex; align-items:end; gap:3px; height:25px; margin-top:-31px; margin-left:auto; width:max-content; }
#     .mini-spark span { display:block; width:4px; border-radius:8px; background:#6B7BE9; opacity:.4; } .mini-spark span:nth-child(2),.mini-spark span:nth-child(5) { opacity:.65; } .mini-spark span:nth-child(4) { opacity:1; }
#     .control-label { display:flex; align-items:center; gap:8px; margin:3px 0 3px; color:#5F718B; font-size:11px; font-weight:800; letter-spacing:.1em; text-transform:uppercase; }
#     .control-label::before { content:""; width:22px; height:1px; background:#A9C4EE; }
#     .stat-card { border-top:3px solid transparent; background:linear-gradient(#FFF,#FFF) padding-box,linear-gradient(90deg,#4B88F5,#8B5CF6,#2DD4BF) border-box; }
#     .widget:first-child { border-top:3px solid #4E8CF6; }
#     @media(max-width:760px) { .command-deck { grid-template-columns:minmax(0,1fr) 150px; } .signal-orbit { display:block; transform:scale(.74); transform-origin:right center; } .command-copy { padding:25px; } }
#     @media(max-width:580px) { .command-deck { grid-template-columns:1fr; } .signal-orbit { display:none; } }
#     @media(max-width:760px) { .block-container { padding:20px 18px 52px; } .dashboard-title { font-size:26px; } .issue-head,.issue-row { grid-template-columns:1.15fr .9fr .9fr; } .issue-head > :nth-child(n+4),.issue-row > :nth-child(n+4) { display:none; } }
# </style>
# """,
#         unsafe_allow_html=True,
#     )

#     if st.button("← Upload another file", key="dashboard_back"):
#         for key in ("analysis_output", "project_dataframe", "project_metrics", "analyzed_filename"):
#             st.session_state.pop(key, None)
#         st.session_state["uploader_version"] = st.session_state.get("uploader_version", 0) + 1
#         for key in ("dashboard_project", "dashboard_status", "dashboard_priority"):
#             st.session_state.pop(key, None)
#         st.query_params["view"] = "upload"
#         st.rerun()

#     st.markdown('<div class="uc-nav"><div class="uc-identity"><span class="uc-mark">⌁</span>UNDER CONTROL</div><div class="uc-breadcrumb">Workspace / Project dashboard</div></div>', unsafe_allow_html=True)
#     if not analysis_output or project_df is None or len(project_df) == 0:
#         st.info("No complete dashboard is available in this session. Upload your project CSV and select Analyze Project to view its results.")
#         return

#     st.markdown('<div class="eyebrow">PROJECT OVERVIEW</div>', unsafe_allow_html=True)
#     st.markdown('<div class="dashboard-title">Your project at a glance.</div>', unsafe_allow_html=True)
#     st.caption(f"Source: {source_name or 'Uploaded project'} · {len(project_df):,} tasks analyzed")

#     state = analysis_output.get("project_state")
#     state_label = {"healthy": "Healthy", "delayed": "Delayed", "uncertain": "Not enough evidence to determine project health"}.get(state, "Project health unavailable")
#     state_detail = {
#         "healthy": "The analysis found evidence supporting a healthy project state.",
#         "delayed": "The analysis found evidence of project delay. Review the supporting findings below.",
#         "uncertain": "You can explore the available task data below. More information is needed to determine overall project health."
#     }.get(state, "Review the available data and analysis limitations below.")
#     st.markdown(
#         '<div class="command-deck"><div class="command-copy">'
#         '<div class="command-eyebrow">PROJECT HEALTH</div>'
#         f'<div class="command-title">{html.escape(state_label)}</div>'
#         f'<div class="command-text">{html.escape(state_detail)}</div>'
#         f'<div class="command-tags"><span>Confidence: {html.escape(str(analysis_output.get("confidence", "Unavailable")).title())}</span></div>'
#         '</div><div class="signal-orbit"><span class="orbit-dot one"></span><span class="orbit-dot two"></span><span class="orbit-dot three"></span><div class="orbit-core">⌁</div></div></div>',
#         unsafe_allow_html=True,
#     )
#     # Analysis limitations come only from the Analysis Agent. The dashboard does
#     # not invent analytical warnings from the uploaded CSV.
#     warnings = list(analysis_output.get("data_warnings") or [])
#     delay = analysis_output.get("estimated_delay_days")
#     if warnings:
#         st.warning("The Analysis Agent reported limitations in the available evidence.")
#         with st.expander("Analysis Agent data warnings", expanded=True):
#             for warning in dict.fromkeys(warnings):
#                 st.write("• " + str(warning))

#     st.markdown('<div class="section-name">Analysis of the full uploaded project</div>', unsafe_allow_html=True)
#     # These values are displayed exactly from the structured Analysis Agent output.
#     signals = analysis_output.get("schedule_signals") or {}
#     overview = [
#         ("Estimated delay", None if delay is None else f"{delay:g} days", "Analysis Agent"),
#         ("Blocked tasks", signals.get("blocked_tasks"), "Analysis Agent schedule signal"),
#         ("Overdue tasks", signals.get("overdue_tasks"), "Analysis Agent schedule signal"),
#         ("High-priority unfinished", signals.get("unfinished_high_priority_tasks"), "Analysis Agent schedule signal"),
#     ]
#     for column, (label, value, note) in zip(st.columns(4), overview):
#         with column:
#             metric_card(label, value, note)

#     st.markdown('<div class="section-name">Explore tasks</div>', unsafe_allow_html=True)
#     st.caption("Filters update the task cards, charts and register below. The analysis above and findings below describe the full upload.")
#     filtered = project_df.copy()
#     project_column = "project_name" if populated(filtered, "project_name").any() else "project_key"
#     for container, field, label, key in zip(
#         st.columns([1.25, 1, 1]),
#         (project_column, "status", "priority"),
#         ("Project", "Issue status", "Priority"),
#         ("dashboard_project", "dashboard_status", "dashboard_priority"),
#     ):
#         with container:
#             values = display_values(project_df, field)
#             options = sorted(values.unique().tolist()) if populated(project_df, field).any() else []
#             selected = st.selectbox(label, [None] + options, format_func=lambda value: "All" if value is None else value,
#                                     key=key, disabled=not options)
#             if selected is not None:
#                 filtered = filtered[display_values(filtered, field) == selected]

#     if len(filtered) == 0:
#         st.info("No tasks match these filters. Choose All to broaden your selection.")
#     else:
#         metrics = ProjectAnalyzer().prepare_project(filtered)["metrics"]
#         known_resolution = any(populated(filtered, c).any() for c in ("status", "resolution", "resolution_date"))
#         resolution = metrics.get("average_resolution_time_minutes")
#         points = pd.to_numeric(filtered["story_point"], errors="coerce") if "story_point" in filtered else pd.Series(dtype=float)
#         point_total = points.sum(min_count=1)
#         stats = [
#             ("Total issues", len(filtered), "Tasks matching your filters"),
#             ("Resolved work", metrics.get("resolved_issues") if known_resolution else None, "Known completion signals"),
#             ("Avg. resolution time", None if resolution is None else f"{resolution:,.0f} min", "Recorded resolution duration"),
#             ("Story points", None if pd.isna(point_total) else f"{point_total:,.1f}", "Sum of available estimates"),
#         ]
#         for column, (label, value, note) in zip(st.columns(4), stats):
#             with column:
#                 metric_card(label, value, note)
#         for container, field, title, color in zip(st.columns(2), ("status", "priority"), ("Issue status", "Priority mix"), ("#4B88F5", "#8B5CF6")):
#             with container:
#                 render_distribution(filtered, field, title, color)
#         for container, field, title, color in zip(st.columns(2), ("type", "assignee_id"), ("Issue types", "Tasks per assignee"), ("#20BDAA", "#4B88F5")):
#             with container:
#                 render_distribution(filtered, field, title, color)
#         st.markdown('<div class="section-name">Issue register</div>', unsafe_allow_html=True)
#         labels = {"issue_key": "Issue", "issue_id": "ID", "text": "Task details", "type": "Type", "priority": "Priority", "status": "Status", "assignee_id": "Assignee", "creation_date": "Created", "due_date": "Due", "resolution_date": "Resolved", "story_point": "Story points"}
#         columns = [c for c in labels if c in filtered and populated(filtered, c).any()]
#         if columns:
#             date_columns = {
#                 labels[c]: st.column_config.DatetimeColumn(labels[c], format="YYYY-MM-DD")
#                 for c in ("creation_date", "due_date", "resolution_date") if c in columns
#             }
#             st.dataframe(filtered[columns].rename(columns=labels), hide_index=True,
#                          width="stretch", column_config=date_columns)
#         else:
#             st.info("Task details cannot be displayed with the column names supplied in this file.")

#     st.markdown('<div class="section-name">Analysis findings · full upload</div>', unsafe_allow_html=True)
#     root = analysis_output.get("root_cause")
#     with st.container(border=True):
#         st.subheader("Root cause")
#         if root:
#             category = root.get("category")
#             if category:
#                 st.caption(f"Category: {category}")
#             st.write(root.get("summary") or "Not provided by the Analysis Agent.")
#             st.write(root.get("explanation") or "Not provided by the Analysis Agent.")
#             affected = root.get("affected_tasks") or []
#             st.write("Affected tasks: " + (", ".join(map(str, affected)) if affected else "Not provided by the Analysis Agent."))
#         else:
#             st.info("Not provided by the Analysis Agent.")

#     tabs = st.tabs(["Bottlenecks", "Critical tasks", "Dependencies", "Workload", "Evidence"])
#     with tabs[0]:
#         rows = analysis_output.get("bottlenecks") or []
#         if not rows:
#             st.info("Not provided by the Analysis Agent.")
#         for item in rows:
#             task_id = item.get("task_id") or "Task"
#             summary = item.get("summary") or ""
#             with st.expander(f"{task_id} · {summary}".rstrip(" ·"), expanded=True):
#                 details = []
#                 if item.get("status"):
#                     details.append(f"Status: {item['status']}")
#                 if item.get("priority"):
#                     details.append(f"Priority: {item['priority']}")
#                 if item.get("assignee"):
#                     details.append(f"Assignee: {item['assignee']}")
#                 if details:
#                     st.caption(" · ".join(details))
#                 st.write("Reason: " + (item.get("reason") or "Not provided by the Analysis Agent."))
#                 st.write("Impact: " + (item.get("impact") or "Not provided by the Analysis Agent."))
#                 affected = item.get("affected_tasks") or []
#                 st.write("Affected tasks: " + (", ".join(map(str, affected)) if affected else "Not provided by the Analysis Agent."))
#     with tabs[1]:
#         rows = analysis_output.get("critical_tasks") or []
#         if rows:
#             st.dataframe(
#                 pd.DataFrame(rows).rename(columns={"task_id": "Task", "reason": "Why it matters"}),
#                 hide_index=True,
#                 use_container_width=True,
#             )
#         else:
#             st.info("Not provided by the Analysis Agent.")
#     with tabs[2]:
#         rows = analysis_output.get("dependencies") or []
#         if rows:
#             dependency_df = pd.DataFrame(rows).rename(columns={
#                 "blocked_task": "Blocked task",
#                 "depends_on": "Depends on",
#                 "impact": "Impact",
#                 "affected_tasks": "Affected tasks",
#             })
#             st.dataframe(dependency_df, hide_index=True, use_container_width=True)
#         else:
#             st.info("Not provided by the Analysis Agent.")
#     with tabs[3]:
#         rows = analysis_output.get("workload_signals") or []
#         if not rows:
#             st.info("Not provided by the Analysis Agent.")
#         for item in rows:
#             with st.container(border=True):
#                 st.write(f"Assignee: {item.get('assignee') or 'Not provided by the Analysis Agent.'}")
#                 st.write("Issue: " + (item.get("issue") or "Not provided by the Analysis Agent."))
#                 related = item.get("related_tasks") or []
#                 st.write("Related tasks: " + (", ".join(map(str, related)) if related else "Not provided by the Analysis Agent."))
#     with tabs[4]:
#         rows = analysis_output.get("evidence") or []
#         if rows:
#             for item in rows:
#                 st.write(f"• {item}")
#         else:
#             st.info("Not provided by the Analysis Agent.")
import html
import textwrap

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
    """Presentation-only metric card. Values are passed through unchanged."""
    unavailable = value is None or (isinstance(value, float) and pd.isna(value))
    value_text = "Not available" if unavailable else str(value)
    size = "font-size:19px" if unavailable else ""
    is_zero_signal = label in {"Blocked tasks", "Overdue tasks"} and not unavailable and str(value).strip() in {"0", "0.0"}
    icons = {
        "Total issues": "◇",
        "Blocked tasks": "⊘",
        "Overdue tasks": "◷",
        "High-priority unfinished": "⚑",
    }
    variants = {
        "Total issues": "issues",
        "Blocked tasks": "blocked",
        "Overdue tasks": "overdue",
        "High-priority unfinished": "priority",
    }
    variant = variants.get(label, "default")
    if is_zero_signal:
        variant += " stat-ok"
        icons[label] = "✓"
    st.markdown(
        f'<div class="stat-card stat-{variant}"><div class="stat-icon">{icons.get(label, "✦")}</div>'
        f'<div class="stat-label">{html.escape(label)}</div>'
        f'<div class="stat-value" style="{size}">{html.escape(value_text)}</div>'
        f'<div class="stat-source">{html.escape(note)}</div></div>', unsafe_allow_html=True
    )


def render_summary_bars(frame, field, title, color):
    """Render existing dataframe counts as the compact Analysis visual."""
    if not populated(frame, field).any():
        st.info("Not enough data to display this chart.")
        return
    counts = display_values(frame, field).value_counts()
    maximum = max(int(counts.max()), 1)
    rows = "".join(
        '<div class="summary-bar-row">'
        f'<span>{html.escape(str(name))}</span>'
        f'<div class="summary-bar-track"><i style="width:{int(value) / maximum * 100:.2f}%;background:{color}"></i></div>'
        f'<b>{int(value)}</b></div>'
        for name, value in counts.items()
    )
    st.markdown(
        f'<section class="summary-bar-panel"><div class="summary-bar-title">{html.escape(title)}</div>'
        f'{rows}</section>',
        unsafe_allow_html=True,
    )


def render_register_table(frame, total_records=None):
    """Presentation-only Issue register built from the currently filtered dataframe."""
    labels = {
        "issue_key": "Issue", "issue_id": "ID", "text": "Task details",
        "priority": "Priority", "status": "Status", "assignee_id": "Assignee",
        "creation_date": "Created", "due_date": "Due", "resolution_date": "Resolved",
        "progress": "Progress",
    }
    columns = [column for column in labels if column in frame and populated(frame, column).any()]
    if not columns:
        st.markdown(
            '<section class="register-empty"><div class="register-empty-icon">⌕</div>'
            '<div class="register-empty-title">No issue details are available</div>'
            '<div class="register-empty-copy">The uploaded file does not contain fields that can be shown in the register.</div></section>',
            unsafe_allow_html=True,
        )
        return

    def _value(value):
        return "" if pd.isna(value) else str(value).strip()

    def _tone(value, kind):
        value = _value(value).casefold()
        if kind == "status":
            if any(word in value for word in ("block", "impediment")):
                return "blocked"
            if any(word in value for word in ("done", "resolved", "closed", "complete")):
                return "done"
            if any(word in value for word in ("progress", "review", "testing")):
                return "progress"
            return "open"
        if "highest" in value:
            return "highest"
        if "high" in value:
            return "high"
        if "medium" in value:
            return "medium"
        return "low"

    def _issue_icon(row):
        status = _tone(row.get("status"), "status")
        icons = {"blocked": "⊘", "done": "✓", "progress": "◌", "open": "⚑"}
        return f'<span class="register-issue-icon {status}">{icons.get(status, "◇")}</span>'

    def cell(column, row):
        value = row[column]
        value_text = _value(value)
        escaped = html.escape(value_text)
        if column in {"issue_key", "issue_id"}:
            return f'<div class="register-issue">{_issue_icon(row)}<span>{escaped}</span></div>'
        if column == "text":
            return f'<div class="register-task" title="{escaped}">{escaped}</div>'
        if column == "priority":
            return f'<span class="table-tag uc-badge {_priority_badge_class(value)}">{escaped}</span>'
        if column == "status":
            return f'<span class="table-tag uc-badge {_status_badge_class(value)}">{escaped}</span>'
        if column == "assignee_id":
            return f'<span class="register-assignee">♙<span>{escaped}</span></span>' if value_text else ""
        if column in {"creation_date", "due_date", "resolution_date"}:
            return html.escape(_format_date(value)) if value_text else ""
        if column == "progress":
            return _progress_html(value, compact=True) if value_text else '<span class="not-available">Not available</span>'
        return escaped

    total = len(frame) if total_records is None else total_records
    header = "".join(f'<th>{html.escape(labels[column])}</th>' for column in columns)
    rows = "".join(
        '<tr>' + "".join(f'<td>{cell(column, row)}</td>' for column in columns) + '</tr>'
        for _, row in frame.iterrows()
    )
    st.markdown(
        '<section class="register-card">'
        '<div class="register-card-head"><div class="register-card-title">Issue register</div>'
        f'<div class="register-card-count">{len(frame):,} visible records / {total:,} total</div></div>'
        '<div class="register-shell"><table class="register-table"><thead><tr>'
        f'{header}</tr></thead><tbody>{rows}</tbody></table></div></section>',
        unsafe_allow_html=True,
    )


def _present_value(value, default="Not available"):
    if value is None:
        return default
    if isinstance(value, float) and pd.isna(value):
        return default
    text = str(value).strip()
    return text if text and text.casefold() not in {"nan", "none", "null", "nat", "—", "-"} else default


def _task_row(frame, task_id):
    if frame is None or not task_id:
        return None
    task_key = str(task_id).strip()
    for field in ("issue_key", "issue_id"):
        if field in frame and populated(frame, field).any():
            matches = frame[frame[field].astype("string").str.strip() == task_key]
            if not matches.empty:
                return matches.iloc[0]
    return None


def _row_value(row, field, default="Not available"):
    if row is None or field not in row.index:
        return default
    return _present_value(row[field], default)


def _format_date(value):
    if value is None or (isinstance(value, float) and pd.isna(value)) or pd.isna(value):
        return "Not available"
    try:
        return pd.to_datetime(value).strftime("%d %b %Y")
    except Exception:
        return _present_value(value)


def _format_number(value):
    text = _present_value(value, "")
    if not text:
        return "Not available"
    try:
        number = float(text)
        return f"{number:g}"
    except ValueError:
        return text


def _short_task_title(value):
    text = _present_value(value, "")
    if not text:
        return "Task details"
    for separator in (" - ", " – ", ":", "|"):
        if separator in text:
            text = text.split(separator, 1)[0].strip()
            break
    words = text.split()
    if len(words) > 5:
        text = " ".join(words[:5])
    return text[:64].strip() or "Task details"


def _progress_html(value, compact=False):
    raw = _present_value(value, "")
    if not raw:
        return '<span class="not-available">Not available</span>'
    try:
        number = float(raw.replace("%", ""))
        if number <= 1 and "%" not in raw:
            number *= 100
        number = max(0.0, min(100.0, number))
        label = f"{number:.0f}%"
        klass = "progress-inline compact" if compact else "progress-inline"
        return (
            f'<div class="{klass}"><span>{label}</span>'
            f'<div class="progress-track"><i style="width:{number:.1f}%"></i></div></div>'
        )
    except ValueError:
        return f'<span class="not-available">{html.escape(raw)}</span>'


def _status_class(value):
    text = _present_value(value, "").casefold()
    if any(word in text for word in ("block", "impediment")):
        return "blocked"
    if any(word in text for word in ("done", "resolved", "closed", "complete")):
        return "done"
    if any(word in text for word in ("progress", "review", "testing")):
        return "progress"
    if any(word in text for word in ("open", "todo", "to do", "new")):
        return "open"
    return "neutral"


# Centralized frontend-only badge taxonomy. Data values remain unchanged.
PRIORITY_BADGE_CLASSES = {"highest": "priority-highest", "high": "priority-high", "medium": "priority-medium", "low": "priority-low"}
STATUS_BADGE_CLASSES = {"done": "status-done", "progress": "status-progress", "blocked": "status-blocked", "open": "status-todo", "neutral": "status-neutral"}


def _priority_badge_class(value):
    text = _present_value(value, "").casefold()
    if "highest" in text: return PRIORITY_BADGE_CLASSES["highest"]
    if "high" in text: return PRIORITY_BADGE_CLASSES["high"]
    if "medium" in text: return PRIORITY_BADGE_CLASSES["medium"]
    if "low" in text: return PRIORITY_BADGE_CLASSES["low"]
    return "priority-neutral"


def _status_badge_class(value):
    return STATUS_BADGE_CLASSES.get(_status_class(value), STATUS_BADGE_CLASSES["neutral"])


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


def render_dashboard_ui(analysis_output=None, simulation_output=None, project_df=None, project_metrics=None, source_name=None, active_stage="analysis") -> None:
    """Display uploaded task data, Analysis Agent output, and Simulation Agent output."""
    st.markdown(
        """
<style>
    :root {
        --uc-bg: #F6F7FC;
        --uc-paper: #FFFFFF;
        --uc-ink: #17213B;
        --uc-muted: #8792AA;
        --uc-line: #E6EAF4;
        --uc-blue: #6678E8;
        --uc-purple: #7A67DF;
        --uc-soft-blue: #EEF2FF;
    }

    html, body, [class*="css"] { font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    .stApp {
        color: var(--uc-ink);
        background:
            linear-gradient(118deg, rgba(94,130,235,.085) 0%, rgba(94,130,235,0) 24%),
            linear-gradient(302deg, rgba(157,122,224,.085) 0%, rgba(157,122,224,0) 25%),
            radial-gradient(ellipse at 50% 18%, rgba(255,255,255,.98) 0%, rgba(255,255,255,.74) 34%, rgba(255,255,255,0) 68%),
            linear-gradient(180deg,#F8F9FD 0%,#F5F7FC 55%,#F7F8FC 100%);
        background-attachment: fixed;
        background-repeat: no-repeat;
    }

    .stApp::before, .stApp::after {
        content:"";
        position: fixed;
        z-index: 0;
        pointer-events: none;
        filter: blur(22px);
        opacity: .42;
    }

    .stApp::before {
        width: 280px;
        height: 520px;
        left: -150px;
        top: 18%;
        border-radius: 46% 54% 60% 40% / 42% 46% 54% 58%;
        background: linear-gradient(180deg, rgba(98,145,239,.16), rgba(127,177,246,.05));
    }

    .stApp::after {
        width: 340px;
        height: 560px;
        right: -180px;
        top: 8%;
        border-radius: 58% 42% 45% 55% / 44% 58% 42% 56%;
        background: linear-gradient(180deg, rgba(151,120,222,.14), rgba(113,153,240,.04));
    }

    .stApp > div { position: relative; z-index: 1; }
    .stApp h1,.stApp h2,.stApp h3 { color: var(--uc-ink); }
    header { visibility: hidden; }
    footer { visibility: hidden; }
    .block-container { max-width: 1120px; padding: 22px 34px 64px; }

    /* ----- top product / stage header ----- */
    .uc-stage-shell { margin: 0 0 12px; }
    .uc-stage-brand {
        margin-bottom: 12px;
        color: #5268D9;
        font-size: 26px;
        font-weight: 800;
        letter-spacing: .20em;
        text-align: center;
        text-transform: uppercase;
    }
    .uc-stage-nav {
        display: grid;
        grid-template-columns: 44px minmax(0,1fr) 44px;
        align-items: center;
        gap: 18px;
        max-width: 820px;
        margin: 0 auto;
    }
    .uc-stage-arrow {
        display: grid;
        place-items: center;
        width: 36px;
        height: 36px;
        color: #6175E4;
        font-size: 22px;
        font-weight: 500;
        user-select: none;
    }
    .uc-stage-arrow.right { justify-self: end; }
    .uc-stage-track { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); position:relative; }
    .uc-stage-track::before {
        content:"";
        position:absolute;
        top:7px;
        left:16.5%;
        right:16.5%;
        height:1px;
        background:#D9DFED;
    }
    .uc-stage-step { position:relative; z-index:1; display:flex; flex-direction:column; align-items:center; gap:8px; color:#9AA4B9; font-size:11px; font-weight:650; }
    .uc-stage-dot { width:10px; height:10px; border-radius:50%; background:#D8DFEC; box-shadow:0 0 0 5px var(--uc-bg); }
    .uc-stage-step.active { color:#596FD9; }
    .uc-stage-step.active .uc-stage-dot { background:#667CE9; }
    .uc-stage-label { padding:4px 12px; border-radius:999px; }
    .uc-stage-step.active .uc-stage-label { background:#FFF; border:1px solid #DDE3F2; box-shadow:0 4px 12px rgba(58,75,139,.08); }

    /* ----- Analysis navigation ----- */
    div[data-testid="stRadio"] {
        position:sticky;
        top:18px;
        margin:18px 0 0;
        padding:0 18px 0 0;
        border:0;
        border-right:1px solid #E2E5EE;
        border-radius:0;
        background:transparent;
        box-shadow:none;
    }

    div[data-testid="stRadio"] [role="radiogroup"] {
        display:flex;
        flex-direction:column;
        gap:8px;
    }

    div[data-testid="stRadio"] label {
        position:relative;
        align-items:center;
        justify-content:flex-start;
        min-height:42px;
        margin:0 !important;
        padding:0 12px 0 16px !important;
        border:1px solid transparent !important;
        border-radius:12px !important;
        color:#657188;
        background:transparent !important;
        font-size:12px;
        font-weight:720;
        letter-spacing:.01em;
        transition:color .16s ease, transform .16s ease, background .16s ease, border-color .16s ease;
    }

    div[data-testid="stRadio"] label > div:first-child { display:none !important; }

    div[data-testid="stRadio"] label:hover {
        color:#7168E6;
        background:#F7F5FF !important;
        transform:translateX(2px);
    }

    div[data-testid="stRadio"] label:has(input:checked) {
        color:#5C51CA;
        background:#F1EEFF !important;
        border-color:#DDD6FE !important;
        box-shadow:0 8px 18px rgba(88,73,181,.08) !important;
        font-weight:820;
        transform:none;
    }

    div[data-testid="stRadio"] label:has(input:checked)::after {
        content:"";
        position:absolute;
        z-index:4;
        left:0;
        top:9px;
        bottom:9px;
        width:3px;
        height:auto;
        border-radius:99px;
        background:#7168E6;
    }

    /* Remove only the native radio control beside the five analysis tabs. */
    div[data-testid="stRadio"] label[data-testid="stRadioOption"] > div > div > div:first-child {
        display:none !important;
    }

    div[data-testid="stRadio"] label[data-testid="stRadioOption"] > div > div {
        gap:0 !important;
    }

    div[data-testid="stRadio"] label p {
        color:inherit !important;
        font-family:Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
        font-size:13px !important;
        font-weight:inherit !important;
        letter-spacing:.01em !important;
        display:flex !important;
        align-items:center !important;
        min-height:42px !important;
        margin:0 !important;
        line-height:1.2 !important;
    }

    div[data-testid="stRadio"] label[data-selected="true"] p {
        color:#7168E6 !important;
        font-weight:800 !important;
    }
    /* ----- shared project heading ----- */
    .page-head { display:flex; align-items:flex-start; justify-content:space-between; gap:18px; margin:18px 0 14px; }
    .dashboard-title { margin:0 0 4px; color:#18223C; font-size:28px; line-height:1.05; font-weight:790; letter-spacing:-.045em; }
    .dashboard-subtitle { color:#8A96AC; font-size:11px; }
    .preview-label { display:flex; align-items:center; gap:9px; flex:0 1 auto; min-width:0; max-width:min(350px,42vw); margin-top:1px; padding:7px 9px; border:1px solid #E2E7F2; border-radius:11px; background:linear-gradient(135deg,#FFF,#FAFBFF); box-shadow:0 5px 14px rgba(45,63,105,.035); }
    .preview-file-icon { display:grid; place-items:center; flex:0 0 auto; width:24px; height:24px; border:1px solid #DCE5FA; border-radius:7px; color:#5F76DD; background:#F0F4FF; font-size:13px; font-weight:800; }
    .preview-file-copy { display:flex; min-width:0; flex:1; flex-direction:column; gap:1px; }
    .preview-file-kicker { color:#98A5BA; font-size:7px; font-weight:800; letter-spacing:.08em; line-height:1.1; text-transform:uppercase; }
    .preview-file-name { overflow:hidden; color:#53637D; font-size:9px; font-weight:750; line-height:1.25; text-overflow:ellipsis; white-space:nowrap; }
    .preview-section { flex:0 0 auto; padding:4px 6px; border-radius:6px; color:#6B70CF; background:#F1F0FF; font-size:8px; font-weight:750; }
    .eyebrow { display:none; }
    .section-name { margin:22px 0 12px; color:#1B2742; font-size:18px; font-weight:780; letter-spacing:-.03em; }

    /* ----- compact project health hero ----- */
    .command-deck {
        position:relative;
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap:18px;
        min-height:108px;
        margin:0 0 17px;
        padding:0 22px;
        overflow:hidden;
        border-radius:18px;
        background:linear-gradient(108deg,#33416F 0%,#3F4A7D 55%,#544D8F 100%);
        box-shadow:0 14px 28px rgba(49,58,108,.14);
    }
    .command-deck::after { content:""; position:absolute; right:-28px; top:-64px; width:220px; height:220px; border:1px solid rgba(255,255,255,.07); border-radius:50%; box-shadow:0 0 0 34px rgba(255,255,255,.025); }
    .command-copy { position:relative; z-index:1; min-width:0; }
    .command-eyebrow { color:#B8C2EA; font-size:9px; font-weight:800; letter-spacing:.17em; }
    .command-title-row { display:flex; align-items:center; gap:9px; margin-top:8px; }
    .command-title { color:#FFF; font-size:23px; font-weight:790; letter-spacing:-.035em; }
    .command-tags { display:flex; gap:6px; }
    .command-tags span { padding:4px 7px; border:1px solid rgba(255,255,255,.16); border-radius:999px; background:rgba(255,255,255,.08); color:#D9E0F5; font-size:8px; font-weight:700; }
    .command-action { position:relative; z-index:1; flex:0 0 auto; padding:9px 12px; border:1px solid rgba(255,255,255,.19); border-radius:10px; color:#DDE3F8; background:rgba(255,255,255,.04); font-size:9px; font-weight:700; }

    /* ----- metric cards ----- */
    .stat-card { position:relative; min-height:126px; display:flex; flex-direction:column; box-sizing:border-box; margin-bottom:8px; padding:15px 16px 13px; overflow:hidden; border:1px solid #E6EAF3; border-radius:14px; background:#FFF; box-shadow:0 8px 18px rgba(37,50,93,.035); }
    .stat-card::after { content:""; position:absolute; right:-34px; top:-38px; width:110px; height:110px; border-radius:50%; opacity:.75; }
    .stat-card::before { content:""; position:absolute; left:0; right:0; bottom:0; height:3px; }
    .stat-icon { display:grid; place-items:center; width:30px; height:30px; margin-bottom:9px; border-radius:10px; font-size:15px; font-weight:700; }
    .stat-label { color:#68758D; font-size:10px; font-weight:740; }
    .stat-value { margin-top:5px; color:#19243E; font-size:27px; line-height:29px; font-weight:790; letter-spacing:-.045em; }
    .stat-source { margin-top:auto; color:#7F8DA4; font-size:9px; }
    .stat-issues .stat-icon { color:#6B80E7; background:#EFF3FF; border:1px solid #DCE4FF; }
    .stat-issues::after { background:#F0F3FF; } .stat-issues::before { background:#7489EB; }
    .stat-blocked .stat-icon { color:#D67E8D; background:#FFF0F2; border:1px solid #F8DDE2; }
    .stat-blocked::after { background:#FFF0F3; } .stat-blocked::before { background:#E9A0AA; }
    .stat-overdue .stat-icon { color:#D8A850; background:#FFF8E9; border:1px solid #F7E9C8; }
    .stat-overdue::after { background:#FFF7E7; } .stat-overdue::before { background:#E9C46F; }
    .stat-priority .stat-icon { color:#906FDD; background:#F6F0FF; border:1px solid #E9DEFA; }
    .stat-priority::after { background:#F5EEFF; } .stat-priority::before { background:#9D82E4; }
    .stat-card.stat-ok .stat-icon { color:#1F8D77; background:#EAF8F4; border-color:#CBEDE5; }
    .stat-card.stat-ok::after { background:#EFFAF7; }
    .stat-card.stat-ok::before { background:#54C3AF; }

    /* ----- dashboard lower panels ----- */
    .glance-list,.donut-panel,.summary-bar-panel,.register-shell,.task-intelligence,.impact-panel,.focus-card,.team-card {
        border:1px solid #E3E8F2;
        background:#FFF;
        box-shadow:0 8px 20px rgba(36,49,91,.03);
    }
    .glance-list { margin:8px 0; overflow:hidden; border-radius:15px; }
    .dashboard-status-grid { display:grid; grid-template-columns:minmax(0,1.35fr) minmax(280px,.82fr); gap:14px; align-items:stretch; margin:8px 0; }
    .dashboard-status-grid .glance-list,.dashboard-status-grid .donut-panel { height:auto; min-height:0; margin:0; }
    .glance-list-head { display:flex; justify-content:space-between; align-items:center; padding:14px 16px 10px; color:#1D2843; font-size:13px; font-weight:770; }
    .glance-list-head span { padding:5px 8px; border-radius:7px; color:#7384DF; background:#F3F5FF; font-size:8px; font-weight:750; }

    /* Healthy empty state: dashboard attention panel */
    .dashboard-all-clear { min-height:328px; display:flex; flex-direction:column; }
    .dashboard-all-clear-body { display:grid; flex:1; place-items:center; padding:18px 20px 25px; text-align:center; }
    .dashboard-clear-mark { position:relative; display:grid; place-items:center; width:76px; height:76px; margin:0 auto 13px; border-radius:50%; background:radial-gradient(circle at 35% 25%,#FBFFFD,#E5F8F0); box-shadow:inset 0 0 0 1px rgba(111,200,160,.08); }
    .dashboard-clear-mark::before,.dashboard-clear-mark::after { content:""; position:absolute; top:50%; width:13px; height:3px; border-radius:99px; background:#78CEAB; }
    .dashboard-clear-mark::before { left:-18px; box-shadow:0 -10px 0 -1px #B9E9D7,0 10px 0 -1px #B9E9D7; }
    .dashboard-clear-mark::after { right:-18px; box-shadow:0 -10px 0 -1px #B9E9D7,0 10px 0 -1px #B9E9D7; }
    .dashboard-clear-mark svg { position:relative; z-index:1; width:45px; height:45px; filter:drop-shadow(0 4px 7px rgba(54,166,121,.14)); }
    .dashboard-clear-title { color:#1F2B45; font-size:17px; font-weight:790; letter-spacing:-.035em; }
    .dashboard-clear-copy { max-width:280px; margin:7px auto 0; color:#8794A8; font-size:10px; line-height:1.55; }
    .glance-columns,.glance-row { display:grid; grid-template-columns:minmax(0,1.55fr) .62fr .72fr .9fr; gap:8px; align-items:center; }
    .glance-columns { padding:8px 16px; color:#77859B; background:#F8F9FD; font-size:8px; font-weight:760; }
    .glance-row { padding:9px 16px; border-top:1px solid #EEF1F7; }
    .glance-id { color:#5C70D8; font-size:10px; font-weight:790; }
    .glance-copy { margin-top:4px; overflow:hidden; color:#8A95A9; font-size:8px; line-height:1.35; text-overflow:ellipsis; white-space:nowrap; }
    .glance-chip { display:inline-flex; width:max-content; max-width:100%; padding:4px 7px; border-radius:999px; color:#677287; background:#F3F4F8; font-size:7px; font-weight:740; white-space:normal; }
    .glance-chip.blocked { color:#B95F70; background:#FFF0F2; }
    .glance-chip.done { color:#25866F; background:#EAF8F4; }
    .glance-chip.progress { color:#5C61B8; background:#F0EEFF; }
    .glance-chip.open { color:#3A6EB3; background:#EEF5FF; }
    .glance-chip.neutral { color:#66738A; background:#F3F4F8; }
    .glance-progress { min-width:0; }
    .not-available { color:#7F8BA0; font-size:8px; font-weight:700; }
    .progress-inline { display:grid; grid-template-columns:auto minmax(45px,1fr); gap:7px; align-items:center; color:#5E6F8B; font-size:8px; font-weight:740; }
    .progress-inline.compact { grid-template-columns:auto minmax(38px,1fr); }
    .progress-track { height:5px; overflow:hidden; border-radius:99px; background:#ECEFF6; }
    .progress-track i { display:block; height:100%; border-radius:99px; background:linear-gradient(90deg,#667CE9,#2DD4BF); }

    .donut-panel { box-sizing:border-box; margin:8px 0; padding:16px 17px; border-radius:15px; background:linear-gradient(145deg,#FFF,#FCFAFF); }
    .donut-head { display:flex; justify-content:space-between; color:#1D2843; font-size:13px; font-weight:770; }
    .donut-head span { color:#9AA4B7; font-size:8px; font-weight:650; }
    .donut-content { display:grid; flex:1; place-content:center; gap:10px; padding:8px 0 2px; }
    .donut { position:relative; display:grid; place-items:center; width:142px; height:142px; margin:0 auto; border-radius:50%; }
    .donut::after { content:""; width:104px; height:104px; border-radius:50%; background:#FFF; box-shadow:inset 0 0 0 1px #EEF1F6; }
    .donut-center { position:absolute; z-index:1; color:#27344E; font-size:20px; font-weight:820; letter-spacing:-.04em; text-align:center; }
    .donut-center small { display:block; margin-top:4px; color:#929CAE; font-size:8px; font-weight:650; letter-spacing:0; }
    .donut-legend { display:grid; grid-template-columns:1fr 1fr; gap:7px 14px; min-width:230px; }
    .donut-legend div { display:flex; justify-content:space-between; gap:8px; color:#8792A6; font-size:8px; }
    .donut-legend b { color:#49566E; }

    .dashboard-bottom { display:grid; grid-template-columns:1.05fr .95fr; gap:14px; margin-top:10px; }
    .focus-card,.team-card { box-sizing:border-box; border-radius:15px; padding:15px 17px; }
    .focus-card { position:relative; overflow:hidden; background:linear-gradient(115deg,#FFF,#FBFAFF); }
    .focus-card::after { content:""; position:absolute; right:-32px; top:-45px; width:130px; height:130px; border-radius:50%; background:#F2EEFF; opacity:.75; }
    .focus-content { position:relative; z-index:1; }
    .focus-label,.team-label { color:#677CE2; font-size:9px; font-weight:800; letter-spacing:.05em; }
    .focus-title { margin-top:13px; color:#27344E; font-size:12px; line-height:1.45; font-weight:720; }
    .focus-copy { margin-top:8px; color:#8A95AA; font-size:9px; line-height:1.5; }
    .focus-tasks { display:flex; flex-wrap:wrap; gap:5px; margin-top:10px; }
    .focus-tasks span { padding:4px 6px; border-radius:999px; color:#775CB9; background:#F3EEFF; font-size:7px; font-weight:700; }
    .team-card { background:linear-gradient(145deg,#FFF,#FAFBFF); }
    .team-signals { margin-top:11px; }
    .team-signal { padding:11px 0; border-top:1px solid #EDF0F6; }
    .team-signal:first-child { padding-top:0; border-top:0; }
    .team-person { color:#25324D; font-size:16px; font-weight:790; letter-spacing:-.03em; }
    .team-copy { margin-top:6px; color:#8793A9; font-size:9px; line-height:1.5; overflow-wrap:anywhere; }

    /* ----- attention page ----- */
    .attention-card-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; margin:4px 0 12px; }
    .attention-visual-card { position:relative; min-height:146px; box-sizing:border-box; overflow:hidden; padding:18px 62px 15px 20px; border:1px solid #E2E8F3; border-left:4px solid #6C79E8; border-radius:16px; background:#FFF; box-shadow:0 8px 22px rgba(36,49,91,.045); }
    .attention-visual-card.selected { border-color:#7064ED; border-left-color:#6554ED; background:linear-gradient(118deg,#FFF 0%,#F7F5FF 100%); box-shadow:0 10px 26px rgba(84,75,186,.11), inset 0 0 0 1px rgba(112,100,237,.12); }
    .attention-visual-card.is-blocked { border-left-color:#F06A70; }
    .attention-visual-card.is-overdue { border-left-color:#F0AF3F; }
    .attention-visual-card.is-focus { border-left-color:#8867E8; }
    .attention-card-top { display:flex; align-items:center; gap:12px; min-width:0; }
    .attention-card-icon { display:grid; flex:0 0 auto; place-items:center; width:42px; height:42px; border-radius:13px; color:#6175DF; background:#EEF2FF; font-size:23px; font-weight:800; }
    .attention-visual-card.is-blocked .attention-card-icon { color:#E4525B; background:#FFF0F1; }
    .attention-visual-card.is-overdue .attention-card-icon { color:#E79B25; background:#FFF7E7; }
    .attention-visual-card.is-focus .attention-card-icon { color:#7D5CDF; background:#F4F0FF; }
    .attention-card-main { min-width:0; }
    .attention-id { color:#5067D8; font-size:13px; font-weight:820; letter-spacing:-.015em; }
    .attention-summary { display:-webkit-box; overflow:hidden; margin-top:4px; color:#77859B; font-size:10px; font-weight:560; line-height:1.42; -webkit-box-orient:vertical; -webkit-line-clamp:2; }
    .attention-card-bottom { display:flex; align-items:center; flex-wrap:wrap; gap:7px; margin-top:14px; }
    .attention-card-pill { padding:5px 9px; border-radius:999px; color:#5D69C6; background:#F0F1FF; font-size:8px; font-weight:780; line-height:1; white-space:nowrap; }
    .attention-card-pill.status-blocked { color:#CF515B; background:#FFF0F2; }
    .attention-card-pill.status-overdue { color:#C98520; background:#FFF6E5; }
    .attention-card-pill.status-focus { color:#7658CB; background:#F3EEFF; }
    .attention-card-meta { display:flex; align-items:center; flex-wrap:wrap; gap:10px; margin-top:11px; color:#7C899F; font-size:9px; font-weight:600; }
    .attention-card-meta span { display:inline-flex; align-items:center; gap:4px; }
    .attention-card-progress { display:flex; align-items:center; gap:7px; min-width:116px; margin-left:auto; color:#273755; font-size:9px; font-weight:780; }
    .attention-card-progress .progress-track { width:76px; height:7px; }
    .st-key-attention_task_picker [data-testid="stHorizontalBlock"] { gap:14px !important; }
    .st-key-attention_task_picker [data-testid="stColumn"] { min-width:0 !important; }
    /* The native button is the full card hit area; the visual card sits above it without intercepting clicks. */
    .st-key-attention_task_picker [class*="st-key-attention_card_"] [data-testid="stElementContainer"],
    .st-key-attention_task_picker [class*="st-key-attention_card_"] [data-testid="stButton"] { width:100% !important; height:146px; }
    .st-key-attention_task_picker [class*="st-key-attention_card_"] [data-testid="stButton"] button { display:block; width:100% !important; height:146px; min-height:146px; padding:0; border:0; border-radius:16px; opacity:0; cursor:pointer; }
    .st-key-attention_task_picker [class*="st-key-attention_card_"] [data-testid="stButton"] button:focus-visible { opacity:1; border:2px solid #6F63EB; background:transparent; }
    .st-key-attention_task_picker [class*="st-key-attention_card_"] [data-testid="stButton"] button p { color:transparent; font-size:0; }
    .st-key-attention_task_picker [class*="st-key-attention_card_"] > [data-testid="stElementContainer"] + [data-testid="stElementContainer"] { position:relative; z-index:2; margin-top:-162px !important; pointer-events:none !important; }
    .st-key-attention_task_picker [class*="st-key-attention_card_"] [data-testid="stMarkdown"],
    .st-key-attention_task_picker [class*="st-key-attention_card_"] [data-testid="stMarkdownContainer"],
    .st-key-attention_task_picker [class*="st-key-attention_card_"] .attention-visual-card { pointer-events:none !important; }
    .st-key-attention_task_picker [class*="st-key-attention_card_"] .attention-visual-card { margin-top:0; }
    /* Healthy empty state: analysis attention page */
    .attention-healthy-state { position:relative; overflow:hidden; min-height:420px; margin:2px 0 8px; border:1px solid #E3E9F5; border-radius:20px; background:radial-gradient(circle at 50% 5%,rgba(116,148,237,.13),transparent 28%),linear-gradient(160deg,#FFFFFF 0%,#F8FBFF 100%); box-shadow:0 12px 30px rgba(49,70,122,.045); }
    .attention-healthy-state::before,.attention-healthy-state::after { content:""; position:absolute; width:250px; height:250px; border-radius:50%; background:radial-gradient(circle,rgba(137,170,244,.10),rgba(137,170,244,0) 68%); pointer-events:none; }
    .attention-healthy-state::before { top:-145px; left:-90px; }
    .attention-healthy-state::after { right:-110px; bottom:-155px; }
    .attention-healthy-content { position:relative; z-index:1; display:flex; min-height:420px; flex-direction:column; align-items:center; justify-content:center; padding:32px 28px; text-align:center; }
    .attention-healthy-scene { position:relative; width:300px; height:170px; margin-bottom:12px; }
    .healthy-path { position:absolute; top:89px; left:8px; width:285px; height:74px; border-top:1px dashed #B7CAFB; border-radius:50% 50% 0 0; transform:rotate(-7deg); }
    .healthy-paper { position:absolute; width:83px; height:112px; border:1px solid #DCE7FB; border-radius:14px; background:linear-gradient(145deg,#FFFFFF,#EEF5FF); box-shadow:0 12px 22px rgba(83,116,189,.09); }
    .healthy-paper::after { content:""; position:absolute; top:48px; left:19px; width:43px; height:6px; border-radius:99px; background:#C6D6F5; box-shadow:0 15px 0 #D8E4F9,0 30px 0 #E4EDFC; }
    .healthy-paper.left { top:28px; left:34px; opacity:.66; transform:rotate(-12deg); }
    .healthy-paper.right { top:31px; right:30px; opacity:.62; transform:rotate(12deg); }
    .healthy-paper.main { top:5px; left:109px; width:96px; height:132px; transform:rotate(-5deg); }
    .healthy-paper.main::before { content:"✓"; position:absolute; top:18px; left:30px; display:grid; place-items:center; width:36px; height:36px; border-radius:50%; color:#FFFFFF; background:#83A6F2; font-size:22px; font-weight:800; box-shadow:0 0 0 9px #E7EFFE; }
    .healthy-paper.main::after { top:76px; left:25px; width:47px; }
    .healthy-glass { position:absolute; top:86px; left:184px; width:52px; height:52px; border:7px solid #5D88E8; border-radius:50%; background:rgba(235,243,255,.55); box-shadow:0 5px 11px rgba(69,111,203,.15); }
    .healthy-glass::after { content:""; position:absolute; right:-30px; bottom:-22px; width:37px; height:8px; border-radius:99px; background:#5D88E8; transform:rotate(47deg); transform-origin:left center; }
    .healthy-spark { position:absolute; color:#7EA2EF; font-size:25px; font-weight:800; line-height:1; }
    .healthy-spark.one { top:25px; left:114px; }
    .healthy-spark.two { top:75px; right:5px; font-size:19px; }
    .attention-healthy-title { color:#18233E; font-size:23px; font-weight:800; letter-spacing:-.045em; }
    .attention-healthy-copy { max-width:570px; margin:10px auto 0; color:#8390A6; font-size:12px; line-height:1.6; }

    .task-intelligence { position:relative; overflow:hidden; margin:16px 0 8px; padding:23px 24px; border-radius:18px; background:linear-gradient(120deg,#FFF 0%,#FCFBFF 72%,#F5F2FF 100%); }
    .task-intelligence::after { content:""; position:absolute; width:230px; height:230px; right:-105px; top:-145px; border-radius:50%; background:rgba(125,105,232,.07); pointer-events:none; }
    .task-intelligence-head { position:relative; z-index:1; display:flex; justify-content:space-between; align-items:flex-start; gap:16px; }
    .task-intelligence-kicker { color:#7181A3; font-size:9px; font-weight:820; letter-spacing:.15em; text-transform:uppercase; }
    .task-intelligence-title { max-width:820px; margin:10px 0 3px; color:#17233E; font-size:22px; line-height:1.2; font-weight:800; letter-spacing:-.045em; }
    .task-intelligence-status { display:inline-flex; flex:0 0 auto; align-items:center; padding:8px 12px; border-radius:10px; color:#5E66B8; background:#F0EEFF; font-size:10px; font-weight:800; }
    .task-intelligence-status.blocked { color:#D4555D; background:#FFF0F2; }
    .task-intelligence-status.done { color:#237D69; background:#EAF8F4; }
    .task-intelligence-status.progress { color:#5D61B6; background:#F0EEFF; }
    .task-intelligence-status.open { color:#3569AD; background:#EEF5FF; }
    .task-intelligence-tags { position:relative; z-index:1; display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:9px; margin:18px 0 16px; }
    .attention-tag { min-height:56px; box-sizing:border-box; padding:10px 12px; border-radius:11px; color:#53627A; background:#F3F5FA; font-size:10px; font-weight:780; }
    .attention-tag small { display:block; margin-bottom:5px; color:#8995A9; font-size:7px; font-weight:820; letter-spacing:.08em; text-transform:uppercase; }
    .attention-tag.blocked { color:#A84F62; background:#FFF0F3; }
    .attention-tag.done { color:#237D69; background:#EAF8F4; }
    .attention-tag.progress { color:#5D61B6; background:#F0EEFF; }
    .attention-tag.open { color:#3569AD; background:#EEF5FF; }
    .attention-tag.priority { color:#725FB4; background:#F2EFFF; }
    .attention-tag.impact { color:#176F66; background:#E8FAF5; }
    .attention-tag.date { color:#5D6D89; background:#F3F6FB; }
    .attention-tag.points { color:#375FAE; background:#EEF5FF; }
    .task-intelligence-copy { position:relative; z-index:1; color:#707E95; font-size:11px; line-height:1.65; }
    .task-intelligence-impact { position:relative; z-index:1; margin-top:17px; padding-top:15px; border-top:1px solid #E8ECF3; color:#727F95; font-size:10px; line-height:1.55; }
    details.task-intelligence-impact summary { cursor:pointer; color:#5D6FD7; font-size:9px; font-weight:800; letter-spacing:.04em; text-transform:uppercase; }
    details.task-intelligence-impact[open] summary { margin-bottom:8px; }

    /* ----- impact page ----- */
    .impact-layout { display:grid; grid-template-columns:1fr; align-items:start; gap:18px; margin:3px 0 20px; }
    .impact-panel { position:relative; overflow:hidden; padding:25px 27px; border:1px solid #E1E7F2; border-radius:21px; background:linear-gradient(145deg,#FFF 0%,#FBFCFF 100%); box-shadow:0 14px 31px rgba(41,57,106,.05); }
    .impact-panel:not(.accent)::after { content:""; position:absolute; width:190px; height:190px; top:-118px; right:-93px; border-radius:50%; background:rgba(112,126,229,.06); pointer-events:none; }
    .impact-panel.accent { min-height:224px; box-sizing:border-box; color:#FFF; border-color:transparent; background:linear-gradient(135deg,#26345C 0%,#3E4D88 55%,#6954A4 100%); box-shadow:0 16px 34px rgba(50,59,111,.18); }
    .impact-panel.accent::after { content:""; position:absolute; width:230px; height:230px; right:-122px; bottom:-130px; border:1px solid rgba(255,255,255,.12); border-radius:50%; box-shadow:0 0 0 38px rgba(255,255,255,.035); pointer-events:none; }
    .impact-kicker { position:relative; z-index:1; margin-bottom:7px; color:#7484A5; font-size:9px; font-weight:820; letter-spacing:.15em; text-transform:uppercase; }
    .impact-panel.accent .impact-kicker { color:#C8D1F0; }
    .impact-heading { position:relative; z-index:1; margin-bottom:20px; color:#1A2742; font-size:22px; line-height:1.15; font-weight:800; letter-spacing:-.045em; }
    .impact-panel.accent .impact-heading { color:#FFF; }
    .dependency-item { position:relative; z-index:1; display:grid; grid-template-columns:minmax(250px,390px) minmax(0,1fr); gap:15px; align-items:center; padding:16px 0; border-top:1px solid #EEF1F7; }
    .dependency-item:first-of-type { padding-top:0; border-top:0; }
    .dependency-route { display:flex; align-items:center; flex-wrap:wrap; gap:9px; min-width:0; }
    .dependency-node { display:inline-flex; min-height:31px; box-sizing:border-box; align-items:center; padding:0 11px; border:1px solid #E4E9F8; border-radius:9px; color:#22355C; background:#F7F8FD; font-size:11px; font-weight:820; line-height:1; white-space:nowrap; }
    .dependency-node.source { color:#566BD2; border-color:#E7E9FC; background:#F0F2FF; }
    .dependency-arrow { display:grid; place-items:center; width:20px; height:20px; color:#6E7FC0; font-size:18px; font-weight:800; }
    .dependency-status { display:inline-flex; min-height:27px; align-items:center; padding:0 10px; border-radius:999px; color:#C75761; background:#FFF0F2; font-size:8px; font-weight:820; white-space:nowrap; }
    .dependency-copy { min-width:0; color:#738098; font-size:10px; line-height:1.5; }
    .workload-item { position:relative; z-index:1; display:grid; grid-template-columns:135px minmax(0,1fr); column-gap:18px; align-items:start; padding:15px 0; border-top:1px solid rgba(255,255,255,.14); }
    .workload-item:first-of-type { padding-top:0; border-top:0; }
    .workload-person { display:inline-flex; width:max-content; align-items:center; gap:6px; padding:7px 11px; border:1px solid rgba(255,255,255,.23); border-radius:999px; color:#FFF; background:rgba(255,255,255,.08); font-size:10px; font-weight:780; }
    .workload-person::before { content:"◌"; color:#C7D3FF; font-size:13px; line-height:0; }
    .workload-issue { margin:0; color:#F5F7FF; font-size:12px; font-weight:670; line-height:1.5; }
    .workload-tasks { grid-column:2; margin-top:6px; color:#C5CEEC; font-size:9px; line-height:1.45; }
    .impact-empty-state { position:relative; overflow:hidden; display:flex; min-height:440px; box-sizing:border-box; align-items:center; justify-content:center; margin:3px 0 20px; padding:46px 30px; border:1px solid #E0E7F3; border-radius:23px; background:radial-gradient(circle at 50% 27%,rgba(125,149,241,.12),transparent 29%),linear-gradient(145deg,#FFFFFF 0%,#F9FBFF 100%); box-shadow:0 14px 31px rgba(41,57,106,.05); text-align:center; }
    .impact-empty-state::before,.impact-empty-state::after { content:""; position:absolute; border-radius:50%; pointer-events:none; }
    .impact-empty-state::before { width:330px; height:170px; top:68px; left:calc(50% - 165px); background:radial-gradient(ellipse,rgba(123,146,240,.14),rgba(123,146,240,0) 70%); }
    .impact-empty-state::after { width:180px; height:180px; right:-74px; bottom:-86px; background:radial-gradient(circle,rgba(155,127,238,.10),rgba(155,127,238,0) 70%); }
    .impact-empty-content { position:relative; z-index:1; display:flex; max-width:640px; flex-direction:column; align-items:center; }
    .impact-empty-scene { position:relative; width:330px; height:205px; margin-bottom:13px; }
    .impact-empty-cloud { position:absolute; border-radius:50%; background:radial-gradient(circle at 36% 28%,rgba(255,255,255,.98),rgba(225,234,255,.66) 53%,rgba(225,234,255,0) 72%); }
    .impact-empty-cloud.one { width:260px; height:150px; left:35px; top:25px; }
    .impact-empty-cloud.two { width:145px; height:104px; right:-12px; top:64px; opacity:.7; }
    .impact-empty-path { position:absolute; width:160px; height:92px; border:2px dashed #B9CBFB; border-right:0; border-bottom:0; border-radius:88px 0 0 0; opacity:.88; }
    .impact-empty-path.one { top:25px; left:14px; transform:rotate(14deg); }
    .impact-empty-path.two { right:12px; top:79px; transform:scaleX(-1) rotate(16deg); }
    .impact-empty-folder { position:absolute; z-index:2; left:calc(50% - 64px); top:74px; width:128px; height:84px; border:1px solid #D6E2FD; border-radius:14px 14px 18px 18px; background:linear-gradient(145deg,#FDFEFF,#DCE8FF); box-shadow:0 16px 26px rgba(77,110,201,.16); transform:rotate(-4deg); }
    .impact-empty-folder::before { content:""; position:absolute; left:11px; top:-13px; width:52px; height:22px; border:1px solid #D6E2FD; border-bottom:0; border-radius:10px 12px 0 0; background:#EAF1FF; }
    .impact-empty-bars { position:absolute; display:flex; align-items:end; justify-content:center; gap:5px; inset:0; padding-top:30px; }
    .impact-empty-bars i { display:block; width:11px; border-radius:8px 8px 3px 3px; background:linear-gradient(#7C98F5,#5879E2); box-shadow:0 3px 7px rgba(80,109,214,.18); }
    .impact-empty-bars i:nth-child(1) { height:25px; } .impact-empty-bars i:nth-child(2) { height:43px; } .impact-empty-bars i:nth-child(3) { height:34px; }
    .impact-empty-node { position:absolute; z-index:3; display:grid; width:39px; height:39px; place-items:center; border:3px solid #FFF; border-radius:50%; color:#6684E9; background:linear-gradient(145deg,#E7EEFF,#C6D7FF); box-shadow:0 6px 14px rgba(66,95,182,.15); font-size:15px; font-weight:850; }
    .impact-empty-node.one { top:25px; left:53px; } .impact-empty-node.two { top:40px; right:47px; color:#8466DD; background:linear-gradient(145deg,#F0EAFF,#D9CEFF); } .impact-empty-node.three { top:118px; left:10px; width:31px; height:31px; font-size:12px; } .impact-empty-node.four { top:125px; right:7px; width:31px; height:31px; color:#8466DD; background:linear-gradient(145deg,#F0EAFF,#D9CEFF); font-size:12px; }
    .impact-empty-check { position:absolute; z-index:4; top:57px; left:calc(50% + 37px); display:grid; width:34px; height:34px; place-items:center; border:3px solid #FFF; border-radius:50%; color:#FFF; background:linear-gradient(145deg,#8A78ED,#536FE0); box-shadow:0 7px 14px rgba(85,100,205,.20); font-size:18px; font-weight:850; }
    .impact-empty-title { color:#172440; font-size:25px; line-height:1.2; font-weight:820; letter-spacing:-.045em; }
    .impact-empty-copy { max-width:510px; margin-top:9px; color:#8190A8; font-size:12px; line-height:1.6; }

    /* ----- analytics page ----- */
    .analytics-head { display:flex; align-items:flex-end; justify-content:space-between; gap:18px; margin:2px 0 14px; padding:2px 1px; }
    .analytics-title { color:#182541; font-size:23px; font-weight:820; letter-spacing:-.048em; }
    .analytics-summary { display:flex; align-items:baseline; gap:4px; padding:9px 13px; border:1px solid #E4E9F4; border-radius:10px; color:#7E8AA1; background:rgba(255,255,255,.76); font-size:10px; font-weight:650; box-shadow:0 4px 12px rgba(51,66,112,.025); }
    .analytics-summary b { color:#5669D5; font-size:19px; font-weight:820; letter-spacing:-.04em; }
    .summary-bar-panel { position:relative; min-height:252px; box-sizing:border-box; overflow:hidden; margin:8px 0; padding:21px 22px 18px; border:1px solid #E2E8F3; border-radius:19px; background:linear-gradient(145deg,#FFF 0%,#FBFCFF 100%); box-shadow:0 12px 27px rgba(40,56,102,.045); }
    .summary-bar-panel::after { content:""; position:absolute; width:145px; height:145px; top:-102px; right:-68px; border-radius:50%; background:rgba(113,128,229,.065); pointer-events:none; }
    .summary-bar-title { position:relative; z-index:1; display:flex; align-items:center; gap:8px; margin-bottom:19px; color:#23304A; font-size:13px; font-weight:800; letter-spacing:-.02em; }
    .summary-bar-title::before { content:""; display:block; width:7px; height:7px; border-radius:50%; background:#7282E4; box-shadow:0 0 0 5px #F0F3FF; }
    .summary-bar-row { position:relative; z-index:1; display:grid; grid-template-columns:112px minmax(80px,1fr) 30px; gap:11px; align-items:center; margin:14px 0; }
    .summary-bar-row span { overflow:hidden; color:#5C6A85; font-size:10px; font-weight:700; text-overflow:ellipsis; white-space:nowrap; }
    .summary-bar-row b { color:#33415C; font-size:10px; font-weight:800; text-align:right; }
    .summary-bar-track { height:9px; overflow:hidden; border-radius:99px; background:#EDF0F7; box-shadow:inset 0 1px 1px rgba(68,82,128,.035); }
    .summary-bar-track i { display:block; height:100%; min-width:4px; border-radius:99px; box-shadow:0 2px 5px rgba(84,104,211,.16); }

    /* ----- issue register ----- */
    .st-key-issue_register_filters { margin:3px 0 16px; padding:13px 16px 6px; border:1px solid #E2E8F3; border-radius:16px; background:rgba(255,255,255,.94); box-shadow:0 9px 22px rgba(46,62,112,.035); }
    .st-key-issue_register_filters [data-testid="stHorizontalBlock"] { gap:12px !important; }
    .st-key-issue_register_filters div[data-testid="stSelectbox"] label { margin-bottom:5px; color:#73809A; font-size:9px; font-weight:760; }
    .st-key-issue_register_filters div[data-testid="stSelectbox"] > div > div { min-height:40px; border-color:#E0E7F3; border-radius:10px; background:#FFF; box-shadow:0 1px 2px rgba(48,63,108,.02); }
    .st-key-issue_register_filters div[data-testid="stSelectbox"] input,.st-key-issue_register_filters div[data-testid="stSelectbox"] span { color:#52617B !important; -webkit-text-fill-color:#52617B; font-size:10px; font-weight:650; }
    .register-card { overflow:hidden; margin:2px 0 8px; border:1px solid #E0E7F2; border-radius:18px; background:#FFF; box-shadow:0 11px 27px rgba(40,56,102,.045); }
    .register-card-head { display:flex; align-items:center; justify-content:space-between; gap:14px; padding:16px 18px; border-bottom:1px solid #EDF0F6; }
    .register-card-title { display:flex; align-items:center; gap:8px; color:#1E2A45; font-size:14px; font-weight:800; letter-spacing:-.02em; }
    .register-card-title span { display:grid; place-items:center; width:27px; height:27px; border-radius:8px; color:#5E6CE1; background:#EEF1FF; font-size:14px; }
    .register-card-count { padding:7px 10px; border-radius:9px; color:#76839B; background:#F7F8FC; font-size:9px; font-weight:700; white-space:nowrap; }
    .register-shell { max-height:520px; overflow:auto; margin:0; }
    .register-table { width:100%; min-width:960px; border-collapse:separate; border-spacing:0; color:#62708A; font-size:9px; }
    .register-table th { position:sticky; top:0; z-index:2; padding:12px 14px; color:#74819A; background:#F5F7FC; border-bottom:1px solid #E7EBF4; font-size:8px; font-weight:800; letter-spacing:.01em; text-align:left; white-space:nowrap; }
    .register-table td { max-width:295px; padding:13px 14px; border-bottom:1px solid #EEF1F6; line-height:1.45; vertical-align:middle; white-space:nowrap; }
    .register-table tbody tr:last-child td { border-bottom:0; }
    .register-table tr:hover td { background:#FAFBFF; }
    .register-table td:nth-child(2) { min-width:260px; white-space:normal; }
    .register-issue { display:flex; align-items:center; gap:8px; color:#5068DC; font-size:10px; font-weight:820; }
    .register-issue-icon { display:grid; place-items:center; width:28px; height:28px; border-radius:9px; color:#687CE5; background:#EEF2FF; font-size:15px; font-weight:800; }
    .register-issue-icon.blocked { color:#DE5962; background:#FFF0F1; }
    .register-issue-icon.done { color:#318F79; background:#EAF8F3; }
    .register-issue-icon.progress { color:#6782DA; background:#EEF4FF; }
    .register-issue-icon.open { color:#7A61D5; background:#F3EFFF; }
    .register-task { display:-webkit-box; overflow:hidden; max-width:270px; color:#34415B; font-size:9px; font-weight:680; line-height:1.45; text-overflow:ellipsis; -webkit-box-orient:vertical; -webkit-line-clamp:2; }
    .table-tag { display:inline-flex; align-items:center; min-height:24px; padding:0 9px; border-radius:999px; font-size:8px; font-weight:800; white-space:nowrap; }
    .table-tag.priority { color:#6573CE; background:#EFF2FF; }
    .table-tag.priority.highest { color:#7355C7; background:#F1ECFF; }
    .table-tag.priority.high { color:#416DCC; background:#EAF2FF; }
    .table-tag.priority.medium { color:#B17B29; background:#FFF5DF; }
    .table-tag.priority.low { color:#667791; background:#F0F3F8; }
    .table-tag.status { color:#51667D; background:#F1F3F8; }
    .table-tag.status.done { color:#2B8A75; background:#E7F8F2; }
    .table-tag.status.blocked { color:#CD5660; background:#FFF0F2; }
    .table-tag.status.progress { color:#5F62C5; background:#F0EEFF; }
    .table-tag.status.open { color:#62718C; background:#F2F4F8; }
    .register-assignee { display:inline-flex; align-items:center; gap:6px; color:#596982; font-size:9px; font-weight:680; }
    .register-assignee::first-letter { color:#6174DB; }
    .register-table .progress-inline.compact { min-width:106px; gap:6px; }
    .register-table .progress-inline.compact .progress-track { width:72px; }
    .register-empty { margin:2px 0 8px; padding:58px 24px; border:1px solid #E1E8F3; border-radius:18px; background:#FFF; text-align:center; box-shadow:0 10px 25px rgba(40,56,102,.04); }
    .register-empty-icon { display:grid; place-items:center; width:46px; height:46px; margin:0 auto 12px; border-radius:14px; color:#6B7BDE; background:#EEF2FF; font-size:26px; }
    .register-empty-title { color:#202C46; font-size:15px; font-weight:800; }
    .register-empty-copy { max-width:370px; margin:7px auto 0; color:#8794AA; font-size:10px; line-height:1.5; }

    /* ----- project note memo board ----- */
    .memo-board {
        margin:16px 0 0;
        overflow:hidden;
        border:1px solid #E4E8F2;
        border-radius:18px;
        background:#FFF;
        box-shadow:0 10px 28px rgba(40,55,96,.055);
    }
    .memo-board-head {
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap:12px;
        padding:15px 18px;
        border-bottom:1px solid #EDF0F6;
    }
    .memo-board-title { display:flex; align-items:center; gap:9px; color:#1F2B45; font-size:13px; font-weight:780; letter-spacing:-.02em; }
    .memo-board-icon { display:grid; place-items:center; width:25px; height:25px; border:1px solid #E1E7F2; border-radius:8px; color:#6477D9; background:#F5F7FF; font-size:14px; }
    .memo-board-more { color:#9AA6BA; font-size:17px; font-weight:760; letter-spacing:.16em; line-height:1; }
    .memo-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px; padding:16px 18px 18px; }
    .memo-card {
        position:relative;
        display:flex;
        min-height:174px;
        box-sizing:border-box;
        flex-direction:column;
        overflow:hidden;
        padding:16px;
        border:1px solid rgba(223,229,240,.9);
        border-radius:14px;
        box-shadow:0 5px 15px rgba(48,62,103,.035);
    }
    .memo-card::after { content:""; position:absolute; right:0; bottom:0; left:0; height:3px; }
    .memo-card.mint { background:linear-gradient(145deg,#FCFFFD,#F4FCF7); }
    .memo-card.blue { background:linear-gradient(145deg,#FEFFFF,#F4F8FF); }
    .memo-card.rose { background:linear-gradient(145deg,#FFFEFE,#FFF6F7); }
    .memo-card.lilac { background:linear-gradient(145deg,#FFFEFF,#F8F5FF); }
    .memo-card.mint::after { background:#73C69C; }
    .memo-card.blue::after { background:#718CE4; }
    .memo-card.rose::after { background:#E58A96; }
    .memo-card.lilac::after { background:#A98AE2; }
    .memo-card-top { display:flex; align-items:center; justify-content:space-between; gap:10px; }
    .memo-status { width:9px; height:9px; border-radius:50%; background:currentColor; box-shadow:0 0 0 5px currentColor; opacity:.8; }
    .memo-card.mint .memo-status { color:#72BA92; }
    .memo-card.blue .memo-status { color:#7691E4; }
    .memo-card.rose .memo-status { color:#DE8C98; }
    .memo-card.lilac .memo-status { color:#A58ADC; }
    .memo-card-more { color:#A2ADBD; font-size:14px; font-weight:800; line-height:1; letter-spacing:.12em; }
    .memo-heading { margin:17px 0 8px; color:#25314B; font-size:13px; font-weight:780; line-height:1.35; letter-spacing:-.015em; }
    .memo-copy { color:#718099; font-size:10px; line-height:1.65; overflow-wrap:anywhere; }

    /* existing data notices */
    .data-note { margin:12px 0; padding:12px 14px; border:1px solid #E4E8F2; border-radius:12px; color:#6E7D95; background:#FFF; font-size:9px; line-height:1.5; }

    @media(max-width:860px) {
        .block-container { padding:24px 18px 55px; }
        .uc-stage-brand { font-size:21px; }
        .uc-stage-nav { grid-template-columns:30px minmax(0,1fr) 30px; gap:8px; }
        div[data-testid="stRadio"] { position:static; margin:0; padding:0 16px 0 0; }
        div[data-testid="stRadio"] [role="radiogroup"] { gap:7px; }
        .page-head { margin-top:22px; }
        .dashboard-title { font-size:24px; }
        .dashboard-bottom,.attention-card-grid,.impact-layout,.dashboard-status-grid { grid-template-columns:1fr; }
        .glance-list.attention-populated,.donut-panel.paired-with-attention { height:auto; min-height:0; }
        .impact-empty-state { min-height:390px; }
        .glance-columns,.glance-row { grid-template-columns:minmax(0,1.7fr) .75fr .8fr; }
        .glance-columns > :last-child,.glance-row > :last-child { display:none; }
    }
    @media(max-width:620px) {
        .uc-stage-arrow { display:none; }
        .uc-stage-nav { grid-template-columns:1fr; }
        .command-action { display:none; }
        .page-head { flex-direction:column; }
        .preview-label { margin-top:0; }
        .stat-card { min-height:118px; }
        .dependency-item { grid-template-columns:1fr; gap:8px; }
        .dependency-copy { grid-column:1; }
        .dependency-route { grid-column:1; grid-row:1; }
        .impact-empty-state { min-height:350px; padding:32px 18px; }
        .impact-empty-scene { transform:scale(.83); margin-bottom:-2px; }
        .impact-empty-title { font-size:22px; }
    }

    /* ----- shared readability scale ----- */
    .stApp, .stApp * { font-family:Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    .uc-stage-brand { font-size:28px; }
    .uc-stage-step { font-size:13px; }
    div[data-testid="stRadio"] label p { font-size:15px !important; }
    .dashboard-title { font-size:32px; }
    .dashboard-subtitle { font-size:13px; line-height:1.5; }
    .preview-file-kicker { font-size:8px; } .preview-file-name { font-size:10px; } .preview-section { font-size:9px; }
    .command-eyebrow,.focus-label,.team-label,.impact-kicker { font-size:10px; }
    .command-tags span,.command-action { font-size:10px; }
    .stat-label,.summary-bar-row span,.summary-bar-row b { font-size:12px; }
    .stat-source,.dashboard-clear-copy,.glance-id,.donut-head span,.team-copy,.focus-copy,.dependency-copy { font-size:11px; }
    .glance-columns,.glance-copy,.glance-chip,.not-available,.progress-inline,.donut-legend div { font-size:10px; }
    .glance-list-head,.donut-head,.summary-bar-title,.register-card-title { font-size:15px; }
    .attention-summary { font-size:11px; line-height:1.5; }
    .attention-card-pill,.attention-card-meta,.attention-card-progress { font-size:10px; }
    .attention-tag { font-size:11px; } .attention-tag small { font-size:8px; }
    .task-intelligence-kicker { font-size:10px; } .task-intelligence-copy,.task-intelligence-impact { font-size:12px; }
    .impact-heading { font-size:24px; } .workload-issue { font-size:13px; } .workload-person,.workload-tasks { font-size:11px; }
    .memo-heading { font-size:14px; } .memo-copy { font-size:11px; }

    /* ----- shared card titles ----- */
    .glance-list-head,
    .donut-head,
    .summary-bar-title,
    .register-card-title,
    .memo-board-title,
    .focus-label,
    .team-label,
    .impact-heading,
    .analytics-title,
    .uc-flow-title,
    .uc-notes-title {
        color:#1F2B45 !important;
        font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif !important;
        font-size:16px !important;
        font-weight:780 !important;
        letter-spacing:-.025em !important;
        line-height:1.25 !important;
        text-transform:none !important;
    }
    .register-card-title span,
    .memo-board-icon,
    .uc-flow-icon,
    .uc-notes-illustration { display:none !important; }

    /* Shared colors for every live priority/status badge. */
    .uc-badge { --uc-badge-bg:#F1F3F7; --uc-badge-text:#647084; --uc-badge-border:#E4E8EF; background:var(--uc-badge-bg) !important; color:var(--uc-badge-text) !important; border-color:var(--uc-badge-border) !important; }
    .uc-badge.priority-highest { --uc-badge-bg:#F7E9FA; --uc-badge-text:#8A3E88; --uc-badge-border:#EFD5EC; }
    .uc-badge.priority-high { --uc-badge-bg:#EDF0F4; --uc-badge-text:#465463; --uc-badge-border:#DDE3E9; }
    .uc-badge.priority-medium { --uc-badge-bg:#F4F1EE; --uc-badge-text:#74675F; --uc-badge-border:#E9E1DB; }
    .uc-badge.priority-low { --uc-badge-bg:#EEF0F7; --uc-badge-text:#5F6688; --uc-badge-border:#DEE1EC; }
    .table-tag.uc-badge.priority-highest,.glance-chip.uc-badge.priority-highest,.attention-card-pill.uc-badge.priority-highest,.attention-tag.uc-badge.priority-highest,.uc-task-id.uc-badge.priority-highest { background:#F7E9FA !important; color:#8A3E88 !important; border-color:#EFD5EC !important; }
    .table-tag.uc-badge.priority-high,.glance-chip.uc-badge.priority-high,.attention-card-pill.uc-badge.priority-high,.attention-tag.uc-badge.priority-high,.uc-task-id.uc-badge.priority-high { background:#EDF0F4 !important; color:#465463 !important; border-color:#DDE3E9 !important; }
    .table-tag.uc-badge.priority-medium,.glance-chip.uc-badge.priority-medium,.attention-card-pill.uc-badge.priority-medium,.attention-tag.uc-badge.priority-medium,.uc-task-id.uc-badge.priority-medium { background:#F4F1EE !important; color:#74675F !important; border-color:#E9E1DB !important; }
    .table-tag.uc-badge.priority-low,.glance-chip.uc-badge.priority-low,.attention-card-pill.uc-badge.priority-low,.attention-tag.uc-badge.priority-low,.uc-task-id.uc-badge.priority-low { background:#EEF0F7 !important; color:#5F6688 !important; border-color:#DEE1EC !important; }

    .uc-badge.priority-neutral,.uc-badge.status-neutral { --uc-badge-bg:#F1F3F7; --uc-badge-text:#647084; --uc-badge-border:#E4E8EF; }
    .uc-badge.status-done { --uc-badge-bg:#EAF8F3; --uc-badge-text:#287D69; --uc-badge-border:#D3EEE5; }
    .uc-badge.status-progress { --uc-badge-bg:#F0EEFF; --uc-badge-text:#5E5BBC; --uc-badge-border:#E1DDFB; }
    .uc-badge.status-blocked { --uc-badge-bg:#FFF0F2; --uc-badge-text:#BD5862; --uc-badge-border:#F7DCE0; }
    .uc-badge.status-todo { --uc-badge-bg:#EEF5FF; --uc-badge-text:#3E70B5; --uc-badge-border:#D9E8FB; }
    .glance-chip.uc-badge,.attention-card-pill.uc-badge,.table-tag.uc-badge,.task-intelligence-status.uc-badge,.dependency-status.uc-badge { background:var(--uc-badge-bg) !important; color:var(--uc-badge-text) !important; border-color:var(--uc-badge-border) !important; }
    .attention-tag.uc-badge { background:var(--uc-badge-bg) !important; color:var(--uc-badge-text) !important; }
</style>
""",
        unsafe_allow_html=True,
    )

    if not analysis_output or project_df is None or len(project_df) == 0:
        st.info("No complete dashboard is available in this session. Upload your project CSV and select Analyze Project to view its results.")
        return

    if active_stage == "analysis":
        # All information below comes from the existing Analysis Agent output or
        # the standardized project dataframe. This section changes presentation only.
        attention = {}
        for item in analysis_output.get("bottlenecks") or []:
            task_id = item.get("task_id")
            if task_id:
                attention[task_id] = {
                    "Task": task_id, "Summary": item.get("summary"),
                    "Why it matters": item.get("reason"), "Impact": item.get("impact"),
                    "Status": item.get("status"), "Priority": item.get("priority"),
                    "Progress": item.get("progress"),
                }
        for item in analysis_output.get("critical_tasks") or []:
            task_id = item.get("task_id")
            if task_id and task_id not in attention:
                attention[task_id] = {
                    "Task": task_id, "Summary": item.get("reason"),
                    "Why it matters": None, "Impact": None, "Status": None, "Priority": None,
                }

        nav_col, content_col = st.columns([0.17, 0.83], gap="large")

        with nav_col:
            selected_section = st.radio(
                "Analysis sections",
                ["Dashboard", "Attention", "Impact map", "Analytics", "Issue register"],
                key="analysis_section_nav",
                label_visibility="collapsed",
            )

        with content_col:
            # Shared heading used by each section in the right content column.
            project_badge = None
            for badge_field in ("project_name", "project_key"):
                if populated(project_df, badge_field).any():
                    project_badge = str(display_values(project_df, badge_field).iloc[0])
                    break
            if not project_badge:
                project_badge = "Project"
            uploaded_label = str(source_name or project_badge)
    
            section_titles = {
                "Dashboard": ("Project dashboard", "Project overview", "Overview"),
                "Attention": ("Tasks needing attention", "Review the analysis focus items", "Attention"),
                "Impact map": ("Project impact", "Dependencies and workload signals", "Impact"),
                "Analytics": ("Project analytics", "Distributions from the uploaded project data", "Analytics"),
                "Issue register": ("Issue register", "Filtered task records from the uploaded project data", "Register"),
            }
    
            def _analysis_heading():
                title, subtitle, badge = section_titles.get(selected_section, section_titles["Dashboard"])
                st.markdown(
                    '<div class="page-head"><div>'
                    f'<div class="dashboard-title">{html.escape(title)}</div>'
                    f'<div class="dashboard-subtitle">{len(project_df):,} tasks analyzed · {html.escape(subtitle)}</div>'
                    '</div>'
                    '<div class="preview-label">'
                    '<span class="preview-file-icon" aria-hidden="true">▤</span>'
                    '<span class="preview-file-copy"><span class="preview-file-kicker">Uploaded project</span>'
                    f'<span class="preview-file-name" title="{html.escape(uploaded_label)}">{html.escape(uploaded_label)}</span></span>'
                    f'<span class="preview-section">{html.escape(badge)}</span></div></div>',
                    unsafe_allow_html=True,
                )
    
            state = analysis_output.get("project_state")
            state_label = str(state).replace("_", " ").title() if state else ""
            confidence = analysis_output.get("confidence")
            signals = analysis_output.get("schedule_signals") or {}
            root = analysis_output.get("root_cause") or {}
    
            if selected_section == "Dashboard":
                _analysis_heading()
                st.markdown(
                    '<div class="command-deck"><div class="command-copy">'
                    '<div class="command-eyebrow">PROJECT HEALTH</div>'
                    '<div class="command-title-row">'
                    f'<div class="command-title">{html.escape(state_label)}</div>'
                    + '</div></div>'
                    + (f'<div class="command-action">{html.escape(str(confidence).title())} confidence</div>' if confidence else '')
                    + '</div>',
                    unsafe_allow_html=True,
                )
                overview = [
                    ("Total issues", len(project_df), "Tasks analyzed"),
                    ("Blocked tasks", signals.get("blocked_tasks"), "No current blockers" if str(signals.get("blocked_tasks")).strip() in {"0", "0.0"} else "Dependencies unresolved"),
                    ("Overdue tasks", signals.get("overdue_tasks"), "No overdue tasks" if str(signals.get("overdue_tasks")).strip() in {"0", "0.0"} else "Past their due date"),
                    ("High-priority unfinished", signals.get("unfinished_high_priority_tasks"), "Requires focus"),
                ]
                for column, (label, value, note) in zip(st.columns(4), overview):
                    with column:
                        metric_card(label, value, note)
    
                agent_notes = [str(note).strip() for note in (analysis_output.get("notes") or []) if note is not None and str(note).strip()]
    
                status_counts = display_values(project_df, "status").value_counts() if populated(project_df, "status").any() else pd.Series(dtype="int64")
                total_tasks = len(project_df)
                done_count = sum(int(value) for name, value in status_counts.items() if str(name).strip().casefold() in {"done", "resolved", "closed"})
                resolved_percent = (done_count / total_tasks * 100) if total_tasks else 0
                palette = ["#66C1B5", "#6680E8", "#A692E9", "#DC909E", "#E7BC6C"]
                position = 0.0
                segments = []
                for (_, count), color in zip(status_counts.items(), palette):
                    next_position = position + (int(count) / total_tasks * 100 if total_tasks else 0)
                    segments.append(f"{color} {position:.2f}% {next_position:.2f}%")
                    position = next_position
                donut_background = f"conic-gradient({', '.join(segments)})" if segments else "#EDF0F4"
    
                attention_rows = ""
                for item in list(attention.values())[:5]:
                    row = _task_row(project_df, item.get("Task"))
                    status_text = _present_value(item.get("Status"), _row_value(row, "status"))
                    priority_text = _present_value(item.get("Priority"), _row_value(row, "priority"))
                    status_class = " " + _status_badge_class(status_text)
                    priority_class = _priority_badge_class(priority_text)
                    summary_text = item.get("Summary") or item.get("Why it matters") or ""
                    attention_rows += (
                        '<div class="glance-row">'
                        '<div><div class="glance-id">' + html.escape(str(item["Task"])) + '</div>'
                        + (f'<div class="glance-copy">{html.escape(str(summary_text))}</div>' if summary_text else '') + '</div>'
                        f'<div><span class="glance-chip uc-badge {priority_class}">{html.escape(priority_text)}</span></div>'
                        f'<div><span class="glance-chip uc-badge{status_class}">{html.escape(status_text)}</span></div>'
                        f'<div class="glance-progress">{_progress_html(item.get("Progress"), compact=True)}</div>'
                        '</div>'
                    )
    
                legend = "".join(
                    f'<div><span>{html.escape(str(name))}</span><b>{int(count)}</b></div>'
                    for name, count in list(status_counts.items())[:6]
                )
                if attention_rows:
                    attention_panel_html = (
                        '<section class="glance-list attention-populated"><div class="glance-list-head">Tasks needing attention'
                        '<span>View details ↗</span></div>'
                        '<div class="glance-columns"><span>Task</span><span>Priority</span><span>Status</span><span>Progress</span></div>'
                        + attention_rows + '</section>'
                    )
                else:
                    attention_panel_html = (
                        '<section class="glance-list dashboard-all-clear">'
                        '<div class="glance-list-head">Tasks needing attention</div>'
                        '<div class="dashboard-all-clear-body"><div>'
                        '<div class="dashboard-clear-mark" aria-hidden="true">'
                        '<svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">'
                        '<path d="M24 4.5 39 10v11.1c0 9.5-6.1 17.8-15 21.4-8.9-3.6-15-11.9-15-21.4V10l15-5.5Z" fill="#F6FFFA" stroke="#47B986" stroke-width="2.4"/>'
                        '<path d="m16.7 23.8 4.8 4.8 10.3-10.4" stroke="#35A976" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>'
                        '</svg></div>'
                        '<div class="dashboard-clear-title">All clear</div>'
                        '<div class="dashboard-clear-copy">No overdue or high-priority unfinished tasks were detected.</div>'
                        '</div></div></section>'
                    )
                status_panel_html = ""
                if len(status_counts):
                    status_panel_html = (
                        f'<section class="donut-panel"><div class="donut-head">Issue status'
                        f'<span>{total_tasks} tasks</span></div>'
                        f'<div class="donut-content"><div class="donut" style="background:{donut_background}"><div class="donut-center">{resolved_percent:.1f}%<small>Resolved work</small></div></div>'
                        f'<div class="donut-legend">{legend}</div></div></section>'
                    )
                st.markdown(
                    f'<div class="dashboard-status-grid">{attention_panel_html}{status_panel_html}</div>',
                    unsafe_allow_html=True,
                )
    
                root_summary = root.get("summary") if root else None
                root_explanation = root.get("explanation") if root else None
                affected_html = "".join(
                    f"<span>{html.escape(str(task))}</span>" for task in ((root.get("affected_tasks") or [])[:8] if root else [])
                )
                workload = list(analysis_output.get("workload_signals") or [])
                focus_html = (
                    '<div class="focus-card"><div class="focus-content"><div class="focus-label">Primary focus</div>'
                    + (f'<div class="focus-title">{html.escape(str(root_summary))}</div>' if root_summary else '<div class="focus-title">No primary focus was identified in this analysis.</div>')
                    + (f'<div class="focus-copy">{html.escape(str(root_explanation))}</div>' if root_explanation else '')
                    + (f'<div class="focus-tasks">{affected_html}</div>' if affected_html else '')
                    + '</div></div>'
                )
                if workload:
                    team_signals = []
                    for signal in workload:
                        assignee = signal.get("assignee") or "Workload to watch"
                        issue = signal.get("issue")
                        related = ", ".join(map(str, signal.get("related_tasks") or []))
                        team_signals.append(
                            '<div class="team-signal">'
                            f'<div class="team-person">{html.escape(str(assignee))}</div>'
                            + (f'<div class="team-copy">{html.escape(str(issue))}</div>' if issue else '')
                            + (f'<div class="team-copy">Related · {html.escape(related)}</div>' if related else '')
                            + '</div>'
                        )
                    team_html = ('<div class="team-card"><div class="team-label">TEAM SIGNAL</div>'
                                 f'<div class="team-signals">{"".join(team_signals)}</div></div>')
                else:
                    team_html = '<div class="team-card"><div class="team-label">TEAM SIGNAL</div><div class="team-person">No workload signal</div><div class="team-copy">No workload signal was identified in this analysis.</div></div>'
                st.markdown(f'<div class="dashboard-bottom">{focus_html}{team_html}</div>', unsafe_allow_html=True)
    
                if agent_notes:
                    memo_styles = ("mint", "blue", "rose", "lilac")

                    def _memo_heading(note):
                        """Derive a display heading only; the original note remains unchanged below it."""
                        compact = " ".join(str(note).split())
                        for separator in (". ", ": ", "; "):
                            if separator in compact:
                                candidate = compact.split(separator, 1)[0].strip()
                                if candidate:
                                    return candidate[:72].rstrip()
                        return compact[:72].rstrip() or "Project note"

                    memo_cards = []
                    for index, note in enumerate(dict.fromkeys(agent_notes)):
                        style = memo_styles[index % len(memo_styles)]
                        original_note = str(note)
                        memo_cards.append(
                            f'<article class="memo-card {style}">'
                            '<div class="memo-card-top"><span class="memo-status" aria-hidden="true"></span></div>'
                            f'<div class="memo-heading">{html.escape(_memo_heading(original_note))}</div>'
                            f'<div class="memo-copy">{html.escape(original_note)}</div>'
                            '</article>'
                        )
                    st.markdown(
                        '<section class="memo-board"><div class="memo-board-head">'
                        '<div class="memo-board-title">Project note</div>'
                        '</div>'
                        f'<div class="memo-grid">{"".join(memo_cards)}</div></section>',
                        unsafe_allow_html=True,
                    )
    
            elif selected_section == "Attention":
                _analysis_heading()
                if not attention:
                    st.markdown(
                        '<section class="attention-healthy-state"><div class="attention-healthy-content">'
                        '<div class="attention-healthy-scene" aria-hidden="true">'
                        '<div class="healthy-path"></div><div class="healthy-paper left"></div>'
                        '<div class="healthy-paper main"></div><div class="healthy-paper right"></div>'
                        '<div class="healthy-glass"></div><span class="healthy-spark one">✦</span><span class="healthy-spark two">✦</span>'
                        '</div><div class="attention-healthy-title">No tasks need attention right now</div>'
                        '<div class="attention-healthy-copy">Great news! The analysis didn’t find any tasks that require attention. Everything looks on track at the moment.</div>'
                        '</div></section>',
                        unsafe_allow_html=True,
                    )
                else:
                    visible_attention = list(attention.values())[:5]
                    task_ids = [str(item.get("Task")) for item in visible_attention]
                    default_item = next(
                        (item for item in visible_attention if str(item.get("Status") or "").strip().casefold() == "blocked"),
                        visible_attention[0],
                    )
                    selection_key = "attention_selected_task"
                    if st.session_state.get(selection_key) not in task_ids:
                        st.session_state[selection_key] = str(default_item.get("Task"))

                    def _attention_value(value):
                        if value is None:
                            return ""
                        value = str(value).strip()
                        return "" if value.casefold() in {"", "none", "nan", "not available"} else value

                    with st.container(key="attention_task_picker"):
                        for start_index in range(0, len(visible_attention), 2):
                            columns = st.columns(2)
                            for card_index, (column, item) in enumerate(
                                zip(columns, visible_attention[start_index:start_index + 2]), start=start_index
                            ):
                                task_id = str(item.get("Task"))
                                task_row = _task_row(project_df, item.get("Task"))
                                summary = _attention_value(item.get("Summary") or item.get("Why it matters"))
                                card_status = _attention_value(item.get("Status") or _row_value(task_row, "status"))
                                card_priority = _attention_value(item.get("Priority") or _row_value(task_row, "priority"))
                                card_assignee = _attention_value(_row_value(task_row, "assignee_id"))
                                due_raw = _row_value(task_row, "due_date")
                                card_due = _format_date(due_raw) if _attention_value(due_raw) else ""
                                card_progress = _attention_value(item.get("Progress"))
                                card_state_text = f"{card_status} {card_priority}".casefold()
                                if "blocked" in card_state_text:
                                    card_state, card_icon, status_class = "is-blocked", "⊘", "status-blocked"
                                elif "overdue" in card_state_text:
                                    card_state, card_icon, status_class = "is-overdue", "◷", "status-overdue"
                                elif "high" in card_state_text:
                                    card_state, card_icon, status_class = "is-focus", "⚑", "status-focus"
                                else:
                                    card_state, card_icon, status_class = "", "◌", ""
                                card_pills = "".join(
                                    f'<span class="attention-card-pill uc-badge {css_class}">{html.escape(value)}</span>'
                                    for value, css_class in ((card_priority, _priority_badge_class(card_priority)), (card_status, _status_badge_class(card_status)))
                                    if value
                                )
                                card_meta = "".join(
                                    f'<span>{symbol} {html.escape(value)}</span>'
                                    for symbol, value in (("◌", card_assignee), ("□", card_due))
                                    if value
                                )
                                card_progress_html = (
                                    f'<div class="attention-card-progress">{_progress_html(card_progress, compact=True)}</div>'
                                    if card_progress else ""
                                )
                                with column:
                                    with st.container(key=f"attention_card_{card_index}"):
                                        if st.button(f"Select {task_id}", key=f"attention_task_{task_id}", type="secondary"):
                                            st.session_state[selection_key] = task_id
                                            st.rerun()
                                        is_selected = st.session_state[selection_key] == task_id
                                        st.markdown(
                                            f'<article class="attention-visual-card {card_state} {"selected" if is_selected else ""}">'
                                            f'<div class="attention-card-top"><div class="attention-card-icon">{card_icon}</div>'
                                            f'<div class="attention-card-main"><div class="attention-id">{html.escape(task_id)}</div>'
                                            f'<div class="attention-summary">{html.escape(summary)}</div></div></div>'
                                            f'<div class="attention-card-bottom">{card_pills}</div>'
                                            f'<div class="attention-card-meta">{card_meta}{card_progress_html}</div>'
                                            '</article>',
                                            unsafe_allow_html=True,
                                        )

                    selected = next(
                        item for item in visible_attention
                        if str(item.get("Task")) == st.session_state[selection_key]
                    )
                    selected_row = _task_row(project_df, selected.get("Task"))
                    selected_status = _present_value(selected.get("Status"), _row_value(selected_row, "status"))
                    selected_priority = _present_value(selected.get("Priority"), _row_value(selected_row, "priority"))
                    selected_points = _format_number(_row_value(selected_row, "story_point", ""))
                    selected_due = _format_date(selected_row["due_date"]) if selected_row is not None and "due_date" in selected_row.index else "Not available"
                    selected_impact = _present_value(selected.get("Impact"))
                    selected_progress = _progress_html(selected.get("Progress"))
                    selected_tags = "".join([
                        f'<span class="attention-tag uc-badge {_status_badge_class(selected_status)}"><small>Status</small>{html.escape(selected_status)}</span>',
                        f'<span class="attention-tag points"><small>Story points</small>{html.escape(selected_points)}</span>',
                        f'<span class="attention-tag impact"><small>Customer impact</small>{html.escape(selected_impact)}</span>',
                        f'<span class="attention-tag uc-badge {_priority_badge_class(selected_priority)}"><small>Priority</small>{html.escape(selected_priority)}</span>',
                        f'<span class="attention-tag progress"><small>Progress</small>{selected_progress}</span>',
                        f'<span class="attention-tag date"><small>Due date</small>{html.escape(selected_due)}</span>',
                    ])
                    selected_summary = selected.get("Summary") or selected.get("Why it matters")
                    short_title = _short_task_title(selected_summary)
                    selected_status_badge = (
                        f'<span class="task-intelligence-status uc-badge {_status_badge_class(selected_status)}">{html.escape(selected_status)}</span>'
                        if _attention_value(selected_status) else ""
                    )
                    st.markdown(
                        '<section class="task-intelligence">'
                        '<div class="task-intelligence-head"><div>'
                        f'<div class="task-intelligence-kicker">Task intelligence / {html.escape(str(selected["Task"]))}</div>'
                        f'<div class="task-intelligence-title">{html.escape(short_title)}</div>'
                        f'</div>{selected_status_badge}</div>'
                        + (f'<div class="task-intelligence-tags">{selected_tags}</div>' if selected_tags else '')
                        + (f'<div class="task-intelligence-copy">{html.escape(str(selected.get("Why it matters")))}</div>'
                           if selected.get("Why it matters") and selected.get("Why it matters") != selected_summary else '')
                        + (f'<details class="task-intelligence-impact"><summary>Full task text</summary>{html.escape(str(selected_summary))}</details>'
                           if selected_summary else '')
                        + '</section>', unsafe_allow_html=True,
                    )

    
            elif selected_section == "Impact map":
                _analysis_heading()
                dependencies = list(analysis_output.get("dependencies") or [])
                workload = list(analysis_output.get("workload_signals") or [])
                dependency_items = []
                for item in dependencies[:4]:
                    blocked, source, impact = item.get("blocked_task"), item.get("depends_on"), item.get("impact")
                    status = item.get("status")
                    if blocked and source:
                        status_html = (
                            f'<span class="dependency-status uc-badge {_status_badge_class(status)}">{html.escape(str(status))}</span>'
                            if status is not None and str(status).strip() else ""
                        )
                        dependency_items.append(f'<div class="dependency-item">'
                            f'<div class="dependency-route"><span class="dependency-node">{html.escape(str(blocked))}</span>'
                            f'<span class="dependency-arrow">→</span><span class="dependency-node source">{html.escape(str(source))}</span>{status_html}</div>'
                            + (f'<div class="dependency-copy">{html.escape(str(impact))}</div>' if impact else '') + '</div>')
                workload_items = []
                for item in workload:
                    issue = item.get("issue")
                    if issue:
                        related_text = ", ".join(map(str, item.get("related_tasks") or []))
                        workload_items.append('<div class="workload-item">'
                            + (f'<div class="workload-person">{html.escape(str(item.get("assignee")))}</div>' if item.get("assignee") else '')
                            + f'<div class="workload-issue">{html.escape(str(issue))}</div>'
                            + (f'<div class="workload-tasks">Related · {html.escape(related_text)}</div>' if related_text else '') + '</div>')
                panels = []
                if dependency_items:
                    panels.append('<section class="impact-panel"><div class="impact-kicker">FLOW AT RISK</div>'
                                  '<div class="impact-heading">Dependencies holding work back</div>' + "".join(dependency_items) + '</section>')
                if workload_items:
                    panels.append('<section class="impact-panel accent"><div class="impact-kicker">TEAM SIGNAL</div>'
                                  '<div class="impact-heading">Workload to watch</div>' + "".join(workload_items) + '</section>')
                if panels:
                    st.markdown(f'<div class="impact-layout">{"".join(panels)}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(
                        '<section class="impact-empty-state"><div class="impact-empty-content">'
                        '<div class="impact-empty-scene" aria-hidden="true">'
                        '<div class="impact-empty-cloud one"></div><div class="impact-empty-cloud two"></div>'
                        '<div class="impact-empty-path one"></div><div class="impact-empty-path two"></div>'
                        '<div class="impact-empty-node one">•</div><div class="impact-empty-node two">•</div>'
                        '<div class="impact-empty-node three">•</div><div class="impact-empty-node four">•</div>'
                        '<div class="impact-empty-folder"><div class="impact-empty-bars"><i></i><i></i><i></i></div></div>'
                        '<div class="impact-empty-check">✓</div></div>'
                        '<div class="impact-empty-title">No dependency or workload signals</div>'
                        '<div class="impact-empty-copy">No dependency or workload signals were returned by the Analysis Agent.</div>'
                        '</div></section>',
                        unsafe_allow_html=True,
                    )
    
            elif selected_section == "Analytics":
                _analysis_heading()
                analytics_status = display_values(project_df, "status").value_counts() if populated(project_df, "status").any() else pd.Series(dtype="int64")
                analytics_resolved = sum(int(value) for name, value in analytics_status.items() if str(name).strip().casefold() in {"done", "resolved", "closed"})
                st.markdown(
                    '<div class="analytics-head"><div class="analytics-title">Explore project data</div>'
                    f'<div class="analytics-summary"><b>{len(project_df):,}</b> total issues &nbsp;/&nbsp; <b>{analytics_resolved:,}</b> resolved work</div></div>',
                    unsafe_allow_html=True,
                )
                for container, field, title, color in zip(st.columns(2), ("status", "priority"), ("Issue status", "Priority mix"), ("#7181E7", "#866AE0")):
                    with container:
                        render_summary_bars(project_df, field, title, color)
                render_summary_bars(project_df, "assignee_id", "Tasks per assignee", "#6F98BC")
    
            elif selected_section == "Issue register":
                _analysis_heading()
                filtered = project_df.copy()
                project_column = "project_name" if populated(filtered, "project_name").any() else "project_key"
                with st.container(key="issue_register_filters"):
                    for container, field, label, key in zip(
                        st.columns([1.25, 1, 1]), (project_column, "status", "priority"),
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
                    st.markdown(
                        '<section class="register-empty"><div class="register-empty-icon">⌕</div>'
                        '<div class="register-empty-title">No issues match the current filters</div>'
                        '<div class="register-empty-copy">Try adjusting or clearing the filters to view more records.</div></section>',
                        unsafe_allow_html=True,
                    )
                else:
                    render_register_table(filtered, total_records=len(project_df))
    
    
    
    elif active_stage == "simulation":
        # =========================================================
        # SIMULATION PAGE — Streamlit recreation of the supplied React design
        # =========================================================

        if not simulation_output:
            st.info("No Simulation Agent result is available for this session.")
        else:
            if hasattr(simulation_output, "model_dump"):
                simulation_output = simulation_output.model_dump()

            def _esc(value):
                return html.escape(str(value)) if value is not None else ""

            def _flatten_output(value, prefix=""):
                rows = []
                if isinstance(value, dict):
                    for key, item in value.items():
                        label = f"{prefix} · {key}" if prefix else str(key)
                        if isinstance(item, dict):
                            rows.extend(_flatten_output(item, label))
                        else:
                            rows.append((label, item))
                return rows

            def _value_text(value):
                if isinstance(value, list):
                    return ", ".join(map(str, value))
                return str(value)

            def _output_rows(value):
                return "".join(
                    '<div class="uc-output-row">'
                    f'<span>{_esc(label).replace("_", " ")}</span>'
                    f'<strong>{_esc(_value_text(item))}</strong>'
                    '</div>'
                    for label, item in _flatten_output(value)
                )

            identified_problem = simulation_output.get("identified_problem") or ""
            candidate_strategies = simulation_output.get("candidate_strategies") or []
            simulated_strategies = simulation_output.get("simulated_strategies") or []
            selected_strategy = simulation_output.get("selected_strategy")
            selected_simulation = simulation_output.get("selected_simulation")
            expected_delay_reduction = simulation_output.get("expected_delay_reduction")
            recovery_plan_summary = simulation_output.get("recovery_plan_summary") or ""
            recovery_execution_order = simulation_output.get("recovery_execution_order") or []
            recovery_order_reason = simulation_output.get("recovery_order_reason") or ""
            explanation = simulation_output.get("explanation") or ""

            selected_strategy_payload = selected_strategy if isinstance(selected_strategy, dict) else {}
            if not selected_strategy_payload and isinstance(selected_simulation, dict):
                selected_strategy_payload = selected_simulation.get("strategy") or {}
            selected_description = selected_strategy_payload.get("description") or ""
            selected_type = selected_strategy_payload.get("type") or ""

            candidate_cards_html = ""
            for index, strategy in enumerate(candidate_strategies, start=1):
                description = strategy.get("description")
                strategy_type = strategy.get("type")
                target_tasks = strategy.get("target_tasks") or []
                changes = strategy.get("changes") or {}
                target_html = "".join(f'<span>{_esc(task_id)}</span>' for task_id in target_tasks)
                candidate_cards_html += (
                    '<article class="uc-strategy-card candidate">'
                    f'<div class="uc-strategy-index">0{index}</div>'
                    + (f'<div class="uc-strategy-type">{_esc(strategy_type)}</div>' if strategy_type else '')
                    + (f'<div class="uc-strategy-desc">{_esc(description)}</div>' if description else '')
                    + (f'<div class="uc-strategy-targets"><small>Target tasks</small>{target_html}</div>' if target_html else '')
                    + (f'<details class="uc-detail"><summary>Proposed changes</summary><div class="uc-output-table">{_output_rows(changes)}</div></details>' if changes else '')
                    + '</article>'
                )

            strategy_cards_html = ""
            for index, result in enumerate(simulated_strategies, start=1):
                strategy = result.get("strategy") or {}
                strategy_type = strategy.get("type")
                description = strategy.get("description")
                target_tasks = strategy.get("target_tasks") or []
                status = result.get("status")
                expected_effect = result.get("expected_effect")
                risk = result.get("risk")
                resource_impact = result.get("resource_impact")
                affected_tasks = result.get("affected_tasks") or []
                modified_tasks = result.get("modified_tasks") or []
                before = result.get("before") or {}
                after = result.get("after") or {}
                result_comparison = result.get("comparison") or {}
                assumptions = result.get("assumptions") or []
                result_warnings = result.get("warnings") or []
                is_selected = isinstance(selected_simulation, dict) and result == selected_simulation
                selected_class = " selected" if is_selected else ""
                target_html = "".join(f'<span>{_esc(task_id)}</span>' for task_id in target_tasks)
                affected_html = "".join(f'<span>{_esc(task_id)}</span>' for task_id in affected_tasks)
                modified_html = "".join(f'<span>{_esc(task_id)}</span>' for task_id in modified_tasks)
                detail_html = (
                    '<details class="uc-detail"><summary>Simulation details</summary>'
                    + (f'<div class="uc-task-group"><small>Affected tasks</small><div class="uc-strategy-targets">{affected_html}</div></div>' if affected_html else '')
                    + (f'<div class="uc-task-group"><small>Modified tasks</small><div class="uc-strategy-targets modified">{modified_html}</div></div>' if modified_html else '')
                    + (f'<div class="uc-before-after"><div><small>Before</small><div class="uc-output-table">{_output_rows(before)}</div></div><div><small>After</small><div class="uc-output-table">{_output_rows(after)}</div></div></div>' if before or after else '')
                    + (f'<div class="uc-output-table selected-changes"><small>Before / after comparison</small>{_output_rows(result_comparison)}</div>' if result_comparison else '')
                    + (f'<div class="uc-agent-list"><small>Assumptions</small>{"".join(f"<p>{_esc(item)}</p>" for item in assumptions)}</div>' if assumptions else '')
                    + (f'<div class="uc-agent-list warning"><small>Warnings</small>{"".join(f"<p>{_esc(item)}</p>" for item in result_warnings)}</div>' if result_warnings else '')
                    + '</details>'
                )
                strategy_cards_html += (
                    f'<article class="uc-strategy-card{selected_class}">'
                    '<div class="uc-strategy-top">'
                    f'<span class="uc-strategy-index">0{index}</span>'
                    + (f'<span class="uc-strategy-status uc-badge {_status_badge_class(status)}">{_esc(status)}</span>' if status else '')
                    + '</div>'
                    + (f'<div class="uc-strategy-type">{_esc(strategy_type)}</div>' if strategy_type else '')
                    + (f'<div class="uc-strategy-desc">{_esc(description)}</div>' if description else '')
                    + (f'<div class="uc-strategy-effect">{_esc(expected_effect)}</div>' if expected_effect else '')
                    + (f'<div class="uc-strategy-targets"><small>Target tasks</small>{target_html}</div>' if target_html else '')
                    + '<div class="uc-strategy-meta">'
                    + (f'<span>Risk · {_esc(risk)}</span>' if risk else '')
                    + (f'<span>Resources · {_esc(resource_impact)}</span>' if resource_impact else '')
                    + '</div>'
                    + detail_html
                    + '</article>'
                )

            # Presentation only: reuse the existing simulation conclusion and recommendation values.
            summary_status = selected_simulation.get("status") if isinstance(selected_simulation, dict) else ""
            summary_status_html = (
                f'<div class="uc-flow-pill uc-badge {_status_badge_class(summary_status)}">{_esc(summary_status)}</div>'
                if summary_status else ""
            )
            direction_type_html = (
                f'<div class="uc-flow-pill direction">{_esc(selected_type)}</div>'
                if selected_type else ""
            )
            summary_cards_html = (
                '<section class="uc-connected-flow">'
                '<div class="uc-flow-card conclusion">'
                '<div class="uc-flow-card-head"><div class="uc-flow-title">Simulation conclusion</div></div>'
                + (f'<div class="uc-flow-copy">{_esc(explanation)}</div>' if explanation else '')
                + summary_status_html
                + '</div>'
                '<div class="uc-flow-divider" aria-hidden="true"><span></span></div>'
                '<div class="uc-flow-card direction">'
                '<div class="uc-flow-card-head"><div class="uc-flow-title">Recommended direction</div></div>'
                + (f'<div class="uc-flow-copy">{_esc(recovery_plan_summary)}</div>' if recovery_plan_summary else '')
                + direction_type_html
                + '</div></section>'
            )
            comparison_html = ""
            for item in simulation_output.get("comparison") or []:
                comparison_html += (
                    '<article class="uc-compare-card">'
                    f'<div class="uc-compare-type">{_esc(item.get("strategy_type"))}</div>'
                    '<div class="uc-compare-grid">'
                    f'<div><small>Effectiveness</small><strong>{_esc(item.get("effectiveness"))}</strong></div>'
                    f'<div><small>Feasibility</small><strong>{_esc(item.get("feasibility"))}</strong></div>'
                    f'<div><small>Risk</small><strong>{_esc(item.get("risk"))}</strong></div>'
                    f'<div><small>Resources</small><strong>{_esc(item.get("resource_impact"))}</strong></div>'
                    '</div>'
                    f'<div class="uc-compare-summary">{_esc(item.get("summary"))}</div>'
                    '</article>'
                )

            selected_decision_html = ""
            if isinstance(selected_strategy, dict) or isinstance(selected_simulation, dict):
                selected_targets = selected_strategy_payload.get("target_tasks") or []
                selected_changes = selected_strategy_payload.get("changes") or {}
                selected_target_html = "".join(f'<span>{_esc(item)}</span>' for item in selected_targets)
                selected_status = selected_simulation.get("status") if isinstance(selected_simulation, dict) else None
                selected_effect = selected_simulation.get("expected_effect") if isinstance(selected_simulation, dict) else None
                selected_affected = selected_simulation.get("affected_tasks") or [] if isinstance(selected_simulation, dict) else []
                selected_modified = selected_simulation.get("modified_tasks") or [] if isinstance(selected_simulation, dict) else []
                selected_before = selected_simulation.get("before") or {} if isinstance(selected_simulation, dict) else {}
                selected_after = selected_simulation.get("after") or {} if isinstance(selected_simulation, dict) else {}
                selected_comparison = selected_simulation.get("comparison") or {} if isinstance(selected_simulation, dict) else {}
                selected_risk = selected_simulation.get("risk") if isinstance(selected_simulation, dict) else None
                selected_resources = selected_simulation.get("resource_impact") if isinstance(selected_simulation, dict) else None
                selected_assumptions = selected_simulation.get("assumptions") or [] if isinstance(selected_simulation, dict) else []
                selected_warnings = selected_simulation.get("warnings") or [] if isinstance(selected_simulation, dict) else []
                selected_decision_html = (
                    '<section class="uc-selected-panel">'
                    '<div class="uc-section-eyebrow">FINAL DECISION</div>'
                    '<div class="uc-selected-head">'
                    '<div>'
                    + (f'<div class="uc-strategy-type">{_esc(selected_type)}</div>' if selected_type else '')
                    + (f'<div class="uc-section-title">{_esc(selected_description)}</div>' if selected_description else '')
                    + '</div>'
                    + (f'<span class="uc-strategy-status uc-badge {_status_badge_class(selected_status)}">{_esc(selected_status)}</span>' if selected_status else '')
                    + '</div>'
                    + (f'<div class="uc-strategy-effect">{_esc(selected_effect)}</div>' if selected_effect else '')
                    + (f'<div class="uc-strategy-targets"><small>Target tasks</small>{selected_target_html}</div>' if selected_target_html else '')
                    + '<div class="uc-strategy-meta">'
                    + (f'<span>Risk · {_esc(selected_risk)}</span>' if selected_risk else '')
                    + (f'<span>Resources · {_esc(selected_resources)}</span>' if selected_resources else '')
                    + '</div>'
                    + (f'<div class="uc-output-table selected-changes"><small>Changes</small>{_output_rows(selected_changes)}</div>' if selected_changes else '')
                    + (f'<div class="uc-task-group"><small>Affected tasks</small><div class="uc-strategy-targets">{"".join(f"<span>{_esc(item)}</span>" for item in selected_affected)}</div></div>' if selected_affected else '')
                    + (f'<div class="uc-task-group"><small>Modified tasks</small><div class="uc-strategy-targets modified">{"".join(f"<span>{_esc(item)}</span>" for item in selected_modified)}</div></div>' if selected_modified else '')
                    + (f'<div class="uc-before-after"><div><small>Before</small><div class="uc-output-table">{_output_rows(selected_before)}</div></div><div><small>After</small><div class="uc-output-table">{_output_rows(selected_after)}</div></div></div>' if selected_before or selected_after else '')
                    + (f'<div class="uc-output-table selected-changes"><small>Before / after comparison</small>{_output_rows(selected_comparison)}</div>' if selected_comparison else '')
                    + (f'<div class="uc-agent-list"><small>Assumptions</small>{"".join(f"<p>{_esc(item)}</p>" for item in selected_assumptions)}</div>' if selected_assumptions else '')
                    + (f'<div class="uc-agent-list warning"><small>Warnings</small>{"".join(f"<p>{_esc(item)}</p>" for item in selected_warnings)}</div>' if selected_warnings else '')
                    + '</section>'
                )
            else:
                selected_decision_html = (
                    '<section class="uc-selected-panel">'
                    '<div class="uc-section-eyebrow">FINAL DECISION</div>'
                    '<div class="uc-empty">No strategy or simulation result was selected by the Simulation Agent.</div>'
                    '</section>'
                )

            # Presentation only: map existing uploaded task fields to visual chip tones.
            # This only chooses a display color; it does not change task data.
            def _roadmap_task_tone(task_id):
                task_row = _task_row(project_df, task_id)
                status = _row_value(task_row, "status", "").casefold()
                priority = _row_value(task_row, "priority", "").casefold()
                if any(word in status for word in ("block", "critical", "impediment")):
                    return _status_badge_class(status)
                if any(word in status for word in ("overdue", "late", "risk", "warning")):
                    return _status_badge_class(status)
                if priority:
                    return _priority_badge_class(priority)
                if status:
                    return _status_badge_class(status)
                return "status-neutral"

            # Build roadmap from live recovery_execution_order.
            roadmap_html = ""
            ordered_steps = sorted(
                recovery_execution_order,
                key=lambda value: value.get("step", 0),
            )

            for index, stage in enumerate(ordered_steps):
                step = stage.get("step", index + 1)
                task_ids = stage.get("task_ids") or []
                action = stage.get("action")
                if not action:
                    continue

                roadmap_html += f"""
                    <div class="uc-flow-stage">
                        <div class="uc-flow-head">
                            <div class="uc-step-circle">{_esc(step)}</div>
                            <div class="uc-step-title">Step {_esc(step)}</div>
                        </div>
                        <div class="uc-stage-items">
                """

                if task_ids:
                    for task_id in task_ids:
                        task_tone = _roadmap_task_tone(task_id)
                        roadmap_html += f"""
                            <div class="uc-flow-card">
                                <div class="uc-task-id uc-badge {task_tone}">{_esc(task_id)}</div>
                                <div class="uc-task-desc">{_esc(action)}</div>
                            </div>
                        """
                else:
                    roadmap_html += f"""
                        <div class="uc-flow-card">
                            <div class="uc-task-desc">{_esc(action)}</div>
                        </div>
                    """

                roadmap_html += "</div></div>"

                if index < len(ordered_steps) - 1:
                    roadmap_html += """
                        <div class="uc-flow-connector">
                            <div class="uc-flow-line">
                                <span class="uc-flow-dot"></span>
                            </div>
                        </div>
                    """

            roadmap_empty_class = ""
            if not roadmap_html:
                roadmap_empty_class = " is-empty"
                roadmap_html = """
                    <div class="uc-roadmap-clear">
                        <div class="uc-roadmap-clear-icon" aria-hidden="true">
                            <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M24 5.5 39 11v10.7c0 9.1-6.1 17.4-15 20.8C15.1 39.1 9 30.8 9 21.7V11l15-5.5Z" fill="#E9F8F1" stroke="#66B992" stroke-width="2.2"/>
                                <path d="m16.5 23.6 5 5.1 10.4-10.5" stroke="#39966E" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </div>
                        <div class="uc-roadmap-clear-title">Everything is on track</div>
                        <div class="uc-roadmap-clear-copy">No recovery actions were returned by the Simulation Agent.</div>
                    </div>
                """

            # st.html renders raw HTML directly, avoiding Markdown parsing
            # that can turn nested/indented HTML into visible code blocks.
            st.html(textwrap.dedent(f"""
                <style>
                    .block-container {{
                        max-width: 1480px !important;
                        padding: 24px 36px 72px !important;
                    }}
                    .stApp {{
                        background:
                            linear-gradient(118deg, rgba(94,130,235,.085) 0%, rgba(94,130,235,0) 24%),
                            linear-gradient(302deg, rgba(157,122,224,.085) 0%, rgba(157,122,224,0) 25%),
                            radial-gradient(ellipse at 50% 18%, rgba(255,255,255,.98) 0%, rgba(255,255,255,.74) 34%, rgba(255,255,255,0) 68%),
                            linear-gradient(180deg,#F8F9FD 0%,#F5F7FC 55%,#F7F8FC 100%) !important;
                        background-attachment: fixed !important;
                        background-repeat: no-repeat !important;
                        color: #16223B !important;
                        font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
                    }}
                    header[data-testid="stHeader"] {{
                        display: none !important;
                    }}

                    .uc-sim-root {{
                        min-height: 0;
                        background: transparent;
                        color: #16223B;
                    }}

                    .uc-main {{
                        padding: 8px 0 0;
                    }}

                    .uc-top-grid {{
                        position:relative;
                        overflow:hidden;
                        padding:28px 24px 26px;
                        border:1px solid #E0E7F8;
                        border-radius:28px;
                        background:radial-gradient(ellipse at 50% 0%,rgba(128,151,242,.22),transparent 55%),linear-gradient(140deg,#F9FBFF 0%,#EFF3FF 100%);
                        box-shadow:0 18px 42px rgba(54,76,140,.09);
                    }}
                    .uc-top-grid::before {{
                        content:"";
                        position:absolute;
                        inset:0;
                        opacity:.5;
                        background:radial-gradient(circle at 11% 76%,rgba(108,144,239,.14) 0 4px,transparent 5px),radial-gradient(circle at 88% 23%,rgba(137,104,230,.13) 0 5px,transparent 6px);
                        pointer-events:none;
                    }}
                    .uc-top-grid::after {{
                        content:"";
                        position:absolute;
                        width:290px;
                        height:290px;
                        top:-204px;
                        right:-105px;
                        border:1px solid rgba(119,130,232,.14);
                        border-radius:50%;
                        box-shadow:0 0 0 34px rgba(119,130,232,.035),0 0 0 74px rgba(119,130,232,.022);
                        pointer-events:none;
                    }}
                    .uc-top-grid .uc-right {{ display:block; }}
                    .uc-connected-flow {{
                        position:relative;
                        z-index:1;
                        display:grid;
                        grid-template-columns:minmax(0,1fr) 54px minmax(0,1fr);
                        align-items:stretch;
                        gap:14px;
                    }}
                    .uc-flow-card {{
                        position:relative;
                        min-height:224px;
                        box-sizing:border-box;
                        padding:29px 26px 24px;
                        border:1px solid #DDE5F3;
                        border-radius:18px;
                        background:linear-gradient(145deg,#FFFFFF,#FAFBFF);
                        box-shadow:0 10px 22px rgba(61,82,148,.07);
                    }}
                    .uc-flow-card::after {{
                        content:"";
                        position:absolute;
                        right:0;
                        bottom:0;
                        left:0;
                        height:5px;
                        border-radius:0 0 22px 22px;
                    }}
                    .uc-flow-card.conclusion {{ border-color:#D6E4FF; }}
                    .uc-flow-card.conclusion::after {{ background:linear-gradient(90deg,#5797FF,#6881F0); }}
                    .uc-flow-card.direction {{ border-color:#E6DBFF; }}
                    .uc-flow-card.direction::after {{ background:linear-gradient(90deg,#9877FA,#6F52DE); }}
                    .uc-flow-divider {{
                        display:grid;
                        place-items:center;
                        align-self:center;
                        min-height:100%;
                    }}
                    .uc-flow-divider span {{
                        position:relative;
                        display:block;
                        width:36px;
                        height:2px;
                        border-radius:99px;
                        background:linear-gradient(90deg,#93ACF3,#8068E6);
                        box-shadow:0 2px 7px rgba(91,108,213,.16);
                    }}
                    .uc-flow-divider span::before {{
                        content:"";
                        position:absolute;
                        top:50%;
                        right:-1px;
                        width:9px;
                        height:9px;
                        border-top:2px solid #8068E6;
                        border-right:2px solid #8068E6;
                        transform:translateY(-50%) rotate(45deg);
                    }}
                    .uc-flow-step {{
                        position:absolute;
                        top:-18px;
                        left:20px;
                        display:grid;
                        width:52px;
                        height:52px;
                        place-items:center;
                        border:4px solid #F5F7FF;
                        border-radius:50%;
                        color:#FFF;
                        font-size:15px;
                        font-weight:850;
                        letter-spacing:-.03em;
                        box-shadow:0 10px 20px rgba(74,95,192,.25);
                    }}
                    .uc-flow-step.blue {{ background:linear-gradient(135deg,#4D9CFF,#3D62D8); }}
                    .uc-flow-step.purple {{ background:linear-gradient(135deg,#A07AFD,#6245DB); }}
                    .uc-flow-card-head {{ display:flex; align-items:center; gap:12px; margin-top:19px; }}
                    .uc-flow-icon {{ display:grid; width:46px; height:46px; place-items:center; border-radius:14px; font-size:23px; font-weight:850; box-shadow:inset 0 1px 0 rgba(255,255,255,.85); }}
                    .uc-flow-icon.chart {{ color:#3F78E7; background:linear-gradient(145deg,#EFF5FF,#E4EDFF); }}
                    .uc-flow-icon.bulb {{ color:#7651DD; background:linear-gradient(145deg,#F4EFFF,#ECE4FF); }}
                    .uc-flow-title {{ color:#172440; font-size:16px; font-weight:820; letter-spacing:-.03em; }}
                    .uc-flow-copy {{ margin-top:17px; color:#647492; font-size:12px; line-height:1.68; }}
                    .uc-flow-pill {{ display:inline-flex; max-width:100%; box-sizing:border-box; margin-top:17px; padding:7px 11px; border:1px solid transparent; border-radius:999px; font-size:10px; font-weight:790; line-height:1.15; overflow-wrap:anywhere; }}
                    .uc-flow-pill.conclusion {{ color:#3D75D9; border-color:#D8E7FF; background:#EFF5FF; }}
                    .uc-flow-pill.direction {{ color:#704BD4; border-color:#E6DAFF; background:#F3EDFF; }}

                    .uc-left {{
                        position: relative;
                        z-index: 1;
                        display: flex;
                        flex-direction: column;
                        gap: 32px;
                    }}

                    .uc-kicker {{
                        display: inline-flex;
                        align-items: center;
                        gap: 8px;
                        width: max-content;
                        padding: 6px 9px;
                        margin-bottom: 16px;
                        border-radius: 99px;
                        background: rgba(255,255,255,.09);
                        color: #C6D9FA;
                        border: 1px solid rgba(220,232,255,.18);
                        font-size: 10px;
                        font-weight: 750;
                        letter-spacing: .06em;
                        text-transform: uppercase;
                    }}

                    .uc-kicker-icon {{
                        color: #7DE5E0;
                        font-size: 12px;
                    }}

                    .uc-problem-title {{
                        margin: 0 0 16px;
                        color: #FFFFFF;
                        font-size: 32px;
                        line-height: 1.18;
                        font-weight: 780;
                        letter-spacing: -.055em;
                    }}

                    .uc-problem-copy {{
                        padding: 2px 0 2px 16px;
                        border-left: 3px solid #75D9D5;
                        color: #CAD8F0;
                        font-size: 13px;
                        line-height: 1.7;
                    }}

                    .uc-right {{
                        position: relative;
                        z-index: 1;
                        display: flex;
                        flex-direction: column;
                        gap: 24px;
                    }}

                    .uc-side-card {{
                        position: relative;
                        overflow: hidden;
                        padding: 20px;
                        border: 1px solid rgba(220,232,255,.18);
                        border-radius: 16px;
                        background: rgba(255,255,255,.08);
                        backdrop-filter: blur(8px);
                        box-shadow: 0 12px 28px rgba(9,20,48,.12);
                    }}

                    .uc-side-card::before {{
                        content: "";
                        position: absolute;
                        top: 0;
                        bottom: 0;
                        left: 0;
                        width: 4px;
                        background: #A9B8CB;
                    }}

                    .uc-side-card.recommended {{
                        border-color: rgba(116,224,214,.34);
                        box-shadow: 0 12px 28px rgba(9,20,48,.14);
                    }}

                    .uc-side-card.recommended::before {{
                        background: #4B88F5;
                    }}

                    .uc-side-title {{
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        margin-bottom: 12px;
                        color: #FFFFFF;
                        font-size: 14px;
                        font-weight: 760;
                    }}

                    .uc-side-title .blue {{
                        color: #4B88F5;
                    }}

                    .uc-side-copy {{
                        color: #CAD8F0;
                        font-size: 12px;
                        line-height: 1.7;
                    }}

                    .uc-strategy-section {{
                        margin-top: 30px;
                    }}

                    .uc-section-head {{
                        display: flex;
                        align-items: end;
                        justify-content: space-between;
                        gap: 16px;
                        margin-bottom: 14px;
                    }}

                    .uc-section-eyebrow {{
                        color: #7185A6;
                        font-size: 9px;
                        font-weight: 820;
                        letter-spacing: .14em;
                        text-transform: uppercase;
                    }}

                    .uc-section-title {{
                        margin-top: 5px;
                        color: #182641;
                        font-size: 20px;
                        font-weight: 780;
                        letter-spacing: -.03em;
                    }}

                    .uc-delay-chip {{
                        padding: 7px 10px;
                        border: 1px solid #DCE7F8;
                        border-radius: 99px;
                        background: #F2F7FF;
                        color: #4266A6;
                        font-size: 10px;
                        font-weight: 760;
                    }}

                    .uc-strategy-grid {{
                        display: grid;
                        grid-template-columns: repeat(2,minmax(0,1fr));
                        gap: 14px;
                    }}

                    .uc-strategy-card {{
                        position: relative;
                        overflow: hidden;
                        min-height: 190px;
                        padding: 20px;
                        border: 1px solid #E3EAF6;
                        border-radius: 18px;
                        background: linear-gradient(145deg,#FFFFFF 0%,#F8FAFF 100%);
                        box-shadow: 0 12px 28px rgba(27,55,97,.045);
                    }}

                    .uc-strategy-card::after {{
                        content: "";
                        position: absolute;
                        right: -45px;
                        bottom: -55px;
                        width: 140px;
                        height: 140px;
                        border: 1px solid rgba(93,117,225,.12);
                        border-radius: 50%;
                        box-shadow: 0 0 0 22px rgba(93,117,225,.025);
                    }}

                    .uc-strategy-card.selected {{
                        border-color: #9EC8F5;
                        background: linear-gradient(145deg,#F7FBFF,#F4F0FF);
                    }}

                    .uc-strategy-card.selected::before {{
                        content: "SELECTED";
                        position: absolute;
                        right: 18px;
                        top: 18px;
                        color: #3E70C6;
                        font-size: 8px;
                        font-weight: 850;
                        letter-spacing: .12em;
                    }}

                    .uc-strategy-top {{
                        display: flex;
                        align-items: center;
                        gap: 9px;
                    }}

                    .uc-strategy-index {{
                        color: #A5B4CC;
                        font-size: 10px;
                        font-weight: 850;
                        letter-spacing: .08em;
                    }}

                    .uc-strategy-status {{
                        padding: 4px 7px;
                        border-radius: 99px;
                        background: #EBF8F4;
                        color: #28816F;
                        font-size: 8px;
                        font-weight: 800;
                        text-transform: uppercase;
                    }}
                    .uc-strategy-status.uc-badge,.uc-flow-pill.uc-badge,.uc-task-id.uc-badge {{ background:var(--uc-badge-bg) !important; color:var(--uc-badge-text) !important; border-color:var(--uc-badge-border) !important; }}

                    .uc-strategy-type {{
                        position: relative;
                        z-index: 1;
                        margin-top: 15px;
                        color: #2B5DB7;
                        font-size: 10px;
                        font-weight: 820;
                        letter-spacing: .08em;
                        text-transform: uppercase;
                    }}

                    .uc-strategy-desc {{
                        position: relative;
                        z-index: 1;
                        margin-top: 7px;
                        color: #253651;
                        font-size: 13px;
                        line-height: 1.55;
                        font-weight: 700;
                    }}

                    .uc-strategy-effect {{
                        position: relative;
                        z-index: 1;
                        margin-top: 9px;
                        color: #73849D;
                        font-size: 10px;
                        line-height: 1.55;
                    }}

                    .uc-strategy-targets {{
                        position: relative;
                        z-index: 1;
                        display: flex;
                        flex-wrap: wrap;
                        gap: 5px;
                        margin-top: 12px;
                    }}

                    .uc-strategy-targets small,
                    .uc-task-group > small,
                    .uc-before-after small,
                    .uc-agent-list small,
                    .uc-output-table > small {{
                        width: 100%;
                        color: #92A0B4;
                        font-size: 8px;
                        font-weight: 800;
                        letter-spacing: .08em;
                        text-transform: uppercase;
                    }}

                    .uc-strategy-targets span {{
                        padding: 4px 7px;
                        border-radius: 99px;
                        background: #EEF4FF;
                        color: #4D69A0;
                        font-size: 8px;
                        font-weight: 760;
                    }}

                    .uc-strategy-targets.modified span {{
                        background: #EAF9F5;
                        color: #287B6B;
                    }}

                    .uc-strategy-meta {{
                        position: relative;
                        z-index: 1;
                        display: flex;
                        flex-wrap: wrap;
                        gap: 12px;
                        margin-top: 13px;
                        padding-top: 10px;
                        border-top: 1px solid #EBF0F7;
                        color: #8897AC;
                        font-size: 8px;
                        font-weight: 720;
                        text-transform: capitalize;
                    }}

                    .uc-detail {{
                        position: relative;
                        z-index: 2;
                        margin-top: 14px;
                        padding-top: 11px;
                        border-top: 1px solid #EBF0F7;
                    }}

                    .uc-detail summary {{
                        cursor: pointer;
                        color: #4D6FA8;
                        font-size: 9px;
                        font-weight: 800;
                        list-style: none;
                    }}

                    .uc-detail summary::after {{
                        content: "+";
                        float: right;
                        color: #92A4C0;
                    }}

                    .uc-detail[open] summary::after {{ content: "−"; }}

                    .uc-task-group {{ margin-top: 13px; }}

                    .uc-before-after {{
                        display: grid;
                        grid-template-columns: repeat(2,minmax(0,1fr));
                        gap: 10px;
                        margin-top: 14px;
                    }}

                    .uc-before-after > div {{
                        padding: 11px;
                        border: 1px solid #E8EEF7;
                        border-radius: 12px;
                        background: #FBFCFF;
                    }}

                    .uc-output-table {{ margin-top: 7px; }}

                    .uc-output-row {{
                        display: flex;
                        align-items: flex-start;
                        justify-content: space-between;
                        gap: 10px;
                        padding: 6px 0;
                        border-top: 1px solid #EEF2F7;
                        color: #8190A5;
                        font-size: 8px;
                    }}

                    .uc-output-row strong {{
                        color: #41526D;
                        font-size: 8px;
                        text-align: right;
                    }}

                    .uc-agent-list {{
                        margin-top: 12px;
                        padding: 11px;
                        border-radius: 12px;
                        background: #F3F7FD;
                    }}

                    .uc-agent-list.warning {{ background: #FFF7EA; }}
                    .uc-agent-list p {{ margin: 6px 0 0; color: #64758E; font-size: 9px; line-height: 1.5; }}

                    .uc-comparison-section {{ margin-top: 30px; }}
                    .uc-comparison-grid {{ display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 14px; }}
                    .uc-compare-card {{ padding: 18px; border: 1px solid #E3EAF6; border-radius: 18px; background: #FFF; box-shadow: 0 10px 24px rgba(27,55,97,.04); }}
                    .uc-compare-type {{ color: #2E5CB2; font-size: 11px; font-weight: 820; text-transform: uppercase; }}
                    .uc-compare-grid {{ display: grid; grid-template-columns: repeat(4,minmax(0,1fr)); gap: 8px; margin-top: 12px; }}
                    .uc-compare-grid > div {{ padding: 9px; border-radius: 10px; background: #F5F8FD; }}
                    .uc-compare-grid small {{ display: block; color: #92A0B4; font-size: 7px; font-weight: 780; text-transform: uppercase; }}
                    .uc-compare-grid strong {{ display: block; margin-top: 4px; color: #42536E; font-size: 9px; font-weight: 760; }}
                    .uc-compare-summary {{ margin-top: 12px; color: #71829A; font-size: 10px; line-height: 1.6; }}

                    .uc-selected-panel {{
                        margin-top: 30px;
                        padding: 22px;
                        border: 1px solid #BFD5F5;
                        border-radius: 20px;
                        background: linear-gradient(145deg,#F8FBFF,#F5F1FF);
                        box-shadow: 0 14px 30px rgba(45,82,150,.06);
                    }}
                    .uc-selected-head {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }}
                    .uc-selected-panel .uc-section-title {{ max-width: 850px; font-size: 17px; line-height: 1.45; }}
                    .selected-changes {{ margin-top: 14px; padding: 12px; border-radius: 12px; background: rgba(255,255,255,.7); }}

                    .uc-empty {{
                        grid-column: 1 / -1;
                        padding: 18px;
                        border: 1px dashed #CBD9EC;
                        border-radius: 14px;
                        background: #F8FAFE;
                        color: #7889A2;
                        font-size: 10px;
                        line-height: 1.55;
                    }}

                    .uc-roadmap-section {{
                        margin-top: 36px;
                        padding-top: 28px;
                        border-top: 1px solid #E5ECF7;
                    }}

                    .uc-roadmap-title {{
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        margin: 0;
                        color: #182641;
                        font-size: 20px;
                        font-weight: 760;
                        letter-spacing: -.025em;
                    }}

                    .uc-roadmap-sub {{
                        margin-top: 6px;
                        color: #7B8BA2;
                        font-size: 12px;
                    }}

                    .uc-flow-scroll {{
                        overflow-x: auto;
                        padding: 28px 4px 48px;
                        scrollbar-width: none;
                    }}
                    .uc-flow-scroll::-webkit-scrollbar {{
                        display: none;
                    }}

                    .uc-flow {{
                        display: flex;
                        align-items: stretch;
                        min-width: max-content;
                        padding: 0 16px;
                    }}

                    .uc-flow.is-empty {{
                        min-width: 0;
                        width: 100%;
                        padding: 0;
                    }}

                    .uc-roadmap-clear {{
                        width: 100%;
                        min-height: 190px;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        padding: 30px 24px;
                        text-align: center;
                        border: 1px solid #DDEDE6;
                        border-radius: 20px;
                        background:
                            radial-gradient(circle at 20% 15%, rgba(161, 220, 193, .16), transparent 26%),
                            radial-gradient(circle at 82% 85%, rgba(169, 183, 250, .13), transparent 28%),
                            linear-gradient(145deg, #FFFFFF, #F8FCFA);
                        box-shadow: 0 12px 30px rgba(42, 106, 79, .06);
                    }}

                    .uc-roadmap-clear-icon {{
                        width: 52px;
                        height: 52px;
                        display: grid;
                        place-items: center;
                        margin-bottom: 12px;
                        border-radius: 18px;
                        background: #62B88D;
                        box-shadow: 0 8px 18px rgba(53, 144, 104, .10);
                    }}

                    .uc-roadmap-clear-icon svg {{
                        display: none;
                    }}

                    .uc-roadmap-clear-icon::before {{
                        content: "✓";
                        color: #FFFFFF;
                        font-size: 30px;
                        font-weight: 800;
                        line-height: 1;
                    }}

                    .uc-roadmap-clear-title {{
                        color: #182641;
                        font-size: 18px;
                        font-weight: 760;
                        letter-spacing: -.02em;
                    }}

                    .uc-roadmap-clear-copy {{
                        max-width: 470px;
                        margin-top: 6px;
                        color: #71819A;
                        font-size: 13px;
                        line-height: 1.55;
                    }}

                    .uc-flow-stage {{
                        width: 256px;
                        flex: 0 0 256px;
                        display: flex;
                        flex-direction: column;
                    }}

                    .uc-flow-head {{
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        margin-bottom: 24px;
                    }}

                    .uc-step-circle {{
                        width: 32px;
                        height: 32px;
                        display: grid;
                        place-items: center;
                        margin-bottom: 8px;
                        border: 2px solid #DBEAFE;
                        border-radius: 50%;
                        background: #fff;
                        color: #2563EB;
                        font-size: 13px;
                        font-weight: 900;
                        box-shadow: 0 2px 7px rgba(17,24,39,.05);
                        transition: .2s ease;
                    }}

                    .uc-step-title {{
                        max-width: 230px;
                        color: #6B7280;
                        font-size: 11px;
                        line-height: 1.35;
                        font-weight: 800;
                        letter-spacing: .06em;
                        text-align: center;
                        text-transform: uppercase;
                    }}

                    .uc-stage-items {{
                        position: relative;
                        display: flex;
                        flex: 1;
                        flex-direction: column;
                        justify-content: center;
                        gap: 16px;
                    }}

                    .uc-flow-card {{
                        position: relative;
                        z-index: 2;
                        padding: 16px;
                        border: 1px solid #E5ECF7;
                        border-radius: 16px;
                        background: #fff;
                        box-shadow: 0 10px 24px rgba(27,55,97,.04);
                        transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease;
                    }}

                    .uc-flow-card:hover {{
                        border-color: #A9C4EE;
                        box-shadow: 0 12px 26px rgba(27,55,97,.08);
                    }}

                    .uc-task-id {{
                        display: inline-flex;
                        padding: 2px 8px;
                        margin-bottom: 8px;
                        border: 1px solid #D9E3F2;
                        border-radius: 999px;
                        background: #F1F5FA;
                        color: #5F718B;
                        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
                        font-size: 11px;
                        font-weight: 800;
                    }}

                    .uc-task-id.blocked {{ background:#FFF0F1; border-color:#F6D3D7; color:#BC5964; }}
                    .uc-task-id.warning {{ background:#FFF6E5; border-color:#F6E0AE; color:#B77A19; }}
                    .uc-task-id.priority {{ background:#F3EEFF; border-color:#E0D6FB; color:#7458C8; }}
                    .uc-task-id.active {{ background:#EDF5FF; border-color:#D3E4FC; color:#3773C7; }}
                    .uc-task-id.neutral {{ background:#F1F5FA; border-color:#D9E3F2; color:#5F718B; }}

                    .uc-task-desc {{
                        color: #60718A;
                        font-size: 12px;
                        line-height: 1.55;
                    }}

                    .uc-flow-connector {{
                        position: relative;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        width: 64px;
                        flex: 0 0 64px;
                        margin-top: 72px;
                    }}

                    .uc-flow-line {{
                        position: relative;
                        width: 100%;
                        height: 2px;
                        background: #DEE6F3;
                    }}

                    .uc-flow-dot {{
                        position: absolute;
                        top: 50%;
                        left: 0;
                        width: 8px;
                        height: 8px;
                        transform: translateY(-50%);
                        border-radius: 50%;
                        background: #4B88F5;
                        animation: ucFlowRight 2s linear infinite;
                    }}

                    .uc-order-note {{
                        margin-top: -24px;
                        padding: 16px 18px;
                        border: 1px solid #E5ECF7;
                        border-radius: 16px;
                        background: #FFFFFF;
                        color: #60718A;
                        font-size: 12px;
                        line-height: 1.6;
                    }}

                    @keyframes ucFlowRight {{
                        0% {{ left: 0; opacity: 0; }}
                        20% {{ opacity: 1; }}
                        80% {{ opacity: 1; }}
                        100% {{ left: 100%; opacity: 0; }}
                    }}

                    @media (max-width: 860px) {{
                        .uc-connected-flow {{ grid-template-columns:1fr; gap:14px; }}
                        .uc-flow-divider {{ min-height:28px; }}
                        .uc-flow-divider span {{ transform:rotate(90deg); }}
                    }}

                    .uc-flow-copy,.uc-notes-list li,.uc-notes-empty,.uc-order-note,.uc-compare-summary,.uc-task-desc {{ font-size:13px; line-height:1.65; }}
                    .uc-flow-title,.uc-roadmap-title {{ font-size:18px; }}
                    .uc-flow-pill,.uc-notes-subtitle,.uc-notes-count {{ font-size:11px; }}

                    @media (max-width: 760px) {{
                        .block-container {{
                            padding: 20px 18px 52px !important;
                        }}
                        .uc-problem-title {{
                            font-size: 26px;
                        }}
                        .uc-right {{
                            grid-template-columns: 1fr;
                        }}
                        .uc-strategy-grid {{
                            grid-template-columns: 1fr;
                        }}
                        .uc-comparison-grid {{ grid-template-columns: 1fr; }}
                        .uc-compare-grid {{ grid-template-columns: repeat(2,minmax(0,1fr)); }}
                        .uc-before-after {{ grid-template-columns: 1fr; }}
                    }}
                </style>

                <div class="uc-sim-root">
                    <main class="uc-main">
                        <div class="uc-top-grid">
                            <div class="uc-right">
                                {summary_cards_html}
                            </div>
                        </div>

                        <section class="uc-roadmap-section">
                            <h2 class="uc-roadmap-title">Recovery Execution Order</h2>
                            <div class="uc-flow-scroll">
                                <div class="uc-flow{roadmap_empty_class}">
                                    {roadmap_html}
                                </div>
                            </div>
                        </section>
                    </main>
                </div>
                """).strip())

            # Presentation only: display the existing Simulation Agent lists without altering their contents.
            simulation_assumptions = simulation_output.get("assumptions") or []
            simulation_warnings = simulation_output.get("warnings") or []
            assumptions_html = "".join(
                f'<li>{_esc(assumption)}</li>' for assumption in simulation_assumptions
            ) or '<div class="uc-notes-empty">No additional assumptions were required.</div>'
            warnings_html = "".join(
                f'<li>{_esc(warning)}</li>' for warning in simulation_warnings
            ) or '<div class="uc-notes-empty safe"><span>✓</span>No simulation warnings were identified.</div>'
            st.html(textwrap.dedent(f"""
                <style>
                    .uc-notes-grid {{
                        display:grid;
                        grid-template-columns:repeat(2,minmax(0,1fr));
                        gap:18px;
                        margin-top:26px;
                    }}
                    .uc-notes-card {{
                        position:relative;
                        overflow:hidden;
                        min-height:208px;
                        box-sizing:border-box;
                        padding:22px 24px;
                        border:1px solid #DCE7FA;
                        border-radius:22px;
                        background:linear-gradient(145deg,#FCFEFF 0%,#F3F8FF 100%);
                        box-shadow:0 12px 26px rgba(49,80,145,.06);
                    }}
                    .uc-notes-card.warning {{
                        border-color:#F4E5C6;
                        background:linear-gradient(145deg,#FFFDFC 0%,#FFF8EA 100%);
                    }}
                    .uc-notes-card::before {{
                        content:"";
                        position:absolute;
                        width:148px;
                        height:148px;
                        top:-58px;
                        left:-45px;
                        border-radius:50%;
                        background:radial-gradient(circle,rgba(89,143,239,.18),rgba(89,143,239,0) 68%);
                        pointer-events:none;
                    }}
                    .uc-notes-card.warning::before {{ background:radial-gradient(circle,rgba(239,174,63,.19),rgba(239,174,63,0) 68%); }}
                    .uc-notes-head {{
                        position:relative;
                        z-index:1;
                        display:grid;
                        grid-template-columns:minmax(0,1fr) auto;
                        align-items:center;
                        gap:14px;
                        min-height:48px;
                    }}
                    .uc-notes-illustration {{
                        position:relative;
                        display:grid;
                        width:74px;
                        height:74px;
                        place-items:center;
                        border-radius:50%;
                        color:#4A82E7;
                        background:radial-gradient(circle at 43% 34%,#BFD9FF 0 17%,#86B5F4 44%,#5D83DD 72%,#4771CD 100%);
                        box-shadow:inset 0 2px 8px rgba(255,255,255,.45),0 9px 18px rgba(74,123,220,.18);
                        font-size:38px;
                        line-height:1;
                    }}
                    .uc-notes-illustration::before,.uc-notes-illustration::after {{
                        content:"";
                        position:absolute;
                        width:12px;
                        height:4px;
                        border-radius:999px;
                        background:#6D9AF0;
                    }}
                    .uc-notes-illustration::before {{ top:-8px; right:9px; transform:rotate(55deg); box-shadow:-29px 9px 0 #9ABAF3; }}
                    .uc-notes-illustration::after {{ top:11px; left:-7px; transform:rotate(35deg); }}
                    .uc-notes-card.warning .uc-notes-illustration {{
                        color:#FFF;
                        background:linear-gradient(145deg,#FFD77D,#EAA42B);
                        box-shadow:inset 0 2px 8px rgba(255,255,255,.48),0 9px 18px rgba(218,155,46,.18);
                        clip-path:polygon(50% 2%,98% 90%,92% 98%,8% 98%,2% 90%);
                        border-radius:0;
                        font-size:34px;
                    }}
                    .uc-notes-card.warning .uc-notes-illustration::before,.uc-notes-card.warning .uc-notes-illustration::after {{ background:#EFB54B; }}
                    .uc-notes-title {{ color:#192746; font-size:20px; font-weight:820; letter-spacing:-.035em; }}
                    .uc-notes-subtitle {{ margin-top:5px; color:#7889A6; font-size:11px; font-weight:620; line-height:1.5; }}
                    .uc-notes-count {{
                        display:grid;
                        width:38px;
                        height:38px;
                        place-items:center;
                        align-self:start;
                        border-radius:50%;
                        color:#3B72D5;
                        background:#E7F0FF;
                        font-size:14px;
                        font-weight:850;
                    }}
                    .uc-notes-card.warning .uc-notes-count {{ color:#C7831D; background:#FFF1D2; }}
                    .uc-notes-list {{ position:relative; z-index:1; display:grid; gap:11px; margin:18px 0 0; padding:0; list-style:none; }}
                    .uc-notes-list li {{ position:relative; padding-left:23px; color:#536582; font-size:12px; line-height:1.62; }}
                    .uc-notes-list li::before {{ content:""; position:absolute; top:.58em; left:1px; width:9px; height:9px; border-radius:50%; background:#4D85E9; box-shadow:0 0 0 4px rgba(77,133,233,.10); }}
                    .uc-notes-card.warning .uc-notes-list li::before {{ background:#E9A331; box-shadow:0 0 0 4px rgba(233,163,49,.11); }}
                    .uc-notes-empty {{ position:relative; z-index:1; margin-top:25px; padding:16px; border:1px dashed #C8D8F2; border-radius:13px; color:#7889A6; background:rgba(255,255,255,.66); font-size:12px; line-height:1.5; text-align:center; }}
                    .uc-notes-empty.safe {{ border-color:#D7E8D9; color:#5E8F6A; }}
                    .uc-notes-empty.safe span {{ display:inline-grid; width:20px; height:20px; place-items:center; margin-right:6px; border-radius:50%; color:#FFF; background:#79B989; font-size:12px; font-weight:800; vertical-align:middle; }}
                    @media(max-width:760px) {{
                        .uc-notes-grid {{ grid-template-columns:1fr; }}
                        .uc-notes-head {{ grid-template-columns:minmax(0,1fr) auto; gap:10px; }}
                    }}
                </style>
                <section class="uc-notes-grid">
                    <article class="uc-notes-card">
                        <div class="uc-notes-head">
                            <div><div class="uc-notes-title">Assumptions</div><div class="uc-notes-subtitle">Key assumptions used in the simulation analysis.</div></div>
                            <div class="uc-notes-count">{len(simulation_assumptions)}</div>
                        </div>
                        <ul class="uc-notes-list">{assumptions_html}</ul>
                    </article>
                    <article class="uc-notes-card warning">
                        <div class="uc-notes-head">
                            <div><div class="uc-notes-title">Warnings</div><div class="uc-notes-subtitle">Important limitations and conditions to consider.</div></div>
                            <div class="uc-notes-count">{len(simulation_warnings)}</div>
                        </div>
                        <ul class="uc-notes-list">{warnings_html}</ul>
                    </article>
                </section>
            """))
