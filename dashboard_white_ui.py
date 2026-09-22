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


def render_dashboard_ui(analysis_output=None, simulation_output=None, project_df=None, project_metrics=None, source_name=None, active_stage="analysis") -> None:
    """Display uploaded task data, Analysis Agent output, and Simulation Agent output."""
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
    .focus-card { position:relative; display:grid; grid-template-columns:auto minmax(0,1fr); gap:18px; margin:18px 0 8px; padding:22px; overflow:hidden; background:linear-gradient(115deg,#FFFFFF 0%,#F6F9FF 67%,#F3EEFF 100%); border:1px solid #DEE8F7; border-radius:18px; box-shadow:0 14px 30px rgba(27,55,97,.055); }
    .focus-card::after { content:""; position:absolute; right:-54px; top:-58px; width:170px; height:170px; border:1px solid rgba(102,119,232,.13); border-radius:50%; box-shadow:0 0 0 24px rgba(102,119,232,.035),0 0 0 48px rgba(68,190,191,.025); }
    .focus-icon { position:relative; z-index:1; display:grid; place-items:center; width:46px; height:46px; border-radius:15px; color:#FFF; background:linear-gradient(145deg,#4B88F5,#7865E7); box-shadow:0 10px 22px rgba(74,103,214,.22); font-size:19px; }
    .focus-content { position:relative; z-index:1; }
    .focus-label { color:#6F83A4; font-size:9px; font-weight:800; letter-spacing:.14em; text-transform:uppercase; }
    .focus-title { max-width:850px; margin-top:6px; color:#182641; font-size:18px; line-height:1.35; font-weight:770; letter-spacing:-.025em; }
    .focus-copy { max-width:900px; margin-top:7px; color:#71829B; font-size:11px; line-height:1.65; }
    .focus-tasks { display:flex; flex-wrap:wrap; gap:6px; margin-top:13px; }
    .focus-tasks span { padding:5px 8px; color:#536C9C; background:#EEF4FF; border:1px solid #D9E6FA; border-radius:99px; font-size:9px; font-weight:750; }
    .attention-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; margin-bottom:8px; }
    .attention-card { position:relative; min-height:150px; padding:17px 18px 16px; overflow:hidden; background:#FFF; border:1px solid #E5ECF7; border-radius:16px; box-shadow:0 10px 24px rgba(27,55,97,.04); transition:transform .18s ease,box-shadow .18s ease,border-color .18s ease; }
    .attention-card:hover { transform:translateY(-2px); border-color:#C9D9F3; box-shadow:0 14px 30px rgba(27,55,97,.075); }
    .attention-card::before { content:""; position:absolute; left:0; top:18px; bottom:18px; width:3px; border-radius:0 4px 4px 0; background:linear-gradient(#4B88F5,#8B5CF6); }
    .attention-head { display:flex; align-items:center; justify-content:space-between; gap:10px; }
    .attention-id { color:#325FC1; font-size:12px; font-weight:820; letter-spacing:.02em; }
    .attention-tags { display:flex; justify-content:flex-end; flex-wrap:wrap; gap:5px; }
    .attention-tag { padding:4px 7px; color:#6E7F98; background:#F4F7FB; border-radius:99px; font-size:8px; font-weight:760; }
    .attention-tag.blocked { color:#B45355; background:#FFF0F1; }
    .attention-tag.priority { color:#7A57B5; background:#F3EEFF; }
    .attention-summary { margin-top:13px; color:#263650; font-size:12px; line-height:1.45; font-weight:720; }
    .attention-reason { margin-top:8px; color:#7A899F; font-size:10px; line-height:1.55; }
    .attention-impact { margin-top:10px; padding-top:9px; border-top:1px solid #EEF2F7; color:#8795AA; font-size:9px; line-height:1.45; }
    .impact-layout { display:grid; grid-template-columns:minmax(0,1.35fr) minmax(280px,.65fr); gap:14px; margin:8px 0 22px; }
    .impact-panel { padding:20px; background:linear-gradient(145deg,#FFF 0%,#F8FAFF 100%); border:1px solid #E3EAF6; border-radius:18px; box-shadow:0 10px 26px rgba(27,55,97,.04); }
    .impact-panel.accent { background:linear-gradient(145deg,#172746 0%,#29447E 100%); border-color:transparent; }
    .impact-kicker { margin-bottom:5px; color:#7185A6; font-size:9px; font-weight:820; letter-spacing:.13em; text-transform:uppercase; }
    .impact-panel.accent .impact-kicker { color:#AFC9F8; }
    .impact-heading { margin-bottom:14px; color:#1E2D48; font-size:16px; font-weight:780; letter-spacing:-.025em; }
    .impact-panel.accent .impact-heading { color:#FFF; }
    .dependency-item { display:grid; grid-template-columns:minmax(72px,.7fr) 24px minmax(72px,.7fr) minmax(120px,1.35fr); align-items:center; gap:8px; padding:11px 0; border-top:1px solid #EDF2F8; }
    .dependency-item:first-of-type { border-top:0; padding-top:2px; }
    .dependency-node { padding:7px 8px; border-radius:9px; background:#EDF4FF; color:#315EBA; font-size:9px; font-weight:800; text-align:center; overflow-wrap:anywhere; }
    .dependency-node.source { background:#F2EDFF; color:#7352B8; }
    .dependency-arrow { color:#9CAFD0; font-size:15px; text-align:center; }
    .dependency-copy { color:#75869E; font-size:9px; line-height:1.5; }
    .workload-item { padding:11px 0; border-top:1px solid rgba(218,229,252,.14); }
    .workload-item:first-of-type { border-top:0; padding-top:2px; }
    .workload-person { color:#FFF; font-size:11px; font-weight:760; }
    .workload-issue { margin-top:4px; color:#C4D5F2; font-size:9px; line-height:1.5; }
    .workload-tasks { margin-top:5px; color:#8FADD9; font-size:8px; font-weight:700; }
    .impact-empty { padding:14px; color:#71829B; background:#F3F7FD; border-radius:12px; font-size:10px; line-height:1.5; }
    .impact-panel.accent .impact-empty { color:#C4D5F2; background:rgba(255,255,255,.07); }
    .data-note { display:flex; align-items:flex-start; gap:10px; margin:3px 0 18px; padding:11px 13px; color:#816A3E; background:#FFF9E9; border:1px solid #F5E9C6; border-radius:12px; font-size:10px; line-height:1.55; }
    .data-note strong { color:#6C552C; }
    .agent-note { display:flex; align-items:flex-start; gap:10px; margin:3px 0 18px; padding:13px 15px; color:#506783; background:linear-gradient(110deg,#F5F8FF,#F8F5FF); border:1px solid #DCE6FA; border-radius:14px; box-shadow:0 8px 20px rgba(41,72,139,.04); font-size:11px; line-height:1.6; }
    .agent-note > span { color:#5B72E8; font-size:14px; line-height:1.3; }
    .agent-note strong { color:#304E8B; font-size:10px; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }
    .agent-note ul { margin:7px 0 0; padding-left:17px; }
    .agent-note li + li { margin-top:4px; }
    @media(max-width:760px) { .command-deck { grid-template-columns:minmax(0,1fr) 150px; } .signal-orbit { display:block; transform:scale(.74); transform-origin:right center; } .command-copy { padding:25px; } }
    @media(max-width:580px) { .command-deck { grid-template-columns:1fr; } .signal-orbit { display:none; } }
    @media(max-width:760px) { .block-container { padding:20px 18px 52px; } .dashboard-title { font-size:26px; } .focus-card { grid-template-columns:1fr; } .attention-grid,.impact-layout { grid-template-columns:1fr; } .dependency-item { grid-template-columns:minmax(70px,1fr) 20px minmax(70px,1fr); } .dependency-copy { grid-column:1/-1; } .issue-head,.issue-row { grid-template-columns:1.15fr .9fr .9fr; } .issue-head > :nth-child(n+4),.issue-row > :nth-child(n+4) { display:none; } }
</style>
""",
        unsafe_allow_html=True,
    )

    if not analysis_output or project_df is None or len(project_df) == 0:
        st.info("No complete dashboard is available in this session. Upload your project CSV and select Analyze Project to view its results.")
        return

    if active_stage == "analysis":
        st.markdown('<div class="eyebrow">PROJECT OVERVIEW</div>', unsafe_allow_html=True)
        st.markdown('<div class="dashboard-title">Your project at a glance.</div>', unsafe_allow_html=True)
        st.caption(f"Source: {source_name or 'Uploaded project'} · {len(project_df):,} tasks analyzed")

        state = analysis_output.get("project_state")
        state_label = str(state).replace("_", " ").title() if state else ""
        confidence = analysis_output.get("confidence")
        st.markdown(
            '<div class="command-deck"><div class="command-copy">'
            '<div class="command-eyebrow">PROJECT HEALTH</div>'
            f'<div class="command-title">{html.escape(state_label)}</div>'
            + (f'<div class="command-tags"><span>Confidence: {html.escape(str(confidence).title())}</span></div>' if confidence else '')
            + '</div><div class="signal-orbit"><span class="orbit-dot one"></span><span class="orbit-dot two"></span><span class="orbit-dot three"></span><div class="orbit-core">⌁</div></div></div>',
            unsafe_allow_html=True,
        )
        warnings = list(analysis_output.get("data_warnings") or [])
        delay = analysis_output.get("estimated_delay_days")
        if warnings:
            warning_html = "<br>".join(html.escape(str(item)) for item in dict.fromkeys(warnings))
            st.markdown(
                '<div class="data-note"><span>◇</span><div><strong>Data note</strong><br>'
                f'{warning_html}</div></div>',
                unsafe_allow_html=True,
            )

        agent_notes = []
        for note in analysis_output.get("notes") or []:
            if note is not None and str(note).strip():
                agent_notes.append(str(note).strip())

        if agent_notes:
            notes_html = "".join(
                f"<li>{html.escape(note)}</li>"
                for note in dict.fromkeys(agent_notes)
            )
            st.markdown(
                '<div class="agent-note"><span>✦</span><div><strong>Project note</strong>'
                f'<ul>{notes_html}</ul></div></div>',
                unsafe_allow_html=True,
            )

        if delay is not None:
            st.caption(f"Estimated project delay: {delay:g} days")

        signals = analysis_output.get("schedule_signals") or {}
        overview = [
            ("Blocked tasks", signals.get("blocked_tasks"), ""),
            ("Overdue tasks", signals.get("overdue_tasks"), ""),
            ("High-priority unfinished", signals.get("unfinished_high_priority_tasks"), ""),
        ]
        available_overview = [item for item in overview if item[1] is not None]
        if available_overview:
            for column, (label, value, note) in zip(st.columns(len(available_overview)), available_overview):
                with column:
                    metric_card(label, value, note)

        root = analysis_output.get("root_cause") or {}
        if root:
            root_summary = root.get("summary")
            root_explanation = root.get("explanation")
            affected_tasks = root.get("affected_tasks") or []
            affected_html = "".join(
                f"<span>{html.escape(str(task))}</span>"
                for task in affected_tasks[:8]
            )
            st.markdown(
                '<div class="focus-card">'
                '<div class="focus-icon">⌁</div>'
                '<div class="focus-content">'
                '<div class="focus-label">Primary focus</div>'
                + (f'<div class="focus-title">{html.escape(str(root_summary))}</div>' if root_summary else '')
                + (f'<div class="focus-copy">{html.escape(str(root_explanation))}</div>' if root_explanation else '')
                + (f'<div class="focus-tasks">{affected_html}</div>' if affected_html else '')
                + '</div></div>',
                unsafe_allow_html=True,
            )

        # Combine duplicate task references for presentation only; retain agent order.
        attention = {}
        for item in analysis_output.get("bottlenecks") or []:
            key = item.get("task_id")
            if not key:
                continue
            attention[key] = {
                "Task": key,
                "Summary": item.get("summary"),
                "Why it matters": item.get("reason"),
                "Impact": item.get("impact"),
                "Status": item.get("status"),
                "Priority": item.get("priority"),
            }
        for item in analysis_output.get("critical_tasks") or []:
            key = item.get("task_id")
            if key and key not in attention:
                attention[key] = {
                    "Task": key,
                    "Summary": item.get("reason"),
                    "Why it matters": None,
                    "Impact": None,
                    "Status": None,
                    "Priority": None,
                }
        if attention:
            st.markdown('<div class="section-name">Tasks needing attention</div>', unsafe_allow_html=True)
            cards = []
            for item in list(attention.values())[:5]:
                tags = []
                if item.get("Status"):
                    status_class = " blocked" if str(item["Status"]).strip().lower() == "blocked" else ""
                    tags.append(
                        f'<span class="attention-tag{status_class}">{html.escape(str(item["Status"]))}</span>'
                    )
                if item.get("Priority"):
                    tags.append(
                        f'<span class="attention-tag priority">{html.escape(str(item["Priority"]))}</span>'
                    )
                summary = item.get("Summary") or item.get("Why it matters")
                cards.append(
                    '<article class="attention-card">'
                    '<div class="attention-head">'
                    f'<div class="attention-id">{html.escape(str(item["Task"]))}</div>'
                    f'<div class="attention-tags">{"".join(tags)}</div>'
                    '</div>'
                    + (f'<div class="attention-summary">{html.escape(str(summary))}</div>' if summary else '')
                    + (f'<div class="attention-reason">{html.escape(str(item["Why it matters"]))}</div>' if item.get("Why it matters") and item.get("Why it matters") != summary else '')
                    + (f'<div class="attention-impact">Impact · {html.escape(str(item["Impact"]))}</div>' if item.get("Impact") else '')
                    + '</article>'
                )
            st.markdown(
                f'<div class="attention-grid">{"".join(cards)}</div>',
                unsafe_allow_html=True,
            )
            if len(attention) > 5:
                st.caption(f"Showing 5 of {len(attention)} tasks returned by the Analysis Agent.")

        dependencies = list(analysis_output.get("dependencies") or [])
        workload = list(analysis_output.get("workload_signals") or [])

        dependency_items = []
        for item in dependencies[:4]:
            blocked = item.get("blocked_task")
            source = item.get("depends_on")
            impact = item.get("impact")
            if not blocked or not source:
                continue
            dependency_items.append(
                '<div class="dependency-item">'
                f'<div class="dependency-node">{html.escape(str(blocked))}</div>'
                '<div class="dependency-arrow">←</div>'
                f'<div class="dependency-node source">{html.escape(str(source))}</div>'
                + (f'<div class="dependency-copy">{html.escape(str(impact))}</div>' if impact else '')
                + '</div>'
            )

        workload_items = []
        for item in workload[:3]:
            assignee = item.get("assignee")
            issue = item.get("issue")
            if not issue:
                continue
            related = item.get("related_tasks") or []
            related_text = ", ".join(map(str, related[:5]))
            workload_items.append(
                '<div class="workload-item">'
                + (f'<div class="workload-person">{html.escape(str(assignee))}</div>' if assignee else '')
                + f'<div class="workload-issue">{html.escape(str(issue))}</div>'
                + (f'<div class="workload-tasks">Related · {html.escape(related_text)}</div>' if related_text else '')
                + '</div>'
            )

        impact_panels = []
        if dependency_items:
            impact_panels.append(
                '<section class="impact-panel">'
                '<div class="impact-kicker">FLOW AT RISK</div>'
                '<div class="impact-heading">Dependencies holding work back</div>'
                f'{"".join(dependency_items)}'
                '</section>'
            )
        if workload_items:
            impact_panels.append(
                '<section class="impact-panel accent">'
                '<div class="impact-kicker">TEAM SIGNAL</div>'
                '<div class="impact-heading">Workload to watch</div>'
                f'{"".join(workload_items)}'
                '</section>'
            )
        if impact_panels:
            st.markdown(
                '<div class="section-name">Project impact map</div>'
                f'<div class="impact-layout">{"".join(impact_panels)}</div>',
                unsafe_allow_html=True,
            )


        with st.expander("Explore project data", expanded=False):
            st.caption("Filters apply only to the data below. Analysis and recovery findings describe the full project.")
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
                stats = [
                    ("Total issues", len(filtered), "Tasks matching your filters"),
                    ("Resolved work", metrics.get("resolved_issues") if known_resolution else None, "Known completion signals"),
                ]
                for column, (label, value, note) in zip(st.columns(2), stats):
                    with column:
                        metric_card(label, value, note)
                for container, field, title, color in zip(st.columns(2), ("status", "priority"), ("Issue status", "Priority mix"), ("#4B88F5", "#8B5CF6")):
                    with container:
                        render_distribution(filtered, field, title, color)
                render_distribution(filtered, "assignee_id", "Tasks per assignee", "#4B88F5")
                st.markdown('<div class="section-name">Issue register</div>', unsafe_allow_html=True)
                labels = {"issue_key": "Issue", "issue_id": "ID", "text": "Task details", "priority": "Priority", "status": "Status", "assignee_id": "Assignee", "creation_date": "Created", "due_date": "Due", "resolution_date": "Resolved"}
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
                    + (f'<span class="uc-strategy-status">{_esc(status)}</span>' if status else '')
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

            summary_cards_html = ""
            if explanation:
                summary_cards_html += (
                    '<div class="uc-side-card">'
                    '<div class="uc-side-title"><span>◉</span>Simulation conclusion</div>'
                    f'<div class="uc-side-copy">{_esc(explanation)}</div>'
                    '</div>'
                )
            if recovery_plan_summary:
                summary_cards_html += (
                    '<div class="uc-side-card recommended">'
                    '<div class="uc-side-title"><span class="blue">◎</span>Recommended direction</div>'
                    f'<div class="uc-side-copy">{_esc(recovery_plan_summary)}</div>'
                    '</div>'
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
                    + (f'<span class="uc-strategy-status">{_esc(selected_status)}</span>' if selected_status else '')
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
                        roadmap_html += f"""
                            <div class="uc-flow-card">
                                <div class="uc-task-id">{_esc(task_id)}</div>
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

            # st.html renders raw HTML directly, avoiding Markdown parsing
            # that can turn nested/indented HTML into visible code blocks.
            st.html(textwrap.dedent(f"""
                <style>
                    .block-container {{
                        max-width: 1480px !important;
                        padding: 24px 36px 72px !important;
                    }}
                    .stApp {{
                        background: #F8FAFE !important;
                        color: #16223B !important;
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
                        position: relative;
                        display: grid;
                        grid-template-columns: 1fr;
                        gap: 32px;
                        overflow: hidden;
                        padding: 30px;
                        border-radius: 24px;
                        background: linear-gradient(128deg,#142542 0%,#29477F 58%,#514096 100%);
                        box-shadow: 0 24px 50px rgba(29,49,96,.16);
                    }}

                    .uc-top-grid::before {{
                        content: "";
                        position: absolute;
                        inset: 0;
                        opacity: .22;
                        background-image: linear-gradient(rgba(255,255,255,.13) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.13) 1px,transparent 1px);
                        background-size: 30px 30px;
                        mask-image: linear-gradient(90deg,#000,transparent 78%);
                        pointer-events: none;
                    }}

                    .uc-top-grid .uc-right {{
                        display: grid;
                        grid-template-columns: repeat(2, minmax(0, 1fr));
                        gap: 16px;
                    }}

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
                        transform: translateY(-4px);
                        border-color: #A9C4EE;
                        box-shadow: 0 12px 26px rgba(27,55,97,.08);
                    }}

                    .uc-task-id {{
                        display: inline-flex;
                        padding: 2px 8px;
                        margin-bottom: 8px;
                        border: 1px solid #E5ECF7;
                        border-radius: 5px;
                        background: #F3F7FC;
                        color: #5F718B;
                        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
                        font-size: 11px;
                        font-weight: 800;
                    }}

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

                    @media (max-width: 1100px) {{
                        .uc-top-grid {{
                            grid-template-columns: 1fr;
                        }}
                        .uc-right {{
                            display: grid;
                            grid-template-columns: repeat(2,minmax(0,1fr));
                        }}
                    }}

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
                            <h2 class="uc-roadmap-title">
                                <span style="color:#2563EB">⑂</span>
                                Recovery Execution Order
                            </h2>
                            <div class="uc-flow-scroll">
                                <div class="uc-flow">
                                    {roadmap_html}
                                </div>
                            </div>

                            {f'<div class="uc-order-note">{_esc(recovery_order_reason)}</div>' if recovery_order_reason else ''}
                        </section>
                    </main>
                </div>
                """).strip())

            simulation_assumptions = simulation_output.get("assumptions") or []
            simulation_warnings = simulation_output.get("warnings") or []

            with st.expander("Simulation assumptions and warnings", expanded=False):
                if simulation_assumptions:
                    st.write("Assumptions")
                    for assumption in simulation_assumptions:
                        st.write("• " + str(assumption))
                if simulation_warnings:
                    st.write("Warnings")
                    for warning in simulation_warnings:
                        st.write("• " + str(warning))
