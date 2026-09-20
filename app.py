
# import html
# import importlib

# import streamlit as st

# import dashboard_white_ui


# MAX_UPLOAD_BYTES = 10 * 1024 * 1024


# def clear_uploaded_file():
#     """Rebuild the native uploader empty when the user removes a file."""
#     st.session_state["uploader_version"] = st.session_state.get("uploader_version", 0) + 1


# # =========================================================
# # PAGE CONFIGURATION
# # =========================================================

# st.set_page_config(
#     page_title="Under Control",
#     layout="centered",
#     initial_sidebar_state="collapsed"
# )

# if st.query_params.get("view") == "dashboard":
#     importlib.reload(dashboard_white_ui)
#     dashboard_white_ui.render_dashboard_ui()
#     st.stop()


# # =========================================================
# # CUSTOM CSS
# # =========================================================

# st.markdown(
#     """
# <style>

#     /* =========================
#        GLOBAL
#        ========================= */

#     .stApp {
#         background-color: #FFFFFF;
#     }

#     .block-container {
#         max-width: 820px;
#         padding-top: 55px;
#         padding-bottom: 70px;
#     }

#     header {
#         visibility: hidden;
#     }


#     /* =========================
#        BRAND
#        ========================= */

#     .brand {
#         text-align: center;
#         color: #2563EB;
#         font-size: 22px;
#         font-weight: 700;
#         letter-spacing: 0.5px;
#         margin-bottom: 55px;
#     }


#     /* =========================
#        TITLE
#        ========================= */

#     .main-title {
#         text-align: center;
#         color: #172033;
#         font-size: 32px;
#         font-weight: 700;
#         letter-spacing: -0.7px;
#         margin: 0;
#     }

#     .subtitle {
#         text-align: center;
#         color: #4B5563;
#         font-size: 15px;
#         line-height: 1.6;
#         max-width: 620px;
#         margin: 12px auto 38px auto;
#     }


#     /* =========================
#        UPLOAD CARD
#        ========================= */

#     .upload-card {
#         background-color: #F8FAFF;
#         border: 1.5px dashed #B9D2FF;
#         border-radius: 18px;
#         min-height: 250px;
#         text-align: center;
#         padding: 45px 30px 40px 30px;
#         box-sizing: border-box;
#     }

#     .upload-icon {
#         width: 58px;
#         height: 58px;

#         display: flex;
#         align-items: center;
#         justify-content: center;

#         background-color: #EAF2FF;
#         color: #2563EB;

#         border-radius: 15px;

#         font-size: 28px;
#         font-weight: 600;

#         margin: 0 auto 18px auto;
#     }

#     .upload-title {
#         color: #172033;
#         font-size: 18px;
#         font-weight: 600;
#         margin-bottom: 7px;
#     }

#     .upload-description {
#         color: #94A3B8;
#         font-size: 14px;
#     }


#     /* =========================
#        STREAMLIT UPLOADER
#        ========================= */

#     div[data-testid="stFileUploader"] {
#         margin-top: -105px;
#         margin-bottom: 25px;
#         position: relative;
#         z-index: 5;
#     }

#     div[data-testid="stFileUploader"] section {
#         background-color: transparent;
#         border: none;
#     }

#     div[data-testid="stFileUploader"] small {
#         display: none;
#     }

#     div[data-testid="stFileUploader"] button {
#         border: 1px solid #D9E6FF;
#         border-radius: 9px;
#         background-color: #FFFFFF;
#         color: #2563EB;
#         font-weight: 600;
#         padding: 7px 17px;
#     }

#     div[data-testid="stFileUploader"] button:hover {
#         border-color: #2563EB;
#         color: #2563EB;
#         background-color: #FFFFFF;
#     }


#     /* =========================
#        REQUIREMENTS
#        ========================= */

#     .requirements {
#         text-align: center;
#         color: #94A3B8;
#         font-size: 12px;
#         margin-top: 12px;
#         margin-bottom: 28px;
#     }


