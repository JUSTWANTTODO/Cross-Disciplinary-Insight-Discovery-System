import os
from services.insight_service import generate_insight_badges
from utils.pdf_parser import extract_text_from_pdf
from utils.text_cleaner import clean_text
from services.intent_service import normalize_intent
from services.live_search_service import unified_search
from services.embedding_service import rank_papers_by_similarity
from services.confidence_service import compute_confidence
from agents.research_agent import generate_hypotheses
import re
import streamlit as st
from dotenv import load_dotenv
load_dotenv()


# Cached Agent Call
@st.cache_data(show_spinner=False)
def cached_generate_hypotheses(user_input, ranked_papers, max_hypotheses):
    return generate_hypotheses(
        user_input=user_input,
        ranked_papers=ranked_papers,
        max_hypotheses=max_hypotheses
    )


# Agent Session Memory
if "iteration" not in st.session_state:
    st.session_state.iteration = 1

if "cleaned_text" not in st.session_state:
    st.session_state.cleaned_text = None

if "ranked_papers" not in st.session_state:
    st.session_state.ranked_papers = None

if "agent_output" not in st.session_state:
    st.session_state.agent_output = None

if "refined_output" not in st.session_state:   # FIX
    st.session_state.refined_output = None

if "has_results" not in st.session_state:
    st.session_state.has_results = False


# Page config
st.set_page_config(page_title="Silo Synapse", layout="wide")

left, center, right = st.columns([1, 2, 1])


