import io
import logging
import hashlib
import json
from pathlib import Path
from time import perf_counter
import pandas as pd

#from pipeline.pipeline import run_analysis
import html
import importlib

import streamlit as st

import dashboard_white_ui


MAX_UPLOAD_BYTES = 10 * 1024 * 1024
DEV_PREVIEW = False  # Set to True to enable local development preview of the last successful analysis
DEV_STATE_PATH = Path(__file__).with_name(".under_control_dev_state.json")


def clear_uploaded_file():
    """Rebuild the native uploader empty when the user removes a file."""
    st.session_state["uploader_version"] = st.session_state.get("uploader_version", 0) + 1
    clear_analysis_result()
    st.session_state.pop("uploaded_fingerprint", None)
    if DEV_PREVIEW:
        DEV_STATE_PATH.unlink(missing_ok=True)


def clear_analysis_result():
    for key in (
        "analysis_output",
        "simulation_output",
        "project_dataframe",
        "analyzed_filename",
    ):
        st.session_state.pop(key, None)
    for key in ("dashboard_project", "dashboard_status", "dashboard_priority"):
        st.session_state.pop(key, None)


def save_dev_preview(analysis_result, simulation_result, project_dataframe, filename):
    """Persist the latest successful result for local UI development."""
    if not DEV_PREVIEW:
        return
    payload = {
        "analysis_output": analysis_result,
        "simulation_output": simulation_result,
        "project_dataframe": project_dataframe.to_json(orient="split", date_format="iso"),
        "analyzed_filename": filename,
    }
    temporary_path = DEV_STATE_PATH.with_suffix(".tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    temporary_path.replace(DEV_STATE_PATH)


def restore_dev_preview():
    """Restore the last result unless the user explicitly opened Upload."""
    if not DEV_PREVIEW or st.session_state.get("analysis_output"):
        return
    if st.query_params.get("view") == "upload" or not DEV_STATE_PATH.exists():
        return
    try:
        payload = json.loads(DEV_STATE_PATH.read_text(encoding="utf-8"))
        project_dataframe = pd.read_json(
            io.StringIO(payload["project_dataframe"]),
            orient="split",
        )
        st.session_state["analysis_output"] = payload["analysis_output"]
        st.session_state["simulation_output"] = payload["simulation_output"]
        st.session_state["project_dataframe"] = project_dataframe
        st.session_state["analyzed_filename"] = payload.get("analyzed_filename", "Development preview")
        st.query_params["view"] = "analysis"
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        logging.getLogger(__name__).exception("Could not restore the development preview")
        DEV_STATE_PATH.unlink(missing_ok=True)


def read_uploaded_csv(uploaded_file):
    """Read a user-uploaded CSV with common encodings and delimiter detection."""
    file_bytes = uploaded_file.getvalue()

    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = file_bytes.decode(encoding)
            dataframe = pd.read_csv(
                io.StringIO(text),
                sep=",",
                engine="python",
            )

            dataframe = dataframe.replace(r"^\s*$", pd.NA, regex=True).dropna(how="all")
            if dataframe.empty:
                raise ValueError("The uploaded CSV contains no data.")

            return dataframe

        except UnicodeDecodeError:
            continue
        except (pd.errors.ParserError, pd.errors.EmptyDataError, pd.errors.ParserWarning):
            continue

    raise ValueError(
        "The CSV file could not be read. Please upload a valid project CSV file."
    )



def render_route_transition_overlay():
    """Cover the old Upload DOM while Streamlit builds the Analysis page."""
    st.markdown(
        """
        <style>
        .uc-route-transition {
            position: fixed;
            inset: 0;
            z-index: 999999;
            display: flex;
            align-items: center;
            justify-content: center;
            background:
                linear-gradient(118deg, rgba(94,130,235,.08) 0%, rgba(94,130,235,0) 24%),
                linear-gradient(302deg, rgba(157,122,224,.08) 0%, rgba(157,122,224,0) 25%),
                radial-gradient(ellipse at 50% 22%, rgba(255,255,255,.99) 0%, rgba(255,255,255,.90) 42%, rgba(247,248,252,.96) 100%);
            opacity: 1;
            transition: opacity .18s ease;
            pointer-events: all;
        }

        .uc-route-transition__card {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 12px;
            padding: 24px 28px;
            border: 1px solid rgba(215,219,240,.78);
            border-radius: 22px;
            background: rgba(255,255,255,.78);
            box-shadow: 0 20px 54px rgba(77,83,155,.10);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }

        .uc-route-transition__mark {
            width: 42px;
            height: 42px;
            display: grid;
            place-items: center;
            border-radius: 14px;
            color: #FFFFFF;
            font-size: 19px;
            font-weight: 800;
            background: linear-gradient(135deg,#6678E8 0%,#7A67DF 100%);
            box-shadow: 0 10px 24px rgba(102,120,232,.20);
        }

        .uc-route-transition__title {
            color: #18223C;
            font-size: 16px;
            font-weight: 750;
            line-height: 1.25;
        }

        .uc-route-transition__text {
            color: #8793AA;
            font-size: 12px;
            line-height: 1.5;
        }
        </style>

        <div class="uc-route-transition" id="uc-route-transition">
            <div class="uc-route-transition__card">
                <div class="uc-route-transition__mark">✓</div>
                <div class="uc-route-transition__title">Analysis ready</div>
                <div class="uc-route-transition__text">Opening your project view…</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hide_route_transition_overlay():
    """Fade the transition cover only after the dashboard has finished rendering."""
    st.markdown(
        """
        <style>
        #uc-route-transition {
            opacity: 0 !important;
            pointer-events: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# PAGE CONFIGURATION
# =========================================================

def render_workflow_navigation():
    stages = ("upload", "analysis", "simulation")
    selected = st.query_params.get("view", "upload")
    if selected == "dashboard":
        selected = "analysis"
    available = (True, bool(st.session_state.get("analysis_output")) and st.session_state.get("project_dataframe") is not None,
                 bool(st.session_state.get("simulation_output")) and st.session_state.get("project_dataframe") is not None)
    if selected not in stages or not available[stages.index(selected)]:
        selected = "upload"
    st.query_params["view"] = selected
    current = stages.index(selected)

    def navigate(destination):
        st.query_params["view"] = destination

    st.markdown("""<style>
    .workflow-brand {text-align:center;color:#345EE9;font-size:clamp(22px,3vw,26px);font-weight:750;line-height:1.3;letter-spacing:.08em;margin:4px 0 24px;}
    .st-key-workflow_navigation {max-width:740px;margin:0 auto 22px;padding:0;
        border:none!important;border-radius:0!important;background:transparent!important;box-shadow:none!important;}
    .st-key-workflow_navigation [data-testid="stHorizontalBlock"] {align-items:flex-start;gap:8px;
        flex-wrap:nowrap;background:none;}
    .st-key-workflow_navigation [data-testid="stColumn"] {position:relative;}
    .st-key-workflow_navigation [data-testid="stColumn"]:nth-child(2)::after,
    .st-key-workflow_navigation [data-testid="stColumn"]:nth-child(3)::after {content:"";position:absolute;top:17px;left:50%;width:calc(100% + 8px);height:1px;background:#DEE6F3;pointer-events:none;}
    .st-key-workflow_navigation [data-testid="stElementContainer"]:has(button) {width:100%!important;}
    .st-key-workflow_navigation [data-testid="stButton"] {width:100%;position:relative;z-index:1;}
    .st-key-workflow_navigation [data-testid="stButton"] button {
        width:100%!important;min-height:66px!important;margin:0!important;padding:0!important;
        display:flex!important;flex-direction:column;gap:8px!important;justify-content:flex-start!important;
        border:0!important;border-radius:0!important;background:transparent!important;
        box-shadow:none!important;color:#718099!important;opacity:1!important;}
    .st-key-workflow_navigation [data-testid="stButton"] button::before {
        content:"";display:block;flex-shrink:0;width:12px;height:12px;margin-top:11px;
        border-radius:50%;background:#CDD8EA;border:2px solid #F7F9FE;box-shadow:none;}
    .st-key-workflow_navigation [data-testid="stButton"] button[kind="primary"]::before {
        background:#5879E2;border-color:#EDF2FF;box-shadow:0 0 0 3px #5879E210;}
    .st-key-workflow_navigation [data-testid="stButton"] button[kind="primary"] {color:#4F6ED0!important;}
    .st-key-workflow_navigation [data-testid="stButton"] button p {font-size:13px!important;font-weight:500!important;}
    .st-key-workflow_navigation [data-testid="stButton"] button:disabled {color:#8795AB!important;}
    .st-key-workflow_navigation [data-testid="stButton"] button:disabled::before {background:#E0E6F1;box-shadow:0 0 0 1px #D5DEEE;}
    .st-key-workflow_navigation [data-testid="stButton"] button:focus-visible {outline:2px solid #345EE9!important;outline-offset:4px;}
    .st-key-workflow_navigation .st-key-workflow_previous button,
    .st-key-workflow_navigation .st-key-workflow_next button {
        width:36px!important;height:36px!important;min-height:36px!important;margin:0 auto!important;
        border:0!important;border-radius:0!important;justify-content:center!important;
        color:#4F6ED0!important;background:transparent!important;}
    .st-key-workflow_navigation .st-key-workflow_previous button::before,
    .st-key-workflow_navigation .st-key-workflow_next button::before {display:none!important;}
    .st-key-workflow_navigation .st-key-workflow_previous button p,
    .st-key-workflow_navigation .st-key-workflow_next button p {font-size:22px!important;font-weight:400!important;line-height:1!important;}
    .st-key-workflow_navigation .st-key-workflow_previous button:disabled,
    .st-key-workflow_navigation .st-key-workflow_next button:disabled {color:#8395B5!important;border-color:#CDD8EA!important;}
    @media(max-width:600px) {
        .st-key-workflow_navigation [data-testid="stHorizontalBlock"] {gap:2px;}
        .st-key-workflow_navigation [data-testid="stButton"] button p {font-size:12px!important;}
        .st-key-workflow_navigation .st-key-workflow_previous button,
        .st-key-workflow_navigation .st-key-workflow_next button {width:34px!important;height:36px!important;min-height:36px!important;}}
    </style><div class="workflow-brand">UNDER CONTROL</div>""", unsafe_allow_html=True)
    with st.container(key="workflow_navigation"):
        columns = st.columns([.4, 1, 1, 1, .4])
        with columns[0]:
            st.button("←", key="workflow_previous", help="Previous stage", disabled=current == 0,
                      on_click=navigate, args=(stages[max(0, current - 1)],))
        for i, (name, label) in enumerate(zip(stages, ("Upload", "Analysis", "Simulation"))):
            with columns[i + 1]:
                st.button(label, key=f"workflow_{name}", disabled=not available[i],
                          type="primary" if current == i else "secondary", on_click=navigate, args=(name,))
        with columns[4]:
            next_index = min(2, current + 1)
            st.button("→", key="workflow_next", help="Next stage", disabled=current == 2 or not available[next_index],
                      on_click=navigate, args=(stages[next_index],))
    return selected


st.set_page_config(
    page_title="Under Control",
    layout="centered",
    initial_sidebar_state="collapsed"
)

restore_dev_preview()

_route_transition_target = st.session_state.get("route_transition_target")
if (
    _route_transition_target == "analysis"
    and st.query_params.get("view") == "analysis"
):
    render_route_transition_overlay()

active_stage = render_workflow_navigation()
if active_stage in ("analysis", "simulation"):
    importlib.reload(dashboard_white_ui)
    dashboard_white_ui.render_dashboard_ui(
        analysis_output=st.session_state.get("analysis_output"),
        simulation_output=st.session_state.get("simulation_output"),
        project_df=st.session_state.get("project_dataframe"),
        source_name=st.session_state.get("analyzed_filename"),
        active_stage=active_stage,
    )
    if _route_transition_target == active_stage:
        hide_route_transition_overlay()
        st.session_state.pop("route_transition_target", None)
    st.stop()


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
<style>

    /* =========================
       GLOBAL
       ========================= */

    .stApp {
        background-color: #FFFFFF;
    }

    .block-container {
        max-width: 820px;
        padding-top: 22px;
        padding-bottom: 70px;
    }

    header {
        visibility: hidden;
    }


    /* =========================
       BRAND
       ========================= */

    .brand {
        text-align: center;
        color: #2563EB;
        font-size: 22px;
        font-weight: 700;
        letter-spacing: 0.5px;
        margin-bottom: 55px;
    }


    /* =========================
       TITLE
       ========================= */

    .main-title {
        text-align: center;
        color: #172033;
        font-size: 32px;
        font-weight: 700;
        letter-spacing: -0.7px;
        margin: 0;
    }

    .subtitle {
        text-align: center;
        color: #4B5563;
        font-size: 15px;
        line-height: 1.6;
        max-width: 620px;
        margin: 12px auto 38px auto;
    }


    /* =========================
       UPLOAD CARD
       ========================= */

    .upload-card {
        background-color: #F8FAFF;
        border: 1.5px dashed #B9D2FF;
        border-radius: 18px;
        min-height: 250px;
        text-align: center;
        padding: 45px 30px 40px 30px;
        box-sizing: border-box;
    }

    .upload-icon {
        width: 58px;
        height: 58px;

        display: flex;
        align-items: center;
        justify-content: center;

        background-color: #EAF2FF;
        color: #2563EB;

        border-radius: 15px;

        font-size: 28px;
        font-weight: 600;

        margin: 0 auto 18px auto;
    }

    .upload-title {
        color: #172033;
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 7px;
    }

    .upload-description {
        color: #94A3B8;
        font-size: 14px;
    }


    /* =========================
       STREAMLIT UPLOADER
       ========================= */

    div[data-testid="stFileUploader"] {
        margin-top: -105px;
        margin-bottom: 25px;
        position: relative;
        z-index: 5;
    }

    div[data-testid="stFileUploader"] section {
        background-color: transparent;
        border: none;
    }

    div[data-testid="stFileUploader"] small {
        display: none;
    }

    div[data-testid="stFileUploader"] button {
        border: 1px solid #D9E6FF;
        border-radius: 9px;
        background-color: #FFFFFF;
        color: #2563EB;
        font-weight: 600;
        padding: 7px 17px;
    }

    div[data-testid="stFileUploader"] button:hover {
        border-color: #2563EB;
        color: #2563EB;
        background-color: #FFFFFF;
    }


    /* =========================
       REQUIREMENTS
       ========================= */

    .requirements {
        text-align: center;
        color: #94A3B8;
        font-size: 12px;
        margin-top: 12px;
        margin-bottom: 28px;
    }


    /* =========================
       FILE INFORMATION
       ========================= */

    .file-info {
        display: flex;
        align-items: center;

        width: 100%;

        background-color: #FFFFFF;
        border: 1px solid #D9E6FF;
        border-radius: 14px;

        padding: 15px 18px;
        box-sizing: border-box;

        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.06);

        margin-top: 5px;
    }

    .file-icon {
        width: 42px;
        height: 42px;

        display: flex;
        align-items: center;
        justify-content: center;

        background-color: #EAF2FF;
        color: #2563EB;

        border-radius: 10px;

        font-size: 20px;

        margin-right: 13px;
        flex-shrink: 0;
    }

    .file-name {
        color: #172033;
        font-size: 14px;
        font-weight: 600;
        text-align: left;
    }

    .file-size {
        color: #94A3B8;
        font-size: 12px;
        margin-top: 3px;
        text-align: left;
    }

    .file-status {
        margin-left: auto;
        color: #16A34A;
        font-size: 13px;
        font-weight: 600;
    }

    /* Use Streamlit's actual drop zone as the card, not a separate visual overlay. */
    .upload-card { display: none; }

    div[data-testid="stFileUploader"] {
        margin: 0;
    }

    div[data-testid="stFileUploader"] section {
        min-height: 278px;
        padding: 32px 28px;
        background: #F4F8FF;
        border: 1.5px dashed #B9D2FF;
        border-radius: 20px;
        transition: background 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
    }

    div[data-testid="stFileUploader"] section:hover {
        background: #F8FBFF;
        border-color: #2563EB;
        box-shadow: 0 12px 30px rgba(37, 99, 235, 0.08);
    }

    div[data-testid="stFileUploaderDropzoneInstructions"] {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 9px;
    }

    div[data-testid="stFileUploaderDropzoneInstructions"] > div:first-child {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 64px;
        height: 64px;
        margin-bottom: 7px;
        background: #E7F0FF;
        border: 1px solid #D5E5FF;
        border-radius: 16px;
        color: #2563EB;
    }

    div[data-testid="stFileUploaderDropzoneInstructions"] svg {
        width: 31px;
        height: 31px;
    }

    div[data-testid="stFileUploaderDropzoneInstructions"] span,
    div[data-testid="stFileUploaderDropzoneInstructions"] small {
        color: #172033 !important;
        font-size: 17px !important;
        font-weight: 650 !important;
    }

    div[data-testid="stFileUploaderDropzoneInstructions"] small {
        color: #64748B !important;
        font-size: 13px !important;
        font-weight: 400 !important;
    }

    div[data-testid="stFileUploader"] button {
        padding: 8px 17px;
        background: #FFFFFF;
        border: 1px solid #C8DCFF;
        border-radius: 9px;
        box-shadow: 0 2px 5px rgba(37, 99, 235, 0.05);
        color: #2563EB;
        font-size: 14px;
        font-weight: 650;
    }

    div[data-testid="stFileUploader"] button:hover {
        color: #FFFFFF;
        background: #2563EB;
        border-color: #2563EB;
    }

    div[data-testid="stFileUploader"] button:focus-visible {
        outline: 3px solid rgba(37, 99, 235, 0.22);
        outline-offset: 2px;
    }

    .selected-file {
        display: flex;
        align-items: center;
        gap: 13px;
        padding: 15px 17px;
        background: #FFFFFF;
        border: 1px solid #D8E6FC;
        border-radius: 14px;
        box-shadow: 0 8px 22px rgba(37, 99, 235, 0.07);
    }

    .file-badge {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 42px;
        height: 42px;
        flex: 0 0 auto;
        background: #EAF2FF;
        border-radius: 10px;
        color: #2563EB;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.04em;
    }

    .file-meta { min-width: 0; }
    .file-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

    @media (max-width: 540px) {
        .block-container { padding: 44px 20px 56px; }
        .brand { margin-bottom: 38px; }
        div[data-testid="stFileUploader"] section { min-height: 250px; padding: 25px 18px; }
        .file-status { display: none; }
    }

    /* Layout hooks for the current Streamlit uploader markup. */
    div[data-testid="stFileUploader"] > label { display: none; }
    div[data-testid="stFileUploader"] section {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 12px;
    }
    div[data-testid="stFileUploader"] section::before {
        content: "";
        order: 1;
        width: 64px;
        height: 64px;
        border: 1px solid #D5E5FF;
        border-radius: 16px;
        background: #E7F0FF url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 24 24' fill='none' stroke='%232563EB' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 16V3'/%3E%3Cpath d='m7 8 5-5 5 5'/%3E%3Cpath d='M4 15v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4'/%3E%3C/svg%3E") center/32px 32px no-repeat;
    }
    div[data-testid="stFileUploader"] section::after {
        content: "Drop your CSV file here\\A Drag and drop it here, or browse from your computer";
        order: 2;
        color: #172033;
        font-size: 17px;
        font-weight: 650;
        line-height: 1.75;
        text-align: center;
        white-space: pre-line;
    }
    div[data-testid="stFileUploader"] section > span { order: 3; }
    div[data-testid="stFileUploaderDropzoneInstructions"] {
        display: block;
        order: 4;
    }
    div[data-testid="stFileUploaderDropzoneInstructions"] > div:first-child {
        display: block;
        width: auto;
        height: auto;
        margin: 0;
        background: transparent;
        border: 0;
    }
    div[data-testid="stFileUploaderDropzoneInstructions"] span {
        color: #64748B !important;
        font-size: 12px !important;
        font-weight: 400 !important;
    }

    /* Shared Aurora application canvas: same visual treatment as Analysis/Simulation. */
    html, body, [class*="css"] {
        font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .stApp {
        background:
            linear-gradient(118deg, rgba(94,130,235,.085) 0%, rgba(94,130,235,0) 24%),
            linear-gradient(302deg, rgba(157,122,224,.085) 0%, rgba(157,122,224,0) 25%),
            radial-gradient(ellipse at 50% 18%, rgba(255,255,255,.98) 0%, rgba(255,255,255,.74) 34%, rgba(255,255,255,0) 68%),
            linear-gradient(180deg,#F8F9FD 0%,#F5F7FC 55%,#F7F8FC 100%);
        background-attachment: fixed;
        background-repeat: no-repeat;
    }

    .stApp::before,
    .stApp::after {
        content: "";
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

    .stApp > div {
        position: relative;
        z-index: 1;
    }
    .brand { font-size:14px; }
    .main-title { font-size:38px; }
    .subtitle { font-size:17px; line-height:1.65; }
    div[data-testid="stFileUploaderDropzoneInstructions"] span { font-size:14px !important; line-height:1.55 !important; }
    .upload-note { font-size:12px; }
    .intake-kicker { font-size:11px; }
    .analysis-motion-title { font-size:17px; }
    .analysis-motion-detail { font-size:13px; }

    .brand {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 9px;
        font-size: 12px;
        letter-spacing: 0.16em;
    }

    .brand::before {
        content: "";
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #2563EB;
        box-shadow: 0 0 0 5px rgba(37, 99, 235, 0.10);
    }

    div[data-testid="stFileUploader"] section::before {
        box-shadow: 0 10px 22px rgba(37, 99, 235, 0.10);
    }

    .upload-notes {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 8px;
        margin: -8px 0 30px;
    }

    .upload-note {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 7px 10px;
        background: rgba(255, 255, 255, 0.78);
        border: 1px solid #E1EBFA;
        border-radius: 999px;
        color: #64748B;
        font-size: 11px;
        font-weight: 600;
    }

    .upload-note strong { color: #2563EB; font-size: 12px; }

    .selected-file { position: relative; overflow: hidden; }
    .selected-file::after {
        content: "";
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 4px;
        background: #2563EB;
    }

    /* A light data-grid and floating mark give the drop zone more character. */
    div[data-testid="stFileUploader"] section {
        position: relative;
        overflow: hidden;
        background-color: #F5F9FF;
        background-image:
            linear-gradient(rgba(37, 99, 235, 0.035) 1px, transparent 1px),
            linear-gradient(90deg, rgba(37, 99, 235, 0.035) 1px, transparent 1px),
            radial-gradient(circle at 14% 88%, rgba(191, 219, 254, 0.42), transparent 10rem),
            radial-gradient(circle at 88% 12%, rgba(219, 234, 254, 0.72), transparent 12rem);
        background-size: 28px 28px, 28px 28px, auto, auto;
    }

    div[data-testid="stFileUploader"] section > * { position: relative; z-index: 1; }

    div[data-testid="stFileUploader"] section::before {
        width: 72px;
        height: 72px;
        border-radius: 22px;
        background-size: 34px 34px;
        animation: float-upload-mark 3.6s ease-in-out infinite;
    }

    div[data-testid="stFileUploader"] section::after {
        text-shadow: 0 1px 0 #FFFFFF;
    }

    @keyframes float-upload-mark {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-5px); }
    }

    .workflow {
        display: grid;
        grid-template-columns: 1fr auto 1fr auto 1fr;
        align-items: center;
        gap: 10px;
        max-width: 510px;
        margin: 0 auto;
        padding: 15px 18px;
        background: rgba(255, 255, 255, 0.76);
        border: 1px solid #E3EDF9;
        border-radius: 17px;
        box-shadow: 0 10px 28px rgba(37, 99, 235, 0.045);
    }

    .workflow-step { min-width: 0; text-align: center; }
    .workflow-icon {
        display: grid;
        place-items: center;
        width: 27px;
        height: 27px;
        margin: 0 auto 6px;
        border-radius: 9px;
        background: #EAF2FF;
        color: #2563EB;
        font-size: 12px;
        font-weight: 800;
    }
    .workflow-step:first-child .workflow-icon { background: #2563EB; color: #FFFFFF; }
    .workflow-title { color: #172033; font-size: 11px; font-weight: 750; }
    .workflow-caption { color: #94A3B8; font-size: 10px; margin-top: 2px; }
    .workflow-line { width: 26px; height: 1px; background: #CFE0FA; }

    @media (max-width: 540px) {
        .workflow { gap: 6px; padding: 13px 10px; }
        .workflow-line { width: 12px; }
        .workflow-caption { display: none; }
    }

    /* Signature “data intake” treatment for the hero upload interaction. */
    .intake-kicker {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 9px;
        margin: -24px 0 26px;
        color: #6B86B1;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 0.15em;
        text-transform: uppercase;
    }
    .intake-kicker::before,
    .intake-kicker::after {
        content: "";
        width: 28px;
        height: 1px;
        background: linear-gradient(90deg, transparent, #A8C7F7);
    }
    .intake-kicker::after { transform: scaleX(-1); }

    div[data-testid="stFileUploader"] {
        position: relative;
        padding: 10px 0;
    }
    div[data-testid="stFileUploader"]::before,
    div[data-testid="stFileUploader"]::after {
        position: absolute;
        z-index: 3;
        top: 28px;
        color: #7294C6;
        font-size: 9px;
        font-weight: 800;
        letter-spacing: 0.13em;
        pointer-events: none;
    }
    div[data-testid="stFileUploader"]::before { content: "DATA INTAKE"; left: 25px; }
    div[data-testid="stFileUploader"]::after { content: "01 / CSV"; right: 25px; }

    div[data-testid="stFileUploader"] section {
        border-color: #AACBFC;
        box-shadow: 0 24px 60px rgba(37, 99, 235, 0.13), inset 0 1px 0 rgba(255,255,255,.9);
        animation: blueprint-glow 4s ease-in-out infinite;
    }
    @keyframes blueprint-glow {
        0%, 100% { box-shadow: 0 24px 60px rgba(37, 99, 235, 0.11), inset 0 1px 0 rgba(255,255,255,.9); }
        50% { box-shadow: 0 28px 70px rgba(37, 99, 235, 0.19), inset 0 1px 0 rgba(255,255,255,.96); }
    }

    div[data-testid="stFileUploader"] section::before {
        width: 76px;
        height: 76px;
        border: 0;
        border-radius: 25px;
        background-color: #2563EB;
        background-image:
            linear-gradient(145deg, rgba(255,255,255,.26), transparent 45%),
            url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='36' height='36' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 16V3'/%3E%3Cpath d='m7 8 5-5 5 5'/%3E%3Cpath d='M4 15v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4'/%3E%3C/svg%3E");
        background-position: center;
        background-repeat: no-repeat;
        box-shadow: 0 13px 25px rgba(37, 99, 235, .28), 0 0 0 8px rgba(37, 99, 235, .07);
    }

    div[data-testid="stFileUploader"] button {
        position: relative;
        overflow: hidden;
        padding: 10px 20px;
        color: #FFFFFF;
        background: linear-gradient(135deg, #2563EB, #1746B5);
        border-color: #2563EB;
        box-shadow: 0 10px 20px rgba(37, 99, 235, .22);
        transition: transform .18s ease, box-shadow .18s ease;
    }
    div[data-testid="stFileUploader"] button::after {
        content: "";
        position: absolute;
        inset: 0 auto 0 -70%;
        width: 46%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,.42), transparent);
        transform: skewX(-20deg);
        animation: button-shimmer 3.8s ease-in-out infinite;
    }
    @keyframes button-shimmer {
        0%, 62% { left: -70%; }
        86%, 100% { left: 135%; }
    }
    div[data-testid="stFileUploader"] button:hover {
        color: #FFFFFF;
        background: linear-gradient(135deg, #1D4ED8, #12399A);
        transform: translateY(-2px);
        box-shadow: 0 14px 26px rgba(37, 99, 235, .30);
    }

    @media (max-width: 540px) {
        div[data-testid="stFileUploader"]::before,
        div[data-testid="stFileUploader"]::after { top: 23px; font-size: 8px; }
        div[data-testid="stFileUploader"]::before { left: 18px; }
        div[data-testid="stFileUploader"]::after { right: 18px; }
    }

    /* Hide Streamlit's native add-more-files (+) control from the first render. */
    div[data-testid="stFileUploader"] button[aria-label="Add file"],
    div[data-testid="stFileUploader"] button[aria-label="Add files"],
    div[data-testid="stFileUploader"] button[title="Add file"],
    div[data-testid="stFileUploader"] button[title="Add files"],
    div[data-testid="stFileUploader"] .stFileUploaderFile + button,
    div[data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] + button {
        display: none !important;
    }

    /* The whole card is the upload trigger; no separate button or repeated limit copy. */
    div[data-testid="stFileUploader"] section > span {
        position: absolute !important;
        inset: 0;
        z-index: 4;
        order: unset;
    }
    div[data-testid="stFileUploader"] section > span button {
        width: 100%;
        height: 100%;
        min-height: 100%;
        padding: 0;
        opacity: 0;
        cursor: pointer;
    }
    div[data-testid="stFileUploaderDropzoneInstructions"] { display: none; }
    div[data-testid="stFileUploader"] section::after {
        content: "Drop your project CSV here\\A Drag it anywhere in this space to begin";
        line-height: 1.8;
    }

    div[data-testid="stButton"] > button {
        display: block;
        min-height: 0;
        margin: 12px auto 0;
        padding: 7px 12px;
        color: #64748B;
        background: transparent;
        border: 1px solid #DDE8F7;
        border-radius: 9px;
        font-size: 12px;
        font-weight: 650;
    }
    div[data-testid="stButton"] > button:hover {
        color: #DC2626;
        background: #FFF7F7;
        border-color: #FECACA;
    }

    /* File actions: one quiet destructive action and one clear next step. */
    .st-key-remove_selected_file button {
        width: 100% !important;
        min-height: 46px !important;
        margin: 10px 0 0 !important;
        padding: 0 16px !important;
        color: #7B8BA2 !important;
        background: rgba(255,255,255,.72) !important;
        border: 1px solid #E3EAF5 !important;
        border-radius: 14px !important;
        box-shadow: none !important;
        transition: color .2s ease, background .2s ease, border-color .2s ease !important;
    }
    .st-key-remove_selected_file button:hover {
        color: #C94A5A !important;
        background: #FFF7F8 !important;
        border-color: #F2C9D0 !important;
        transform: none !important;
    }
    .st-key-analyze_project button {
        position: relative;
        width: 100% !important;
        min-height: 46px !important;
        margin: 10px 0 0 !important;
        padding: 0 22px !important;
        overflow: hidden;
        color: #FFFFFF !important;
        background: linear-gradient(110deg,#315EE8 0%,#6377EC 52%,#477BCB 100%) !important;
        background-size: 180% 100% !important;
        border: 0 !important;
        border-radius: 14px !important;
        box-shadow: 0 12px 26px rgba(58,91,210,.22) !important;
        font-size: 13px !important;
        font-weight: 750 !important;
        letter-spacing: .01em !important;
        transition: transform .2s ease, box-shadow .2s ease, background-position .35s ease !important;
    }
    .st-key-analyze_project button:hover {
        color: #FFFFFF !important;
        background-position: 100% 0 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 16px 32px rgba(58,91,210,.29) !important;
    }
    .st-key-analyze_project button:focus-visible,
    .st-key-remove_selected_file button:focus-visible {
        outline: 2px solid #6E8FF1 !important;
        outline-offset: 3px !important;
    }

    /* Lightweight analysis journey shown while the pipeline is running. */
    .analysis-motion {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 26px 0 10px;
        text-align: center;
    }
    .analysis-orbit {
        position: relative;
        width: 82px;
        height: 82px;
        margin-bottom: 17px;
        border: 1px solid #DCE7FA;
        border-radius: 50%;
        animation: analysis-spin 3.6s linear infinite;
    }
    .analysis-orbit::before {
        content: "";
        position: absolute;
        inset: 13px;
        border: 1px solid #C7D9F8;
        border-radius: 50%;
        animation: analysis-spin 2.4s linear infinite reverse;
    }
    .analysis-core {
        position: absolute;
        inset: 25px;
        display: grid;
        place-items: center;
        border-radius: 50%;
        color: #FFFFFF;
        background: linear-gradient(145deg,#4B88F5,#7567E8);
        box-shadow: 0 0 0 8px rgba(85,116,232,.08),0 10px 25px rgba(64,89,190,.22);
        animation: analysis-spin 3.6s linear infinite reverse;
    }
    .analysis-dot {
        position: absolute;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #55C7C1;
        box-shadow: 0 0 0 4px rgba(85,199,193,.10);
    }
    .analysis-dot.one { top: -4px; left: 35px; }
    .analysis-dot.two { right: 2px; bottom: 9px; background:#7D73EB; }
    .analysis-motion-title { color:#182641; font-size:15px; font-weight:760; }
    .analysis-motion-detail { max-width:500px; margin-top:5px; color:#8492A8; font-size:11px; line-height:1.55; }
    .analysis-phases { display:flex; align-items:center; gap:8px; margin-top:15px; }
    .analysis-phases span { color:#A2AFC1; font-size:9px; font-weight:750; letter-spacing:.08em; text-transform:uppercase; }
    .analysis-phases span.active { color:#4F6ED0; }
    .analysis-phases i { width:20px; height:1px; background:#DCE5F3; }
    @keyframes analysis-spin { to { transform: rotate(360deg); } }

    @media (max-width: 540px) {
        .st-key-remove_selected_file button,
        .st-key-analyze_project button { min-height: 44px !important; }
    }



    /* Keep the Upload workflow header visually identical to Analysis/Simulation. */
    .workflow-brand {
        text-align: center !important;
        color: #345EE9 !important;
        font-size: 26px !important;
        font-weight: 750 !important;
        line-height: 1.3 !important;
        letter-spacing: .08em !important;
        margin: 4px 0 24px !important;
    }

    .st-key-workflow_navigation {
        max-width: 740px !important;
        margin: 0 auto 22px !important;
        padding: 0 !important;
        border: none !important;
        border-radius: 0 !important;
        background: transparent !important;
        box-shadow: none !important;
    }

    .st-key-workflow_navigation [data-testid="stButton"] > button {
        margin: 0 !important;
    }

    .st-key-workflow_navigation .st-key-workflow_previous button,
    .st-key-workflow_navigation .st-key-workflow_next button {
        color: #4F6ED0 !important;
        background: transparent !important;
        border: 0 !important;
        box-shadow: none !important;
    }

    .st-key-workflow_navigation .st-key-workflow_previous button:hover,
    .st-key-workflow_navigation .st-key-workflow_next button:hover {
        color: #4F6ED0 !important;
        background: transparent !important;
        border: 0 !important;
        transform: none !important;
        box-shadow: none !important;
    }


    /* =========================================================
       UPLOAD PALETTE — match Analysis / Simulation
       Frontend colors only. No layout, data, or behavior changes.
       ========================================================= */

    .main-title {
        color: #18223C !important;
    }

    .subtitle {
        color: #7F8BA4 !important;
    }

    .intake-kicker {
        color: #7577B2 !important;
    }

    .intake-kicker::before,
    .intake-kicker::after {
        background: linear-gradient(90deg, transparent, #B8B8EC) !important;
    }

    .brand::before {
        background: #6678E8 !important;
        box-shadow: 0 0 0 5px rgba(102,120,232,.10) !important;
    }

    .upload-note {
        border-color: #E2E2F5 !important;
        color: #747F99 !important;
        background: rgba(255,255,255,.80) !important;
    }

    .upload-note strong {
        color: #7168DF !important;
    }

    .selected-file {
        border-color: #DEDEF2 !important;
        box-shadow: 0 8px 22px rgba(91,83,178,.07) !important;
    }

    .selected-file::after {
        background: linear-gradient(180deg,#6678E8,#7A67DF) !important;
    }

    .file-badge,
    .file-icon {
        color: #665FD6 !important;
        background: #F0EFFF !important;
    }

    .file-info {
        border-color: #DEDEF2 !important;
        box-shadow: 0 4px 15px rgba(91,83,178,.055) !important;
    }

    div[data-testid="stFileUploader"] section {
        background-color: #F8F7FF !important;
        background-image:
            linear-gradient(rgba(102,120,232,.028) 1px, transparent 1px),
            linear-gradient(90deg, rgba(122,103,223,.028) 1px, transparent 1px),
            radial-gradient(circle at 14% 88%, rgba(109,137,232,.13), transparent 10rem),
            radial-gradient(circle at 88% 12%, rgba(155,121,229,.14), transparent 12rem) !important;
        border-color: #CFCDF3 !important;
        box-shadow:
            0 24px 60px rgba(91,83,178,.10),
            inset 0 1px 0 rgba(255,255,255,.94) !important;
    }

    div[data-testid="stFileUploader"] section:hover {
        background-color: #FAF9FF !important;
        border-color: #8A7BE3 !important;
        box-shadow:
            0 26px 62px rgba(91,83,178,.14),
            inset 0 1px 0 rgba(255,255,255,.96) !important;
    }

    div[data-testid="stFileUploader"]::before,
    div[data-testid="stFileUploader"]::after {
        color: #777BB0 !important;
    }

    div[data-testid="stFileUploader"] section::before {
        background-color: #6D72DF !important;
        background-image:
            linear-gradient(145deg, rgba(255,255,255,.28), transparent 45%),
            url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='36' height='36' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 16V3'/%3E%3Cpath d='m7 8 5-5 5 5'/%3E%3Cpath d='M4 15v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4'/%3E%3C/svg%3E") !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        box-shadow:
            0 13px 25px rgba(91,83,178,.23),
            0 0 0 8px rgba(122,103,223,.065) !important;
    }

    div[data-testid="stFileUploader"] button {
        color: #FFFFFF !important;
        background: linear-gradient(135deg,#6678E8 0%,#7A67DF 100%) !important;
        border-color: #7168DF !important;
        box-shadow: 0 10px 20px rgba(91,83,178,.18) !important;
    }

    div[data-testid="stFileUploader"] button:hover {
        color: #FFFFFF !important;
        background: linear-gradient(135deg,#5D70DE 0%,#6F5BD1 100%) !important;
        border-color: #6F5BD1 !important;
        box-shadow: 0 14px 26px rgba(91,83,178,.24) !important;
    }

    div[data-testid="stFileUploader"] button:focus-visible {
        outline-color: rgba(122,103,223,.24) !important;
    }

    .workflow {
        border-color: #E2E2F3 !important;
        box-shadow: 0 10px 28px rgba(91,83,178,.04) !important;
    }

    .workflow-icon {
        background: #F0EFFF !important;
        color: #6B66D8 !important;
    }

    .workflow-step:first-child .workflow-icon {
        background: linear-gradient(135deg,#6678E8,#7A67DF) !important;
        color: #FFFFFF !important;
    }

    .workflow-line {
        background: #DADAF2 !important;
    }

    @keyframes blueprint-glow {
        0%, 100% {
            box-shadow: 0 24px 60px rgba(91,83,178,.085), inset 0 1px 0 rgba(255,255,255,.94);
        }
        50% {
            box-shadow: 0 27px 66px rgba(105,91,195,.13), inset 0 1px 0 rgba(255,255,255,.97);
        }
    }


    /* =========================================================
       UPLOAD PALETTE FINAL — force Upload page to match
       Analysis / Simulation palette more closely
       ========================================================= */

    .workflow-brand {
        color: #4665E8 !important;
    }

    .st-key-workflow_navigation [data-testid="stButton"] button {
        color: #7F8CAA !important;
    }

    .st-key-workflow_navigation [data-testid="stButton"] button::before {
        background: #E0E5F0 !important;
        box-shadow: 0 0 0 1px #D6DEEE !important;
    }

    .st-key-workflow_navigation [data-testid="stButton"] button[kind="primary"] {
        color: #5E70DF !important;
    }

    .st-key-workflow_navigation [data-testid="stButton"] button[kind="primary"]::before {
        background: linear-gradient(135deg,#6F7CE7 0%, #7E74E2 100%) !important;
        box-shadow: 0 0 0 5px rgba(111,124,231,.12) !important;
    }

    .st-key-workflow_navigation [data-testid="stButton"] button:disabled {
        color: #98A4BC !important;
    }

    .main-title {
        color: #18223C !important;
    }

    .subtitle {
        color: #8090A9 !important;
    }

    .intake-kicker {
        color: #7B7FB6 !important;
    }

    .intake-kicker::before,
    .intake-kicker::after {
        background: linear-gradient(90deg, transparent, #D4D7F2) !important;
    }

    div[data-testid="stFileUploader"]::before,
    div[data-testid="stFileUploader"]::after {
        color: #7B7FB6 !important;
    }

    div[data-testid="stFileUploader"] section {
        background-color: rgba(249,248,255,.92) !important;
        background-image:
            linear-gradient(rgba(111,124,231,.028) 1px, transparent 1px),
            linear-gradient(90deg, rgba(126,116,226,.028) 1px, transparent 1px),
            radial-gradient(circle at 18% 86%, rgba(115,139,235,.10), transparent 11rem),
            radial-gradient(circle at 84% 16%, rgba(158,130,229,.11), transparent 11rem) !important;
        border-color: #D2D6F3 !important;
        box-shadow:
            0 24px 58px rgba(93,98,168,.08),
            inset 0 1px 0 rgba(255,255,255,.96) !important;
    }

    div[data-testid="stFileUploader"] section:hover {
        background-color: rgba(250,249,255,.97) !important;
        border-color: #B7B8EE !important;
        box-shadow:
            0 26px 62px rgba(93,98,168,.11),
            inset 0 1px 0 rgba(255,255,255,.98) !important;
    }

    div[data-testid="stFileUploader"] section::before {
        background-color: #6D78E5 !important;
        background-image:
            linear-gradient(145deg, rgba(255,255,255,.20), transparent 48%),
            url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='36' height='36' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 16V3'/%3E%3Cpath d='m7 8 5-5 5 5'/%3E%3Cpath d='M4 15v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4'/%3E%3C/svg%3E") !important;
        background-position: center, center !important;
        background-repeat: no-repeat, no-repeat !important;
        background-size: auto, 36px 36px !important;
        box-shadow:
            0 13px 28px rgba(97,101,190,.20),
            0 0 0 8px rgba(122,111,223,.06) !important;
    }

    .selected-file {
        border-color: #DBE0F0 !important;
        background: rgba(255,255,255,.82) !important;
        box-shadow: 0 10px 24px rgba(91,83,178,.055) !important;
    }

    .selected-file::after {
        background: linear-gradient(180deg,#6E79E8 0%, #7B6FDF 100%) !important;
    }

    .file-badge,
    .file-icon {
        color: #6964D8 !important;
        background: #F2F0FE !important;
    }

    .file-name {
        color: #27324B !important;
    }

    .file-size {
        color: #95A1B9 !important;
    }

    .file-status {
        color: #57A95F !important;
    }

    .st-key-remove_selected_file button {
        color: #818DA6 !important;
        border: 1px solid #D8DDF0 !important;
        background: rgba(255,255,255,.72) !important;
        box-shadow: none !important;
    }

    .st-key-remove_selected_file button:hover {
        color: #6F7892 !important;
        border-color: #C8D0E7 !important;
        background: rgba(255,255,255,.90) !important;
        box-shadow: 0 8px 18px rgba(91,83,178,.05) !important;
    }

    .st-key-analyze_project button[kind="primary"] {
        color: #FFFFFF !important;
        background: linear-gradient(135deg,#5F70E2 0%, #7569DB 100%) !important;
        border-color: #6F67DA !important;
        box-shadow: 0 12px 26px rgba(95,112,226,.18) !important;
    }

    .st-key-analyze_project button[kind="primary"]:hover {
        color: #FFFFFF !important;
        background: linear-gradient(135deg,#5668D9 0%, #6C5FD2 100%) !important;
        border-color: #6659CB !important;
        box-shadow: 0 14px 28px rgba(95,112,226,.22) !important;
    }


    /* Normalize Upload header arrows so they match the other pages exactly */
    .st-key-workflow_navigation .st-key-workflow_previous button,
    .st-key-workflow_navigation .st-key-workflow_next button {
        width: 36px !important;
        height: 36px !important;
        min-height: 36px !important;
        margin: 0 auto !important;
        padding: 0 !important;
        display: grid !important;
        place-items: center !important;
        border: 0 !important;
        border-radius: 0 !important;
        background: transparent !important;
        box-shadow: none !important;
        color: #4F6ED0 !important;
        font-family: Inter, "Segoe UI Symbol", "Arial Unicode MS", sans-serif !important;
        font-size: 22px !important;
        font-weight: 400 !important;
        line-height: 1 !important;
        letter-spacing: 0 !important;
        transform: none !important;
    }

    .st-key-workflow_navigation .st-key-workflow_previous button p,
    .st-key-workflow_navigation .st-key-workflow_next button p {
        margin: 0 !important;
        color: inherit !important;
        font-family: Inter, "Segoe UI Symbol", "Arial Unicode MS", sans-serif !important;
        font-size: 22px !important;
        font-weight: 400 !important;
        line-height: 1 !important;
        letter-spacing: 0 !important;
        transform: translateY(-1px) !important;
    }

    .st-key-workflow_navigation .st-key-workflow_previous button:hover,
    .st-key-workflow_navigation .st-key-workflow_next button:hover,
    .st-key-workflow_navigation .st-key-workflow_previous button:active,
    .st-key-workflow_navigation .st-key-workflow_next button:active,
    .st-key-workflow_navigation .st-key-workflow_previous button:focus-visible,
    .st-key-workflow_navigation .st-key-workflow_next button:focus-visible {
        color: #4F6ED0 !important;
        background: transparent !important;
        border: 0 !important;
        box-shadow: none !important;
        transform: none !important;
    }

    .st-key-workflow_navigation .st-key-workflow_previous button:disabled,
    .st-key-workflow_navigation .st-key-workflow_next button:disabled {
        color: #8395B5 !important;
        opacity: 1 !important;
    }

</style>
""",
    unsafe_allow_html=True
)


def analysis_motion_html(title, detail, active_step):
    """Render the current pipeline stage without Streamlit's boxed status UI."""
    phases = ("Read", "Understand", "Simulate")
    phase_html = []
    for index, phase in enumerate(phases):
        phase_html.append(
            f'<span class="{"active" if index <= active_step else ""}">{phase}</span>'
        )
        if index < len(phases) - 1:
            phase_html.append("<i></i>")
    return (
        '<div class="analysis-motion">'
        '<div class="analysis-orbit">'
        '<span class="analysis-dot one"></span>'
        '<span class="analysis-dot two"></span>'
        '<div class="analysis-core">⌁</div>'
        '</div>'
        f'<div class="analysis-motion-title">{html.escape(title)}</div>'
        f'<div class="analysis-motion-detail">{html.escape(detail)}</div>'
        f'<div class="analysis-phases">{"".join(phase_html)}</div>'
        '</div>'
    )


# =========================================================
# HEADER
# =========================================================


st.markdown(
    '<div class="main-title">Turn your project data into clarity</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Start with one CSV file. Under Control will help you uncover what needs attention next.'
    '</div>',
    unsafe_allow_html=True
)

st.markdown('<div class="intake-kicker">Your project story starts here</div>', unsafe_allow_html=True)


# =========================================================
# FILE UPLOADER
# =========================================================

if st.session_state.get("analysis_output"):
    st.info(f"Current project: {st.session_state.get('analyzed_filename', 'Uploaded file')}. Use the steps above to revisit results, or choose a new CSV below.")

uploader_key = f"project_csv_{st.session_state.get('uploader_version', 0)}"
uploaded_file = st.file_uploader(
    "Drop your CSV file here",
    type=["csv"],
    help="CSV files up to 10 MB.",
    key=uploader_key,
)

if uploaded_file is not None:
    fingerprint = hashlib.sha256(uploaded_file.getvalue()).hexdigest() + uploaded_file.name
    if st.session_state.get("uploaded_fingerprint") != fingerprint:
        clear_analysis_result()
        st.session_state["uploaded_fingerprint"] = fingerprint
        st.rerun()
    file_size = uploaded_file.size / (1024 * 1024)

    if uploaded_file.size > MAX_UPLOAD_BYTES:
        st.error("This file is larger than 10 MB. Please choose a smaller CSV file.")
    else:
        safe_name = html.escape(uploaded_file.name)
        st.markdown(
            f'<div class="selected-file">'
            f'<div class="file-badge">CSV</div>'
            f'<div class="file-meta">'
            f'<div class="file-name">{safe_name}</div>'
            f'<div class="file-size">{file_size:.2f} MB</div>'
            f'</div>'
            f'<div class="file-status">✓ Ready to analyze</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        remove_column, analyze_column = st.columns([1, 3], gap="small")
        with remove_column:
            st.button(
                "× Remove",
                key="remove_selected_file",
                on_click=clear_uploaded_file,
                use_container_width=True,
            )
        with analyze_column:
            analyze_clicked = st.button(
                "Analyze project  →",
                key="analyze_project",
                type="primary",
                use_container_width=True,
            )

        if analyze_clicked:
            clear_analysis_result()
            try:
                user_df = read_uploaded_csv(uploaded_file)
                if len(user_df.columns) < 2:
                    raise ValueError("This file doesn't contain enough task information. Upload a CSV with task IDs or descriptions and details such as status, priority, or dates.")
            except (ValueError, pd.errors.ParserError, pd.errors.EmptyDataError) as error:
                st.warning(str(error))
            else:
                analysis_motion = st.empty()
                try:
                    # The backend receives the original upload, unchanged.
                    analysis_motion.markdown(
                        analysis_motion_html(
                            "Reading your project",
                            f"{len(user_df):,} tasks received. Preparing the analysis workspace.",
                            0,
                        ),
                        unsafe_allow_html=True,
                    )
                    started = perf_counter()
                    from pipeline.pipeline import run_analysis
                    tools_ready = perf_counter()
                    analysis_motion.markdown(
                        analysis_motion_html(
                            "Finding the project story",
                            "The agents are connecting risks, blockers and recovery options.",
                            1,
                        ),
                        unsafe_allow_html=True,
                    )
                    pipeline_result = run_analysis(user_df)
                    analysis_finished = perf_counter()
                    timing_logger = logging.getLogger("undercontrol.ui.timing")
                    timing_logger.setLevel(logging.INFO)
                    timing_logger.info(
                        "Analysis tools loaded in %.1fs; backend pipeline completed in %.1fs",
                        tools_ready - started,
                        analysis_finished - tools_ready,
                    )
                    analysis_motion.markdown(
                        analysis_motion_html(
                            "Your project view is ready",
                            "Opening the analysis and recovery path.",
                            2,
                        ),
                        unsafe_allow_html=True,
                    )

                    if not isinstance(pipeline_result, dict):
                        raise RuntimeError("No structured pipeline result was returned.")

                    analysis_result = pipeline_result.get("analysis")
                    simulation_result = pipeline_result.get("simulation")
                    project_dataframe = pipeline_result.get("project_dataframe")

                    if hasattr(analysis_result, "model_dump"):
                        analysis_result = analysis_result.model_dump()

                    if hasattr(simulation_result, "model_dump"):
                        simulation_result = simulation_result.model_dump()

                    if not isinstance(analysis_result, dict) or not analysis_result:
                        raise RuntimeError("No structured analysis was returned.")

                    if not isinstance(simulation_result, dict) or not simulation_result:
                        raise RuntimeError("No structured simulation was returned.")

                    if not isinstance(project_dataframe, pd.DataFrame):
                        raise RuntimeError("No standardized project data was returned.")

                    st.session_state["project_dataframe"] = project_dataframe.copy()
                    st.session_state["analysis_output"] = analysis_result
                    st.session_state["simulation_output"] = simulation_result
                    st.session_state["analyzed_filename"] = uploaded_file.name
                    save_dev_preview(
                        analysis_result,
                        simulation_result,
                        project_dataframe,
                        uploaded_file.name,
                    )
                    # Cover the outgoing Upload DOM during the destination rerun.
                    # The overlay is removed only after render_dashboard_ui() returns.
                    st.session_state["route_transition_target"] = "analysis"
                    st.query_params["view"] = "analysis"
                    st.rerun()
                except Exception:
                    analysis_motion.empty()
                    clear_analysis_result()
                    logging.getLogger(__name__).exception("Project analysis failed")
                    st.error("We couldn't complete the analysis because of a technical problem. Please try again. If the problem continues, contact your project administrator.")



# =========================================================
# REQUIREMENTS
# =========================================================

st.markdown(
    '<div class="requirements">'
    'CSV file only &nbsp; • &nbsp; Up to 10 MB'
    '</div>',
    unsafe_allow_html=True
)