#     /* =========================
#        FILE INFORMATION
#        ========================= */

#     .file-info {
#         display: flex;
#         align-items: center;

#         width: 100%;

#         background-color: #FFFFFF;
#         border: 1px solid #D9E6FF;
#         border-radius: 14px;

#         padding: 15px 18px;
#         box-sizing: border-box;

#         box-shadow: 0 4px 15px rgba(37, 99, 235, 0.06);

#         margin-top: 5px;
#     }

#     .file-icon {
#         width: 42px;
#         height: 42px;

#         display: flex;
#         align-items: center;
#         justify-content: center;

#         background-color: #EAF2FF;
#         color: #2563EB;

#         border-radius: 10px;

#         font-size: 20px;

#         margin-right: 13px;
#         flex-shrink: 0;
#     }

#     .file-name {
#         color: #172033;
#         font-size: 14px;
#         font-weight: 600;
#         text-align: left;
#     }

#     .file-size {
#         color: #94A3B8;
#         font-size: 12px;
#         margin-top: 3px;
#         text-align: left;
#     }

#     .file-status {
#         margin-left: auto;
#         color: #16A34A;
#         font-size: 13px;
#         font-weight: 600;
#     }

#     /* Use Streamlit's actual drop zone as the card, not a separate visual overlay. */
#     .upload-card { display: none; }

#     div[data-testid="stFileUploader"] {
#         margin: 0;
#     }

#     div[data-testid="stFileUploader"] section {
#         min-height: 278px;
#         padding: 32px 28px;
#         background: #F4F8FF;
#         border: 1.5px dashed #B9D2FF;
#         border-radius: 20px;
#         transition: background 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
#     }

#     div[data-testid="stFileUploader"] section:hover {
#         background: #F8FBFF;
#         border-color: #2563EB;
#         box-shadow: 0 12px 30px rgba(37, 99, 235, 0.08);
#     }

#     div[data-testid="stFileUploaderDropzoneInstructions"] {
#         display: flex;
#         flex-direction: column;
#         align-items: center;
#         gap: 9px;
#     }

#     div[data-testid="stFileUploaderDropzoneInstructions"] > div:first-child {
#         display: flex;
#         align-items: center;
#         justify-content: center;
#         width: 64px;
#         height: 64px;
#         margin-bottom: 7px;
#         background: #E7F0FF;
#         border: 1px solid #D5E5FF;
#         border-radius: 16px;
#         color: #2563EB;
#     }

#     div[data-testid="stFileUploaderDropzoneInstructions"] svg {
#         width: 31px;
#         height: 31px;
#     }

#     div[data-testid="stFileUploaderDropzoneInstructions"] span,
#     div[data-testid="stFileUploaderDropzoneInstructions"] small {
#         color: #172033 !important;
#         font-size: 17px !important;
#         font-weight: 650 !important;
#     }

#     div[data-testid="stFileUploaderDropzoneInstructions"] small {
#         color: #64748B !important;
#         font-size: 13px !important;
#         font-weight: 400 !important;
#     }

#     div[data-testid="stFileUploader"] button {
#         padding: 8px 17px;
#         background: #FFFFFF;
#         border: 1px solid #C8DCFF;
#         border-radius: 9px;
#         box-shadow: 0 2px 5px rgba(37, 99, 235, 0.05);
#         color: #2563EB;
#         font-size: 14px;
#         font-weight: 650;
#     }

#     div[data-testid="stFileUploader"] button:hover {
#         color: #FFFFFF;
#         background: #2563EB;
#         border-color: #2563EB;
#     }

#     div[data-testid="stFileUploader"] button:focus-visible {
#         outline: 3px solid rgba(37, 99, 235, 0.22);
#         outline-offset: 2px;
#     }

