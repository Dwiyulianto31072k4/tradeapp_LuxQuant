import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import re

# Set page config
st.set_page_config(
    page_title="Partial TP Calculator",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
    }
    .profit-text {
        color: #00ff00;
        font-weight: bold;
    }
    .loss-text {
        color: #ff0000;
        font-weight: bold;
    }
    .info-box {
        background-color: #e3f2fd;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #2196F3;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("🎯 Partial TP Calculator")
st.markdown("Hitung simulasi keuntungan dan kerugian dari strategi partial take profit")

# Initialize session state
if 'parsed_data' not in st.session_state:
    st.session_state.parsed_data = None

# Function to parse the trading signal text
def parse_trading_signal(text):
    """Parse trading signal text and extract relevant information"""
    try:
        data = {
            'symbol': None,
            'entry': None,
            'targets': [],
            'stop_losses': [],
            'volume_rank': None,
            'risk_level': None
        }
        
        # Extract symbol
        symbol_match = re.search(r'CALL:\s*(\w+)', text)
        if symbol_match:
            data['symbol'] = symbol_match.group(1)
        
        # Extract entry price
        entry_match = re.search(r'Entry:\s*([\d.]+)', text)
        if entry_match:
            data['entry'] = float(entry_match.group(1))
        
        # Extract volume rank
        volume_match = re.search(r'Volume.*Ranked:\s*(\d+)th/(\d+)', text)
        if volume_match:
            data['volume_rank'] = f"{volume_match.group(1)}/{volume_match.group(2)}"
        
        # Extract risk level
        risk_match = re.search(r'Risk Level:\s*([^\n]+)', text)
        if risk_match:
            data['risk_level'] = risk_match.group(1).strip()
        
        # Extract targets
        target_pattern = r'Target\s+(\d+)\s+([\d.]+)\s+([+-][\d.]+)%'
        target_matches = re.findall(target_pattern, text)
        for match in target_matches:
            data['targets'].append({
                'level': int(match[0]),
                'price': float(match[1]),
                'percentage': float(match[2])
            })
        
        # Extract stop losses
        sl_pattern = r'Stop Loss\s+(\d+)\s+([\d.]+)\s+([+-][\d.]+)%'
        sl_matches = re.findall(sl_pattern, text)
        for match in sl_matches:
            data['stop_losses'].append({
                'level': int(match[0]),
                'price': float(match[1]),
                'percentage': float(match[2])
            })
        
        return data
    except Exception as e:
        st.error(f"Error parsing signal: {str(e)}")
        return None

# Main layout
col1, col2 = st.columns([1, 2])

with col1:
    st.header("📥 Input Trading Signal")
    
    # Text area for signal input
    signal_text = st.text_area(
        "Paste trading signal disini:",
        height=300,
        placeholder="""🆕 NEW CALL: TOKENUSDT 🆕
📊 Risk Analysis 📊
Volume(24H) Ranked: 408th/489
Risk Level: ⚠️ High
Entry: 0.0241
📝 Targets & Stop Loss
---------------------------------------
Level      Price    % Change from Entry
---------------------------------------
Target 1   0.0245   +1.66%
Target 2   0.0249   +3.32%
..."""
    )
    
    # Example button
    if st.button("📋 Load Example"):
        signal_text = """🆕 NEW CALL: JELLYJELLYUSDT 🆕
📊 Risk Analysis 📊
Volume(24H) Ranked: 408th/489
Risk Level: ⚠️ High
Entry: 0.0241
📝 Targets & Stop Loss
---------------------------------------
Level      Price    % Change from Entry
---------------------------------------
Target 1   0.0245   +1.66%
Target 2   0.0249   +3.32%
Target 3   0.0261   +8.30%
Target 4   0.0281   +16.60%
Stop Loss 1 0.0233  -3.32%
Stop Loss 2 0.0208  -13.69%
---------------------------------------"""
        st.rerun()
    
    # Parse button
    if st.button("🔍 Parse Signal", type="primary"):
        if signal_text:
            parsed = parse_trading_signal(signal_text)
            if parsed and parsed['entry'] and len(parsed['targets']) > 0:
                st.session_state.parsed_data = parsed
                st.success("✅ Signal parsed successfully!")
            else:
                st.error("❌ Failed to parse signal. Please check the format.")
        else:
            st.warning("⚠️ Please paste a trading signal first.")
    
    # Additional inputs
    st.markdown("---")
    st.subheader("💰 Trading Configuration")
    
    # Trading mode
    trading_mode = st.radio("Mode Trading", ["Spot", "Futures"])
    
    # Modal
    modal = st.number_input("Modal (IDR)", min_value=100000, value=10000000, step=100000)
    
    # Leverage (only for futures)
    leverage = 1
    if trading_mode == "Futures":
        leverage = st.number_input("Leverage", min_value=1, max_value=125, value=10)
    
    # TP distribution
    st.subheader("📊 Distribusi Take Profit")
    
    # Default distribution options
    distribution_type = st.radio(
        "Metode Distribusi",
        ["Equal (Rata)", "Aggressive (Front-loaded)", "Conservative (Back-loaded)", "Custom"]
    )

with col2:
    if st.session_state.parsed_data:
        data = st.session_state.parsed_data
        
        # Display parsed information
        st.header("📊 Signal Analysis")
        
        # Info box
        st.markdown(f"""
        <div class="info-box">
            <strong>Symbol:</strong> {data['symbol']}<br>
            <strong>Entry Price:</strong> {data['entry']}<br>
            <strong>Volume Rank:</strong> {data['volume_rank']}<br>
            <strong>Risk Level:</strong> {data['risk_level']}
        </div>
        """, unsafe_allow_html=True)
        
        # Calculate position size
        effective_modal = modal * leverage
        position_size = effective_modal / data['entry']
        
        # Determine TP percentages based on distribution type
        num_targets = len(data['targets'])
        if distribution_type == "Equal (Rata)":
            tp_percentages = [100/num_targets] * num_targets
        elif distribution_type == "Aggressive (Front-loaded)":
            # More weight on early TPs
            if num_targets == 2:
                tp_percentages = [70, 30]
            elif num_targets == 3:
                tp_percentages = [50, 30, 20]
            else:  # 4 targets
                tp_percentages = [40, 30, 20, 10]
        elif distribution_type == "Conservative (Back-loaded)":
            # More weight on later TPs
            if num_targets == 2:
                tp_percentages = [30, 70]
            elif num_targets == 3:
                tp_percentages = [20, 30, 50]
            else:  # 4 targets
                tp_percentages = [10, 20, 30, 40]
        else:  # Custom
            tp_percentages = []
            st.markdown("#### Custom Distribution")
            cols = st.columns(num_targets)
            remaining = 100
            for i in range(num_targets):
                with cols[i]:
                    if i == num_targets - 1:  # Last TP
                        pct = remaining
                        st.metric(f"TP{i+1}", f"{pct}%")
                    else:
                        pct = st.number_input(
                            f"TP{i+1} (%)",
                            min_value=1,
                            max_value=remaining,
                            value=min(30, remaining),
                            key=f"custom_tp_{i}"
                        )
                        remaining -= pct
                    tp_percentages.append(pct)
        
        # Calculate results
        results = []
        cumulative_profit = 0
        
        for i, target in enumerate(data['targets']):
            size_at_tp = position_size * (tp_percentages[i] / 100)
            sell_value = size_at_tp * target['price']
            cost_basis = size_at_tp * data['entry']
            profit = sell_value - cost_basis
            cumulative_profit += profit
            
            results.append({
                "Level": f"TP{target['level']}",
                "Target Price": target['price'],
                "% Dari Entry": target['percentage'],
                "% Posisi": tp_percentages[i],
                "Jumlah Unit": size_at_tp,
                "Nilai Jual (IDR)": sell_value,
                "Profit (IDR)": profit,
                "Kumulatif Profit": cumulative_profit
            })
        
        # Calculate stop losses
        sl_results = []
        for sl in data['stop_losses']:
            loss = (sl['price'] - data['entry']) * position_size
            sl_results.append({
                "Level": f"SL{sl['level']}",
                "Price": sl['price'],
                "% Change": sl['percentage'],
                "Loss (IDR)": loss,
                "Loss %": (loss / modal) * 100
            })
        
        # Display metrics
        st.header("💰 Ringkasan Hasil")
        
        metric_cols = st.columns(4)
        
        with metric_cols[0]:
            st.metric("Modal Efektif", f"Rp {effective_modal:,.0f}")
            st.metric("Position Size", f"{position_size:,.4f}")
        
        with metric_cols[1]:
            total_profit = sum([r["Profit (IDR)"] for r in results])
            roi = (total_profit / modal) * 100
            st.metric("Total Profit (All TP)", f"Rp {total_profit:,.0f}", f"{roi:.2f}%")
        
        with metric_cols[2]:
            # Partial scenario
            partial_profit = 0
            if len(results) >= 2:
                partial_profit = results[0]["Profit (IDR)"] + results[1]["Profit (IDR)"]
            partial_roi = (partial_profit / modal) * 100
            st.metric("Profit (TP1 & TP2)", f"Rp {partial_profit:,.0f}", f"{partial_roi:.2f}%")
        
        with metric_cols[3]:
            if sl_results:
                primary_sl = sl_results[0]
                st.metric("Primary SL", f"Rp {primary_sl['Loss (IDR)']:,.0f}", 
                         f"{primary_sl['Loss %']:.2f}%", delta_color="inverse")
        
        # Risk Reward Ratio
        if sl_results:
            risk_reward = abs(total_profit / sl_results[0]['Loss (IDR)'])
            st.info(f"**Risk/Reward Ratio**: 1:{risk_reward:.2f}")
        
        # Results table
        st.header("📋 Tabel Rincian Take Profit")
        df_results = pd.DataFrame(results)
        
        # Format for display
        df_display = df_results.copy()
        df_display["Target Price"] = df_display["Target Price"].apply(lambda x: f"{x:.4f}")
        df_display["% Dari Entry"] = df_display["% Dari Entry"].apply(lambda x: f"{x:+.2f}%")
        df_display["% Posisi"] = df_display["% Posisi"].apply(lambda x: f"{x:.1f}%")
        df_display["Jumlah Unit"] = df_display["Jumlah Unit"].apply(lambda x: f"{x:.4f}")
        df_display["Nilai Jual (IDR)"] = df_display["Nilai Jual (IDR)"].apply(lambda x: f"Rp {x:,.0f}")
        df_display["Profit (IDR)"] = df_display["Profit (IDR)"].apply(lambda x: f"Rp {x:,.0f}")
        df_display["Kumulatif Profit"] = df_display["Kumulatif Profit"].apply(lambda x: f"Rp {x:,.0f}")
        
        st.dataframe(df_display, use_container_width=True)
        
        # Stop Loss table
        if sl_results:
            st.header("🛑 Tabel Stop Loss")
            df_sl = pd.DataFrame(sl_results)
            df_sl["Price"] = df_sl["Price"].apply(lambda x: f"{x:.4f}")
            df_sl["% Change"] = df_sl["% Change"].apply(lambda x: f"{x:.2f}%")
            df_sl["Loss (IDR)"] = df_sl["Loss (IDR)"].apply(lambda x: f"Rp {x:,.0f}")
            df_sl["Loss %"] = df_sl["Loss %"].apply(lambda x: f"{x:.2f}%")
            st.dataframe(df_sl, use_container_width=True)
        
        # Visualizations
        st.header("📈 Visualisasi")
        
        viz_cols = st.columns(2)
        
        with viz_cols[0]:
            # Bar chart for profits
            fig_bar = px.bar(df_results, 
                            x="Level", 
                            y="Profit (IDR)",
                            title="Profit per Level TP",
                            color="Profit (IDR)",
                            color_continuous_scale="Viridis")
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with viz_cols[1]:
            # Pie chart for distribution
            fig_pie = px.pie(values=tp_percentages, 
                           names=[f"TP{i+1}" for i in range(len(tp_percentages))],
                           title="Distribusi Posisi per TP")
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Price levels chart
        st.subheader("📊 Level Harga")
        
        fig_levels = go.Figure()
        
        # Add entry line
        fig_levels.add_hline(y=data['entry'], line_dash="dash", line_color="blue", 
                            annotation_text=f"Entry: {data['entry']:.4f}")
        
        # Add TP lines
        for i, target in enumerate(data['targets']):
            fig_levels.add_hline(y=target['price'], line_dash="solid", line_color="green",
                               annotation_text=f"TP{target['level']}: {target['price']:.4f} ({tp_percentages[i]:.1f}%)")
        
        # Add SL lines
        for sl in data['stop_losses']:
            color = "red" if sl['level'] == 1 else "orange"
            fig_levels.add_hline(y=sl['price'], line_dash="solid", line_color=color,
                               annotation_text=f"SL{sl['level']}: {sl['price']:.4f}")
        
        # Configure layout
        all_prices = [data['entry']] + [t['price'] for t in data['targets']] + [sl['price'] for sl in data['stop_losses']]
        price_range = max(all_prices) - min(all_prices)
        
        fig_levels.update_layout(
            title="Level Entry, TP, dan SL",
            yaxis_title="Price",
            height=500,
            yaxis=dict(range=[min(all_prices) - price_range*0.1, max(all_prices) + price_range*0.1])
        )
        
        st.plotly_chart(fig_levels, use_container_width=True)
        
        # Scenario Analysis
        st.header("🎲 Analisis Skenario")
        
        scenario_cols = st.columns(2)
        
        with scenario_cols[0]:
            st.subheader("✅ Skenario Profit")
            for i, result in enumerate(results):
                cumulative = result["Kumulatif Profit"]
                cumulative_roi = (cumulative / modal) * 100
                if i == 0:
                    st.info(f"Mencapai TP{i+1}: **Rp {cumulative:,.0f}** ({cumulative_roi:.2f}% ROI)")
                elif i == 1:
                    st.success(f"Mencapai TP{i+1}: **Rp {cumulative:,.0f}** ({cumulative_roi:.2f}% ROI)")
                else:
                    st.success(f"Mencapai TP{i+1}: **Rp {cumulative:,.0f}** ({cumulative_roi:.2f}% ROI)")
        
        with scenario_cols[1]:
            st.subheader("❌ Skenario Loss")
            for sl in sl_results:
                if sl['Level'] == 'SL1':
                    st.error(f"{sl['Level']}: **Rp {sl['Loss (IDR)']:,.0f}** ({sl['Loss %']:.2f}% Loss)")
                else:
                    st.warning(f"{sl['Level']}: **Rp {sl['Loss (IDR)']:,.0f}** ({sl['Loss %']:.2f}% Loss)")
        
        # Export section
        st.header("💾 Export Data")
        
        export_cols = st.columns(3)
        
        with export_cols[0]:
            # CSV export
            export_data = {
                "Symbol": data['symbol'],
                "Risk Level": data['risk_level'],
                "Trading Mode": trading_mode,
                "Modal": modal,
                "Leverage": leverage,
                "Entry Price": data['entry'],
                "Position Size": position_size,
                "Total Profit": total_profit,
                "ROI %": roi
            }
            
            # Add TP details
            for i, (target, pct) in enumerate(zip(data['targets'], tp_percentages)):
                export_data[f"TP{i+1} Price"] = target['price']
                export_data[f"TP{i+1} %"] = pct
                export_data[f"TP{i+1} Profit"] = results[i]["Profit (IDR)"]
            
            # Add SL details
            for sl in sl_results:
                export_data[f"{sl['Level']} Price"] = sl['Price']
                export_data[f"{sl['Level']} Loss"] = sl['Loss (IDR)']
            
            export_df = pd.DataFrame([export_data])
            csv = export_df.to_csv(index=False)
            
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"{data['symbol']}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with export_cols[1]:
            # Text report
            report = f"""
PARTIAL TP CALCULATOR REPORT
========================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SIGNAL INFORMATION:
- Symbol: {data['symbol']}
- Risk Level: {data['risk_level']}
- Volume Rank: {data['volume_rank']}

CONFIGURATION:
- Trading Mode: {trading_mode}
- Modal: Rp {modal:,.0f}
- Leverage: {leverage}x
- Entry Price: {data['entry']:.4f}
- Position Size: {position_size:.4f}

TAKE PROFIT LEVELS:
"""
            for i, (target, result) in enumerate(zip(data['targets'], results)):
                report += f"- TP{target['level']}: {target['price']:.4f} ({tp_percentages[i]:.1f}% position) = Rp {result['Profit (IDR)']:,.0f}\n"
            
            report += f"\nSTOP LOSS LEVELS:\n"
            for sl in sl_results:
                report += f"- {sl['Level']}: {sl['Price']:.4f} = Rp {sl['Loss (IDR)']:,.0f} ({sl['Loss %']:.2f}% loss)\n"
            
            report += f"""
SUMMARY:
- Total Profit (All TP): Rp {total_profit:,.0f} ({roi:.2f}% ROI)
- Risk/Reward Ratio: 1:{risk_reward:.2f}
- Distribution Method: {distribution_type}
"""
            
            st.download_button(
                label="📄 Download Report",
                data=report,
                file_name=f"{data['symbol']}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
    else:
        # Show instructions when no data is parsed
        st.info("""
        ### 📝 Cara Menggunakan:
        
        1. **Copy & Paste** trading signal ke text area di sebelah kiri
        2. Klik tombol **"🔍 Parse Signal"** untuk menganalisis signal
        3. Atur **modal** dan **mode trading** (Spot/Futures)
        4. Pilih **metode distribusi** untuk partial TP:
           - **Equal**: Pembagian rata untuk setiap TP
           - **Aggressive**: Lebih banyak di TP awal
           - **Conservative**: Lebih banyak di TP akhir
           - **Custom**: Atur sendiri persentasenya
        5. Lihat hasil analisis dan download report
        
        ### 📊 Format Signal yang Didukung:
        Signal harus mengandung informasi:
        - Symbol/Pair (contoh: JELLYJELLYUSDT)
        - Entry price
        - Target prices dengan persentase
        - Stop loss prices dengan persentase
        
        Klik **"📋 Load Example"** untuk melihat contoh format yang benar.
        """)

# Footer
st.markdown("---")
st.markdown("💡 **Tips**: Gunakan distribusi 'Conservative' untuk aset high risk, dan 'Aggressive' untuk aset yang lebih stabil.")
