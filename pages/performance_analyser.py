import streamlit as st
from core.database import get_score_history, get_daily_scores, get_weekly_progress, get_score_statistics
import altair as alt
import pandas as pd

def analyse():
    st.title("📊 Analysis")
    
    # Get data once and check availability
    stats = get_score_statistics()
    if not stats or stats.get('total_attempts', 0) == 0:
        st.info("Complete some translations to see your progress")
        return
    
    # Overview metrics - clean and simple
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Attempts", stats.get('total_attempts', 0))
    with col2:
        st.metric("Average", f"{stats.get('overall_avg', 0):.1f}")
    with col3:
        st.metric("Best", stats.get('max_score', 0))
    
    st.divider()
    
    # Score progression - single clean chart
    df = get_score_history()
    if not df.empty:
        score_col = 'score' if 'score' in df.columns else 'Score'
        if score_col not in df.columns:
            st.error("Score data unavailable")
            return
            
        df["attempt"] = range(1, len(df) + 1)
        
        # Create base chart with transparent background
        base = alt.Chart(df).properties(height=300)
        
        # Scatter plot layer
        scatter = base.mark_circle(
            size=60,
            opacity=0.8,
            stroke='white',
            strokeWidth=1
        ).encode(
            x=alt.X("attempt:O", title="Attempt"),
            y=alt.Y(f"{score_col}:Q", title="Score", scale=alt.Scale(domain=[0, 10])),
            color=alt.Color(
                f"{score_col}:Q", 
                scale=alt.Scale(scheme='blues', domain=[0, 10]),
                legend=None
            ),
            tooltip=["attempt", score_col]
        )
        
        # Trend line layer
        trend = base.transform_regression(
            "attempt", score_col
        ).mark_line(
            color="#ff6b6b", 
            strokeWidth=3,
            opacity=0.8
        ).encode(
            x=alt.X("attempt:O"),
            y=alt.Y(f"{score_col}:Q")
        )
        
        # Combine layers and configure
        chart = (scatter + trend).resolve_scale(
            color='independent'
        ).configure(
            background='transparent'
        ).configure_view(
            strokeWidth=0
        )
        
        st.altair_chart(chart, use_container_width=True)
        
        # Simple stats below chart
        improvement = df[score_col].iloc[-5:].mean() - df[score_col].iloc[:5].mean() if len(df) >= 10 else 0
        if improvement > 0:
            st.success(f"↗️ Improved by {improvement:.1f} points")
        elif improvement < -2:
            st.warning(f"↘️ Decreased by {abs(improvement):.1f} points")
        else:
            st.info("📊 Performance stable")
    
    # Time-based progress - simplified
    with st.expander("📅 Progress Over Time", expanded=False):
        daily_df = get_daily_scores()
        if not daily_df.empty:
            daily_df['date'] = pd.to_datetime(daily_df['date'])
            daily_df = daily_df.sort_values('date').tail(30)  # Last 30 days only
            
            daily_chart = alt.Chart(daily_df).configure(
                background='transparent'
            ).configure_view(
                strokeWidth=0
            ).mark_bar(
                cornerRadiusTopLeft=3,
                cornerRadiusTopRight=3
            ).encode(
                x=alt.X('date:T', title=None),
                y=alt.Y('avg_score:Q', title="Daily Avg", scale=alt.Scale(domain=[0, 10])),
                color=alt.Color('avg_score:Q', scale=alt.Scale(scheme='blues'), legend=None),
                tooltip=['date:T', 'avg_score:Q', 'attempt_count:Q']
            ).properties(height=200)
            
            st.altair_chart(daily_chart, use_container_width=True)
        else:
            st.info("No daily data yet")
    
    # Score distribution - minimal histogram
    with st.expander("📈 Score Distribution", expanded=False):
        if not df.empty:
            hist = alt.Chart(df).configure(
                background='transparent'
            ).configure_view(
                strokeWidth=0
            ).mark_bar(
                cornerRadiusTopLeft=2,
                cornerRadiusTopRight=2
            ).encode(
                x=alt.X(f'{score_col}:Q', bin=alt.Bin(maxbins=15), title="Score"),
                y=alt.Y('count()', title="Count"),
                color=alt.value('#4A90E2'),
                opacity=alt.value(0.7)
            ).properties(height=250)
            
            st.altair_chart(hist, use_container_width=True)
            
            # Quick stats
            median_score = df[score_col].median()
            st.caption(f"Median score: {median_score:.1f} | Most common range: {int(median_score//10)*10}-{int(median_score//10)*10+10}")

if __name__ == "__main__":
    analyse()