#     .selected-file {
#         display: flex;
#         align-items: center;
#         gap: 13px;
#         padding: 15px 17px;
#         background: #FFFFFF;
#         border: 1px solid #D8E6FC;
#         border-radius: 14px;
#         box-shadow: 0 8px 22px rgba(37, 99, 235, 0.07);
#     }

#     .file-badge {
#         display: flex;
#         align-items: center;
#         justify-content: center;
#         width: 42px;
#         height: 42px;
#         flex: 0 0 auto;
#         background: #EAF2FF;
#         border-radius: 10px;
#         color: #2563EB;
#         font-size: 12px;
#         font-weight: 800;
#         letter-spacing: 0.04em;
#     }

#     .file-meta { min-width: 0; }
#     .file-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

#     @media (max-width: 540px) {
#         .block-container { padding: 44px 20px 56px; }
#         .brand { margin-bottom: 38px; }
#         div[data-testid="stFileUploader"] section { min-height: 250px; padding: 25px 18px; }
#         .file-status { display: none; }
#     }

#     /* Layout hooks for the current Streamlit uploader markup. */
#     div[data-testid="stFileUploader"] > label { display: none; }
#     div[data-testid="stFileUploader"] section {
#         display: flex;
#         flex-direction: column;
#         align-items: center;
#         justify-content: center;
#         gap: 12px;
#     }
#     div[data-testid="stFileUploader"] section::before {
#         content: "";
#         order: 1;
#         width: 64px;
#         height: 64px;
#         border: 1px solid #D5E5FF;
#         border-radius: 16px;
#         background: #E7F0FF url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 24 24' fill='none' stroke='%232563EB' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 16V3'/%3E%3Cpath d='m7 8 5-5 5 5'/%3E%3Cpath d='M4 15v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4'/%3E%3C/svg%3E") center/32px 32px no-repeat;
#     }
#     div[data-testid="stFileUploader"] section::after {
#         content: "Drop your CSV file here\\A Drag and drop it here, or browse from your computer";
#         order: 2;
#         color: #172033;
#         font-size: 17px;
#         font-weight: 650;
#         line-height: 1.75;
#         text-align: center;
#         white-space: pre-line;
#     }
#     div[data-testid="stFileUploader"] section > span { order: 3; }
#     div[data-testid="stFileUploaderDropzoneInstructions"] {
#         display: block;
#         order: 4;
#     }
#     div[data-testid="stFileUploaderDropzoneInstructions"] > div:first-child {
#         display: block;
#         width: auto;
#         height: auto;
#         margin: 0;
#         background: transparent;
#         border: 0;
#     }
#     div[data-testid="stFileUploaderDropzoneInstructions"] span {
#         color: #64748B !important;
#         font-size: 12px !important;
#         font-weight: 400 !important;
#     }

#     /* Subtle editorial details that keep the page focused on one action. */
#     .stApp {
#         background:
#             radial-gradient(circle at 50% 15%, rgba(219, 234, 254, 0.46), transparent 25rem),
#             linear-gradient(180deg, #FFFFFF 0%, #FBFDFF 100%);
#     }

#     .brand {
#         display: flex;
#         align-items: center;
#         justify-content: center;
#         gap: 9px;
#         font-size: 12px;
#         letter-spacing: 0.16em;
#     }

#     .brand::before {
#         content: "";
#         width: 7px;
#         height: 7px;
#         border-radius: 50%;
#         background: #2563EB;
#         box-shadow: 0 0 0 5px rgba(37, 99, 235, 0.10);
#     }

#     div[data-testid="stFileUploader"] section::before {
#         box-shadow: 0 10px 22px rgba(37, 99, 235, 0.10);
#     }

#     .upload-notes {
#         display: flex;
#         justify-content: center;
#         flex-wrap: wrap;
#         gap: 8px;
#         margin: -8px 0 30px;
#     }

