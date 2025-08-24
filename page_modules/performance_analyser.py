import streamlit as st
from core.database import get_score_history, get_daily_scores, get_weekly_progress, get_score_statistics
from core.database_supabase import SupabaseDB
import altair as alt
import pandas as pd

supabase_client = SupabaseDB()

def analyse():
    st.divider()
    st.markdown("#### 📊 Analysis")
    
    # Get data from Supabase and check availability
    try:
        stats = supabase_client.get_score_statistics()
        if not stats or stats.get('total_attempts', 0) == 0:
            st.info("Complete some translations to see your progress")
            return
    except Exception as e:
        st.error(f"Error loading statistics: {e}")
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
    try:
        df = supabase_client.get_score_history()
        if df.empty:
            st.info("No score history available yet")
            return
    except Exception as e:
        st.error(f"Error loading score history: {e}")
        return
        
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
    
    # Daily Variation Box Plot - NEW SECTION
    st.divider()
    st.markdown("#### 📦 Daily Score Variation (Last 5 Days)")
    
    try:
        # Get individual scores with dates for last 5 days
        # Using get_score_history() which should have individual records
        recent_df = supabase_client.get_score_history()
        if not recent_df.empty:
            # Handle different possible date column names from your schema
            date_col = None
            if 'checked_on' in recent_df.columns:
                date_col = 'checked_on'
            elif 'date' in recent_df.columns:
                date_col = 'date'
            elif 'created_at' in recent_df.columns:
                date_col = 'created_at'
                
            if date_col:
                recent_df[date_col] = pd.to_datetime(recent_df[date_col])
                
                # Filter for last 5 days
                cutoff_date = recent_df[date_col].max() - pd.Timedelta(days=4)
                recent_df = recent_df[recent_df[date_col] >= cutoff_date].copy()
                
                # Create day label and date for sorting
                recent_df['day'] = recent_df[date_col].dt.strftime('%a %m/%d')
                recent_df['date_only'] = recent_df[date_col].dt.date
                
                # Group by day to see how many days we have
                daily_groups = recent_df.groupby('date_only').size()
                
                if len(daily_groups) >= 2:  # Show if we have at least 2 days
                    # Box plot
                    box_plot = alt.Chart(recent_df).configure(
                        background='transparent'
                    ).configure_view(
                        strokeWidth=0
                    ).mark_boxplot(
                        size=50,
                        color='#4A90E2',
                        opacity=0.7
                    ).encode(
                        x=alt.X('day:O', title="Day", sort=alt.Sort(field='date_only')),
                        y=alt.Y(f'{score_col}:Q', title="Score", scale=alt.Scale(domain=[0, 10])),
                        tooltip=['day:O', f'{score_col}:Q']
                    ).properties(height=250)
                    
                    st.altair_chart(box_plot, use_container_width=True)
                    
                    # Quick insights
                    daily_stats = recent_df.groupby(['day', 'date_only'])[score_col].agg(['mean', 'std', 'count']).round(1)
                    daily_stats = daily_stats.reset_index()
                    
                    if len(daily_stats) > 1:
                        most_consistent_day = daily_stats.loc[daily_stats['std'].idxmin(), 'day']
                        most_variable_day = daily_stats.loc[daily_stats['std'].idxmax(), 'day']
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.caption(f"🎯 Most consistent: {most_consistent_day}")
                        with col2:
                            st.caption(f"🎲 Most variable: {most_variable_day}")
                    
                    # Show summary stats
                    st.caption(f"📊 Showing {len(recent_df)} attempts across {len(daily_groups)} days")
                else:
                    st.info("Need attempts from at least 2 different days for box plot")
            else:
                st.info("Date information not available for box plot")
        else:
            st.info("No recent data available for box plot")
    except Exception as e:
        st.error(f"Error creating box plot: {e}")
    
    # Time-based progress - simplified
    with st.expander("📅 Progress Over Time", expanded=False):
        try:
            daily_df = supabase_client.get_daily_scores()
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
        except Exception as e:
            st.error(f"Error loading daily scores: {e}")
    
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
    
    # Attempts per day over whole period
    with st.expander("📊 Daily Attempt Frequency", expanded=False):
        try:
            daily_df = supabase_client.get_daily_scores()
            if not daily_df.empty:
                daily_df['date'] = pd.to_datetime(daily_df['date'])
                daily_df = daily_df.sort_values('date')
                
                # Bar chart showing attempts per day
                attempts_chart = alt.Chart(daily_df).configure(
                    background='transparent'
                ).configure_view(
                    strokeWidth=0
                ).mark_bar(
                    cornerRadiusTopLeft=3,
                    cornerRadiusTopRight=3
                ).encode(
                    x=alt.X('date:T', title="Date"),
                    y=alt.Y('attempt_count:Q', title="Attempts per Day"),
                    color=alt.Color('attempt_count:Q', scale=alt.Scale(scheme='blues'), legend=None),
                    tooltip=['date:T', 'attempt_count:Q', 'avg_score:Q']
                ).properties(height=250)
                
                st.altair_chart(attempts_chart, use_container_width=True)
                
                # Summary statistics
                total_days = len(daily_df)
                total_attempts = daily_df['attempt_count'].sum()
                avg_attempts_per_day = daily_df['attempt_count'].mean()
                most_active_day = daily_df.loc[daily_df['attempt_count'].idxmax()]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Active Days", total_days)
                with col2:
                    st.metric("Avg/Day", f"{avg_attempts_per_day:.1f}")
                with col3:
                    st.metric("Best Day", int(most_active_day['attempt_count']))
                
                st.caption(f"📅 Most active day: {most_active_day['date'].strftime('%A, %b %d')} with {int(most_active_day['attempt_count'])} attempts")
                
            else:
                st.info("No daily attempt data available")
        except Exception as e:
            st.error(f"Error loading attempt frequency data: {e}")

if __name__ == "__main__":
    analyse()