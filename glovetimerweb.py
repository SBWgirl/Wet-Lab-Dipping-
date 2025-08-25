import streamlit as st
import time
import pandas as pd
import json
from streamlit.components.v1 import html

# ===========================
# Browser speech synthesis
# ===========================
def speak_js(text: str, rate: float = 1.0, volume: float = 1.0):
    safe = json.dumps(text)
    html(f"""
    <script>
      (function() {{
        try {{
          const u = new SpeechSynthesisUtterance({safe});
          u.rate = {rate};
          u.volume = {volume};
          window.speechSynthesis.cancel();
          window.speechSynthesis.speak(u);
        }} catch (e) {{ console.log("TTS failed:", e); }}
      }})();
    </script>
    """, height=0)

# ===========================
# App setup
# ===========================
st.set_page_config(page_title="Glove Dipping Timer", layout="centered")
st.title("🧤 Glove Dipping Timer (11 Steps — Web)")

# persistent log across button presses
if "log" not in st.session_state:
    st.session_state.log = []

with st.sidebar:
    st.header("⚙️ Controls")
    run_automatically = st.checkbox("Run Automatically", True)
    tts_enabled = st.checkbox("Voice Announcements", True)
    rate = st.slider("Voice Rate", 0.5, 2.0, 1.0, 0.05)
    volume = st.slider("Voice Volume", 0.0, 1.0, 1.0, 0.05)
    if st.button("🔊 Test Voice"):
        speak_js("Voice test is working.", rate, volume)
    st.markdown("---")
    if st.button("🗑️ Reset Log"):
        st.session_state.log = []
        st.success("Log cleared.")

# ===========================
# Inputs
# ===========================
st.markdown("### 🧪 Pre‑Dip")
coag_time       = st.number_input("1) Coag (s)", min_value=0, value=10)
coag_cure_time  = st.number_input("2) Coag Cure (s)", min_value=0, value=10)
dip_time        = st.number_input("3) Dip (s)", min_value=0, value=10)

st.markdown("### 🔄 Rotation & Handling (Dip)")
rotation_time   = st.number_input("4) Rotation — per turn (s)", min_value=0, value=2)
rotation_count  = st.number_input("   Rotation — turns", min_value=0, value=4)
sandy_time      = st.number_input("5) SANDY (s)", min_value=0, value=10)
leech_time      = st.number_input("6) Leech (s)", min_value=0, value=10)
cure_time       = st.number_input("7) Cure (s)", min_value=0, value=2400)

st.markdown("### 🧪 Second Dip & Post")
dip2_time       = st.number_input("8) Dip 2 (s)", min_value=0, value=0)
if dip2_time > 0:
    rotation2_time  = st.number_input("9) Rotation 2 — per turn (s)", min_value=0, value=2)
    rotation2_count = st.number_input("   Rotation 2 — turns", min_value=0, value=4)
    leech2_time     = st.number_input("10) Leech 2 (s)", min_value=0, value=10)
else:
    rotation2_time = 0
    rotation2_count = 0
    leech2_time = 0
cure2_time      = st.number_input("11) Cure 2 (s)", min_value=0, value=2400)

# ===========================
# Helpers
# ===========================
def run_step(name, duration, log):
    """Run a single timed step, with skip-on-0 and voice."""
    if duration > 0:
        st.subheader(f"{name} — {duration}s")
        if tts_enabled:
            speak_js(f"Starting {name} for {duration} seconds.", rate, volume)
        progress = st.progress(0)
        time_display = st.empty()
        if run_automatically:
            for sec in range(duration):
                progress.progress((sec + 1) / duration)
                time_display.write(f"⏳ {duration - sec}s remaining")
                time.sleep(1)
        else:
            st.info(f"Run {duration}s manually, then click Next.")
            st.button(f"Next — after {name}", key=f"next_{name}")
        if tts_enabled:
            speak_js(f"{name} complete.", rate, volume)
        st.success(f"✅ {name} complete")
        st.markdown("---")
        log.append({"Step": name, "Time (s)": duration})
    else:
        st.info(f"⏭️ Skipping {name} (0s)")
        st.markdown("---")
        log.append({"Step": name, "Time (s)": 0})

def run_rotation(block_title, per_turn, turns, prefix="Rotation"):
    """Grouped rotation block (per-turn timing)."""
    if per_turn > 0 and turns > 0:
        st.subheader(f"🔄 {block_title} — {turns} × {per_turn}s")
        if tts_enabled:
            speak_js(f"Starting {block_title.lower()}. {turns} turns at {per_turn} seconds per turn.", rate, volume)
        for i in range(1, turns + 1):
            st.write(f"↺ {prefix} — Turn {i}")
            if run_automatically:
                time.sleep(per_turn)
            else:
                st.info(f"Run {per_turn} seconds and click to continue.")
                st.button(f"Next — {prefix} Turn {i}", key=f"{prefix}_{i}")
        if tts_enabled:
            speak_js(f"{block_title} complete.", rate, volume)
        st.success(f"✅ {block_title} complete")
        st.markdown("---")
        st.session_state.log.append({"Step": block_title, "Time (s)": per_turn * turns})
    else:
        st.info(f"⏭️ Skipping {block_title} (0 time or 0 turns)")
        st.markdown("---")
        st.session_state.log.append({"Step": block_title, "Time (s)": 0})

# Section runners
def run_pre_dip():
    run_step("Coag", coag_time, st.session_state.log)
    run_step("Coag Cure", coag_cure_time, st.session_state.log)
    run_step("Dip", dip_time, st.session_state.log)

def run_dip_block():
    run_rotation("Rotation", rotation_time, rotation_count, prefix="Rotation")
    run_step("SANDY", sandy_time, st.session_state.log)
    run_step("Leech", leech_time, st.session_state.log)
    run_step("Cure", cure_time, st.session_state.log)

def run_dip2_block():
    run_step("Dip 2", dip2_time, st.session_state.log)
    if dip2_time > 0:
        run_rotation("Rotation 2", rotation2_time, rotation2_count, prefix="Rotation 2")
        run_step("Leech 2", leech2_time, st.session_state.log)
    else:
        # auto-skip dependent steps when Dip 2 = 0
        st.session_state.log.append({"Step": "Rotation 2", "Time (s)": 0})
        st.session_state.log.append({"Step": "Leech 2", "Time (s)": 0})
    run_step("Cure 2", cure2_time, st.session_state.log)

# ===========================
# Buttons
# ===========================
cols = st.columns(4)
with cols[0]:
    if st.button("▶️ Run Pre‑Dip"):
        run_pre_dip()
with cols[1]:
    if st.button("▶️ Run Dip"):
        run_dip_block()
with cols[2]:
    if st.button("▶️ Run Dip 2"):
        run_dip2_block()
with cols[3]:
    if st.button("▶️ Run ALL"):
        run_pre_dip()
        run_dip_block()
        run_dip2_block()

# ===========================
# Log display & download
# ===========================
st.markdown("### 📋 Timer Log")
if st.session_state.log:
    df = pd.DataFrame(st.session_state.log)
    st.dataframe(df, use_container_width=True)
    st.download_button(
        "📥 Download CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="glove_timer_log.csv",
        mime="text/csv",
    )
else:
    st.info("No steps run yet. Start a section above ✨")