#     .upload-note {
#         display: inline-flex;
#         align-items: center;
#         gap: 6px;
#         padding: 7px 10px;
#         background: rgba(255, 255, 255, 0.78);
#         border: 1px solid #E1EBFA;
#         border-radius: 999px;
#         color: #64748B;
#         font-size: 11px;
#         font-weight: 600;
#     }

#     .upload-note strong { color: #2563EB; font-size: 12px; }

#     .selected-file { position: relative; overflow: hidden; }
#     .selected-file::after {
#         content: "";
#         position: absolute;
#         left: 0;
#         top: 0;
#         bottom: 0;
#         width: 4px;
#         background: #2563EB;
#     }

#     /* A light data-grid and floating mark give the drop zone more character. */
#     div[data-testid="stFileUploader"] section {
#         position: relative;
#         overflow: hidden;
#         background-color: #F5F9FF;
#         background-image:
#             linear-gradient(rgba(37, 99, 235, 0.035) 1px, transparent 1px),
#             linear-gradient(90deg, rgba(37, 99, 235, 0.035) 1px, transparent 1px),
#             radial-gradient(circle at 14% 88%, rgba(191, 219, 254, 0.42), transparent 10rem),
#             radial-gradient(circle at 88% 12%, rgba(219, 234, 254, 0.72), transparent 12rem);
#         background-size: 28px 28px, 28px 28px, auto, auto;
#     }

#     div[data-testid="stFileUploader"] section > * { position: relative; z-index: 1; }

#     div[data-testid="stFileUploader"] section::before {
#         width: 72px;
#         height: 72px;
#         border-radius: 22px;
#         background-size: 34px 34px;
#         animation: float-upload-mark 3.6s ease-in-out infinite;
#     }

#     div[data-testid="stFileUploader"] section::after {
#         text-shadow: 0 1px 0 #FFFFFF;
#     }

#     @keyframes float-upload-mark {
#         0%, 100% { transform: translateY(0); }
#         50% { transform: translateY(-5px); }
#     }

#     .workflow {
#         display: grid;
#         grid-template-columns: 1fr auto 1fr auto 1fr;
#         align-items: center;
#         gap: 10px;
#         max-width: 510px;
#         margin: 0 auto;
#         padding: 15px 18px;
#         background: rgba(255, 255, 255, 0.76);
#         border: 1px solid #E3EDF9;
#         border-radius: 17px;
#         box-shadow: 0 10px 28px rgba(37, 99, 235, 0.045);
#     }

#     .workflow-step { min-width: 0; text-align: center; }
#     .workflow-icon {
#         display: grid;
#         place-items: center;
#         width: 27px;
#         height: 27px;
#         margin: 0 auto 6px;
#         border-radius: 9px;
#         background: #EAF2FF;
#         color: #2563EB;
#         font-size: 12px;
#         font-weight: 800;
#     }
#     .workflow-step:first-child .workflow-icon { background: #2563EB; color: #FFFFFF; }
#     .workflow-title { color: #172033; font-size: 11px; font-weight: 750; }
#     .workflow-caption { color: #94A3B8; font-size: 10px; margin-top: 2px; }
#     .workflow-line { width: 26px; height: 1px; background: #CFE0FA; }

#     @media (max-width: 540px) {
#         .workflow { gap: 6px; padding: 13px 10px; }
#         .workflow-line { width: 12px; }
#         .workflow-caption { display: none; }
#     }

#     /* Signature “data intake” treatment for the hero upload interaction. */
#     .intake-kicker {
#         display: flex;
#         align-items: center;
#         justify-content: center;
#         gap: 9px;
#         margin: -24px 0 26px;
#         color: #6B86B1;
#         font-size: 10px;
#         font-weight: 800;
#         letter-spacing: 0.15em;
#         text-transform: uppercase;
#     }
#     .intake-kicker::before,
#     .intake-kicker::after {
#         content: "";
#         width: 28px;
#         height: 1px;
#         background: linear-gradient(90deg, transparent, #A8C7F7);
#     }
#     .intake-kicker::after { transform: scaleX(-1); }