with center:

    st.markdown("## Silo Synapse")
    st.markdown(
        "An agentic AI system that identifies **non-obvious connections across scientific disciplines** "
        "to generate **testable research hypotheses**."
    )
    st.markdown("---")

   
    # Input
    st.markdown("### Provide Your Research Input")

    input_mode = st.radio("Input Type", ["Text Input", "PDF Upload"], horizontal=True)

    raw_text = ""

    if input_mode == "Text Input":
        raw_text = st.text_area(
            "Paste your research abstract, introduction, or idea",
            height=220,
            max_chars=2000,
            key="input_text"
        )
    else:
        uploaded_file = st.file_uploader("Upload a text-based research PDF", type=["pdf"])
        if uploaded_file:
            with st.spinner("Extracting text from PDF..."):
                raw_text = extract_text_from_pdf(uploaded_file)

    show_insights = st.toggle(
    "Show research insights",
    value=True,
    help="Highlights what makes each hypothesis novel or useful"
)


    if st.button("Generate Cross-Disciplinary Insights", use_container_width=True):

        if not raw_text or len(raw_text.strip()) < 50:
            st.warning("Please provide more substantial content.")
            st.stop()

        cleaned_text = clean_text(raw_text)[:2000]

        with st.spinner("Searching live research papers..."):
            search_query = normalize_intent(cleaned_text)
            papers = unified_search(search_query[:200], max_results=10)

        with st.spinner("Ranking papers..."):
            ranked_papers = rank_papers_by_similarity(
                query_text=cleaned_text,
                papers=papers,
                top_k=5
            )

        with st.spinner("Generating hypotheses..."):
            agent_output = cached_generate_hypotheses(
                cleaned_text, ranked_papers, 3
            )

        st.session_state.cleaned_text = cleaned_text
        st.session_state.ranked_papers = ranked_papers
        st.session_state.agent_output = agent_output
        st.session_state.refined_output = None   # FIX
        st.session_state.has_results = True
        st.session_state.iteration = 1

        st.rerun()



    # Initial Results
    if st.session_state.has_results and st.session_state.ranked_papers:

        st.markdown("---")
        st.markdown("### Top Relevant Research Papers")

        for i, paper in enumerate(st.session_state.ranked_papers[:5], start=1):

            title = paper.get("title", "Untitled")
            source = paper.get("source", "Unknown source")
            abstract = (paper.get("abstract") or "").strip()
            url = paper.get("url")

        # One-line abstract
            if abstract:
                one_liner = abstract.split(".")[0].strip() + "."
            else:
                one_liner = "Summary unavailable."

            st.markdown(f"**{i}. {title}**")
            st.caption(source)
            st.markdown(f"*{one_liner}*")

            if url:
                st.markdown(f"[View Paper]({url})")

            st.markdown("---")


        st.markdown(f"## Generated Research Hypotheses — Iteration 1")
        render_output = st.session_state.agent_output

        # ---------- RENDER FUNCTION ----------
        def render_hypotheses(output):
            raw = output.get("raw_text", "")
            blocks = raw.split('"id":')

            for idx, block in enumerate(blocks[1:], start=1):

        # ---- Extract title early for expander label ----
                title = f"Hypothesis {idx}"
                if '"title"' in block:
                    try:
                        title_text = block.split('"title":')[1].split('"')[1]
                        title = f"Hypothesis {idx}: {title_text}"
                    except:
                        pass

                with st.expander(title, expanded=False):

                    disciplines, evidence = [], []
                    hypothesis_text = ""

            # Disciplines
                    if '"disciplines"' in block:
                        try:
                            raw_d = block.split('"disciplines":')[1].split(']')[0]
                            disciplines = [
                            d.strip()
                                for d in raw_d.replace('[', '').replace('"', '').split(',')
                    ]
                            st.caption(f"Disciplines: {', '.join(disciplines)}")
                        except:
                            pass

            # Hypothesis
                    if '"hypothesis"' in block:
                        try:
                            hypothesis_text = block.split('"hypothesis":')[1].split('"')[1]
                            st.markdown(f"**Hypothesis:** {hypothesis_text}")
                        except:
                            pass

                    # ---- Recommendation Tag ----
                    if '"recommendation_tag"' in block:
                        try:
                            import re
                            label_match = re.search(r'"label"\s*:\s*"([^"]+)"', block)
                            reason_match = re.search(r'"reason"\s*:\s*"([^"]+)"', block)

                            if label_match and reason_match:
                                label = label_match.group(1)
                                reason = reason_match.group(1)

                            if label == "Most Recommended":
                                st.markdown(
                f"""
                <div style="padding:8px; border-left:5px solid #22c55e; 
                            background:#ecfdf5; margin-bottom:8px;">
                ⭐ <strong>{label}</strong><br>
                <span style="font-size:0.85rem;">{reason}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
                            else:
                                st.markdown(
                f"""
                <div style="padding:6px; border-left:4px solid #6366f1; 
                            background:#eef2ff; margin-bottom:6px;
                            font-size:0.85rem;">
                {label} — {reason}
                </div>
                """,
                                    unsafe_allow_html=True
            )
                        except:
                            pass

                    
                    if not hypothesis_text or len(hypothesis_text) < 20:
                        continue

                    # ---- Insight Badges (SAFE) ----
                    badge_result = generate_insight_badges(
                        hypothesis=hypothesis_text,
                        disciplines=disciplines,
                        papers=st.session_state.ranked_papers[:3]
                    )

                    badges = badge_result.get("badges", [])[:2]
                    if show_insights and len(badges) > 0:
                        st.markdown("**Insights**")
                        cols = st.columns(len(badges))
                        for col, badge in zip(cols, badges):
                            with col:
                                st.markdown(
                                    f"<span style='background:#eef2ff; padding:4px 8px; "
                                    f"border-radius:8px; font-size:0.75rem;' "
                                    f"title='{badge.get('explanation', '')}'>"
                                    f"{badge.get('label', '')}</span>",
                                    unsafe_allow_html=True  
)

            # Rationale
                    if '"rationale"' in block:
                        try:
                            rationale = block.split('"rationale":')[1].split('"')[1]
                            st.markdown(f"**Rationale:** {rationale}")
                        except:
                            pass
            # Evidence
                    if '"evidence"' in block:
                        try:
                            raw_e = block.split('"evidence":')[1].split(']')[0]
                            evidence = [
                                e.strip()
                                for e in raw_e.replace('[', '').replace('"', '').split(',')
                            ]
                            st.markdown(f"**Evidence:** {', '.join(evidence)}")
                        except:
                            pass

            # Confidence
                    confidence = compute_confidence(
                        hypothesis_text=hypothesis_text,
                        disciplines=disciplines,
                        evidence=evidence,
                        similarity_score=None
                    )

                    st.markdown(
                        f"**Confidence:** {confidence['label']} "
                        f"({confidence['confidence']})"
                    )
                
                

        # ---------- END RENDER FUNCTION ----------   
        render_hypotheses(render_output)

  

# ---- Suggested Next Focus (Agentic Planning Signal) ----
        raw_text = render_output.get("raw_text", "")

        focus_match = re.search(
            r'"suggested_next_focus"\s*:\s*"([^"]+)"',
    raw_text
)

        if focus_match:
            suggested_focus = focus_match.group(1)

            st.markdown(
        f"""
        <div style="padding:10px; border-left:5px solid #0ea5e9;
                    background:#f0f9ff; margin-bottom:16px;">
        🧭 <strong>Suggested next focus</strong><br>
        <span style="font-size:0.9rem;">{suggested_focus}</span>
        </div>
        """,
        unsafe_allow_html=True
    )


        # Continue Exploration
        st.markdown("### Continue Exploration")

        refinement_instruction = st.text_area(
            "Optional refinement or focus instruction",
            height=100
        )

        if st.button("Continue Exploration", disabled=st.session_state.iteration >= 3):
            refined_input = st.session_state.cleaned_text
            if refinement_instruction.strip():
                refined_input += "\n\nRefinement focus:\n" + refinement_instruction

            refined_output = cached_generate_hypotheses(
                refined_input,
                st.session_state.ranked_papers,
                2
            )

            st.session_state.refined_output = refined_output   
            st.session_state.iteration += 1
            st.rerun()

        #  NEW OUTPUT APPEARS BELOW 
        if st.session_state.refined_output:
            st.markdown("---")
            st.markdown(
                f"## Refined Research Hypotheses — Iteration {st.session_state.iteration}"
            )
            render_hypotheses(st.session_state.refined_output)

        if st.button("Start New Inquiry"):
            for k in [
                "iteration",
                "cleaned_text",
                "ranked_papers",
                "agent_output",
                "refined_output",
                "has_results",
                "input_text"
            ]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()

# Fixed Footer 
st.markdown(
    """
    <style>
    .fixed-footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: white;
        text-align: center;
        padding: 10px 24px;
        font-size: 0.8rem;
        color: #6b7280;
        border-top: 1px solid #e5e7eb;
        z-index: 999;
    }
    </style>

    <div class="fixed-footer">
        <strong>Disclaimer:</strong>
        Outputs are exploratory research hypotheses and not validated scientific conclusions.
        Evidence references may be incomplete or context-dependent.
        Confidence scores represent heuristic estimations of relevance, not empirical certainty.
        <br>
        © 2025 Silo Synapse. All rights reserved.
    </div>
    """,
    unsafe_allow_html=True
)