#     div[data-testid="stFileUploader"] {
#         position: relative;
#         padding: 10px 0;
#     }
#     div[data-testid="stFileUploader"]::before,
#     div[data-testid="stFileUploader"]::after {
#         position: absolute;
#         z-index: 3;
#         top: 28px;
#         color: #7294C6;
#         font-size: 9px;
#         font-weight: 800;
#         letter-spacing: 0.13em;
#         pointer-events: none;
#     }
#     div[data-testid="stFileUploader"]::before { content: "DATA INTAKE"; left: 25px; }
#     div[data-testid="stFileUploader"]::after { content: "01 / CSV"; right: 25px; }

#     div[data-testid="stFileUploader"] section {
#         border-color: #AACBFC;
#         box-shadow: 0 24px 60px rgba(37, 99, 235, 0.13), inset 0 1px 0 rgba(255,255,255,.9);
#         animation: blueprint-glow 4s ease-in-out infinite;
#     }
#     @keyframes blueprint-glow {
#         0%, 100% { box-shadow: 0 24px 60px rgba(37, 99, 235, 0.11), inset 0 1px 0 rgba(255,255,255,.9); }
#         50% { box-shadow: 0 28px 70px rgba(37, 99, 235, 0.19), inset 0 1px 0 rgba(255,255,255,.96); }
#     }

#     div[data-testid="stFileUploader"] section::before {
#         width: 76px;
#         height: 76px;
#         border: 0;
#         border-radius: 25px;
#         background-color: #2563EB;
#         background-image:
#             linear-gradient(145deg, rgba(255,255,255,.26), transparent 45%),
#             url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='36' height='36' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 16V3'/%3E%3Cpath d='m7 8 5-5 5 5'/%3E%3Cpath d='M4 15v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4'/%3E%3C/svg%3E");
#         background-position: center;
#         background-repeat: no-repeat;
#         box-shadow: 0 13px 25px rgba(37, 99, 235, .28), 0 0 0 8px rgba(37, 99, 235, .07);
#     }

#     div[data-testid="stFileUploader"] button {
#         position: relative;
#         overflow: hidden;
#         padding: 10px 20px;
#         color: #FFFFFF;
#         background: linear-gradient(135deg, #2563EB, #1746B5);
#         border-color: #2563EB;
#         box-shadow: 0 10px 20px rgba(37, 99, 235, .22);
#         transition: transform .18s ease, box-shadow .18s ease;
#     }
#     div[data-testid="stFileUploader"] button::after {
#         content: "";
#         position: absolute;
#         inset: 0 auto 0 -70%;
#         width: 46%;
#         background: linear-gradient(90deg, transparent, rgba(255,255,255,.42), transparent);
#         transform: skewX(-20deg);
#         animation: button-shimmer 3.8s ease-in-out infinite;
#     }
#     @keyframes button-shimmer {
#         0%, 62% { left: -70%; }
#         86%, 100% { left: 135%; }
#     }
#     div[data-testid="stFileUploader"] button:hover {
#         color: #FFFFFF;
#         background: linear-gradient(135deg, #1D4ED8, #12399A);
#         transform: translateY(-2px);
#         box-shadow: 0 14px 26px rgba(37, 99, 235, .30);
#     }

#     @media (max-width: 540px) {
#         div[data-testid="stFileUploader"]::before,
#         div[data-testid="stFileUploader"]::after { top: 23px; font-size: 8px; }
#         div[data-testid="stFileUploader"]::before { left: 18px; }
#         div[data-testid="stFileUploader"]::after { right: 18px; }
#     }

#     /* The whole card is the upload trigger; no separate button or repeated limit copy. */
#     div[data-testid="stFileUploader"] section > span {
#         position: absolute !important;
#         inset: 0;
#         z-index: 4;
#         order: unset;
#     }
#     div[data-testid="stFileUploader"] section > span button {
#         width: 100%;
#         height: 100%;
#         min-height: 100%;
#         padding: 0;
#         opacity: 0;
#         cursor: pointer;
#     }
#     div[data-testid="stFileUploaderDropzoneInstructions"] { display: none; }
#     div[data-testid="stFileUploader"] section::after {
#         content: "Drop your project CSV here\\A Drag it anywhere in this space to begin";
#         line-height: 1.8;
#     }

#     div[data-testid="stButton"] > button {
#         display: block;
#         min-height: 0;
#         margin: 12px auto 0;
#         padding: 7px 12px;
#         color: #64748B;
#         background: transparent;
#         border: 1px solid #DDE8F7;
#         border-radius: 9px;
#         font-size: 12px;
#         font-weight: 650;
#     }
#     div[data-testid="stButton"] > button:hover {
#         color: #DC2626;
#         background: #FFF7F7;
#         border-color: #FECACA;
#     }


# </style>
# """,
#     unsafe_allow_html=True
# )


# # =========================================================
# # HEADER
# # =========================================================

# st.markdown(
#     '<div class="brand">UNDER CONTROL</div>',
#     unsafe_allow_html=True
# )

# st.markdown(
#     '<div class="main-title">Turn your project data into clarity</div>',
#     unsafe_allow_html=True
# )

# st.markdown(
#     '<div class="subtitle">'
#     'Start with one CSV file. Under Control will help you uncover what needs attention next.'
#     '</div>',
#     unsafe_allow_html=True
# )

# st.markdown('<div class="intake-kicker">Your project story starts here</div>', unsafe_allow_html=True)


# # =========================================================
# # FILE UPLOADER
# # =========================================================

# uploader_key = f"project_csv_{st.session_state.get('uploader_version', 0)}"
# uploaded_file = st.file_uploader(
#     "Drop your CSV file here",
#     type=["csv"],
#     help="CSV files up to 10 MB.",
#     key=uploader_key,
# )

# if uploaded_file is not None:
#     file_size = uploaded_file.size / (1024 * 1024)

#     if uploaded_file.size > MAX_UPLOAD_BYTES:
#         st.error("This file is larger than 10 MB. Please choose a smaller CSV file.")
#     else:
#         safe_name = html.escape(uploaded_file.name)
#         st.markdown(
#             f'<div class="selected-file">'
#             f'<div class="file-badge">CSV</div>'
#             f'<div class="file-meta">'
#             f'<div class="file-name">{safe_name}</div>'
#             f'<div class="file-size">{file_size:.2f} MB</div>'
#             f'</div>'
#             f'<div class="file-status">✓ Ready to analyze</div>'
#             f'</div>',
#             unsafe_allow_html=True,
#         )
#         st.button("× Remove selected file", key="remove_selected_file", on_click=clear_uploaded_file)


# # =========================================================
# # REQUIREMENTS
# # =========================================================

# st.markdown(
#     '<div class="requirements">'
#     'CSV file only &nbsp; • &nbsp; Up to 10 MB'
#     '</div>',
#     unsafe_allow_html=True
# )


# st.markdown(
#     '<div class="workflow">'
#     '<div class="workflow-step"><div class="workflow-icon">↑</div>'
#     '<div class="workflow-title">Upload</div><div class="workflow-caption">Your CSV file</div></div>'
#     '<div class="workflow-line"></div>'
#     '<div class="workflow-step"><div class="workflow-icon">✓</div>'
#     '<div class="workflow-title">Validate</div><div class="workflow-caption">Check the file</div></div>'
#     '<div class="workflow-line"></div>'
#     '<div class="workflow-step"><div class="workflow-icon">✦</div>'
#     '<div class="workflow-title">Discover</div><div class="workflow-caption">Find insights</div></div>'
#     '</div>',
#     unsafe_allow_html=True,
# )
import io
import logging
import hashlib
from time import perf_counter
import pandas as pd

#from pipeline.pipeline import run_analysis
import html
import importlib

import streamlit as st

import dashboard_white_ui


MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def clear_uploaded_file():
    """Rebuild the native uploader empty when the user removes a file."""
    st.session_state["uploader_version"] = st.session_state.get("uploader_version", 0) + 1
    clear_analysis_result()
    st.session_state.pop("uploaded_fingerprint", None)


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


def read_uploaded_csv(uploaded_file):
    """Read a user-uploaded CSV with common encodings and delimiter detection."""
    file_bytes = uploaded_file.getvalue()

    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = file_bytes.decode(encoding)
            dataframe = pd.read_csv(
                io.StringIO(text),
                sep=None,
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
        padding-top: 55px;
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

    /* Subtle editorial details that keep the page focused on one action. */
    .stApp {
        background:
            radial-gradient(circle at 50% 15%, rgba(219, 234, 254, 0.46), transparent 25rem),
            linear-gradient(180deg, #FFFFFF 0%, #FBFDFF 100%);
    }

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


</style>
""",
    unsafe_allow_html=True
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

        st.button(
            "× Remove selected file",
            key="remove_selected_file",
            on_click=clear_uploaded_file,
        )

        if st.button(
            "Analyze Project",
            key="analyze_project",
            type="primary",
            use_container_width=True,
        ):
            clear_analysis_result()
            try:
                user_df = read_uploaded_csv(uploaded_file)
                if len(user_df.columns) < 2:
                    raise ValueError("This file doesn't contain enough task information. Upload a CSV with task IDs or descriptions and details such as status, priority, or dates.")
            except (ValueError, pd.errors.ParserError, pd.errors.EmptyDataError) as error:
                st.warning(str(error))
            else:
                try:
                    # The backend receives the original upload, unchanged.
                    with st.status("Analyzing your project...", expanded=True) as analysis_status:
                        st.write(f"File read successfully: {len(user_df):,} tasks.")
                        started = perf_counter()
                        with st.spinner("Preparing analysis tools...", show_time=True):
                            from pipeline.pipeline import run_analysis
                        tools_ready = perf_counter()
                        with st.spinner(
                            "Analyzing the project and simulating recovery strategies. Please keep this page open...",
                            show_time=True,
                        ):
                            pipeline_result = run_analysis(user_df)
                        analysis_finished = perf_counter()
                        timing_logger = logging.getLogger("undercontrol.ui.timing")
                        timing_logger.setLevel(logging.INFO)
                        timing_logger.info(
                            "Analysis tools loaded in %.1fs; backend pipeline completed in %.1fs",
                            tools_ready - started,
                            analysis_finished - tools_ready,
                        )
                        analysis_status.update(
                            label="Analysis and simulation completed. Preparing your dashboard...",
                            state="complete",
                            expanded=False,
                        )

                    if not isinstance(pipeline_result, dict):
                        raise RuntimeError("No structured pipeline result was returned.")

                    analysis_result = pipeline_result.get("analysis")
                    simulation_result = pipeline_result.get("simulation")

                    if hasattr(analysis_result, "model_dump"):
                        analysis_result = analysis_result.model_dump()

                    if hasattr(simulation_result, "model_dump"):
                        simulation_result = simulation_result.model_dump()

                    if not isinstance(analysis_result, dict) or not analysis_result:
                        raise RuntimeError("No structured analysis was returned.")

                    if not isinstance(simulation_result, dict) or not simulation_result:
                        raise RuntimeError("No structured simulation was returned.")

                    st.session_state["project_dataframe"] = (
                        dashboard_white_ui.prepare_dashboard_data(user_df)
                    )
                    st.session_state["analysis_output"] = analysis_result
                    st.session_state["simulation_output"] = simulation_result
                    st.session_state["analyzed_filename"] = uploaded_file.name
                    st.query_params["view"] = "analysis"
                    st.rerun()
                except Exception:
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
