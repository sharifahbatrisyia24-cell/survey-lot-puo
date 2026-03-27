import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Polygon, Point
import numpy as np
import folium
from streamlit_folium import st_folium
from pyproj import Transformer
import json

# 1. Konfigurasi Halaman
st.set_page_config(page_title="SISTEM SURVEY LOT | PUO", layout="wide")

# --- SISTEM LOG MASUK ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
    st.session_state['user_display'] = ""

def login():
    st.markdown("""
        <div style="text-align: center; padding: 20px;">
            <h1 style="font-size: 50px; margin-bottom: 0;">🔐</h1>
            <h2 style="color: #1f2937; margin-top: 0;">Sistem Survey Lot PUO</h2>
            <p>Sila masukkan Username (Nombor) dan Kata Laluan</p>
        </div>
    """, unsafe_allow_html=True)
    
    users = {"1": "Aleeya", "2": "Izatul", "3": "Faseha"}
    
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        with st.container(border=True):
            username_input = st.text_input("👤 Masukkan ID:")
            password_input = st.text_input("🔑 Masukkan Kata Laluan:", type="password")
            
            if st.button("Log Masuk", use_container_width=True):
                if password_input == "admin123" and username_input in users:
                    st.session_state['authenticated'] = True
                    st.session_state['user_display'] = users[username_input]
                    st.rerun()
                else:
                    st.error("Username atau Kata Laluan Salah!")
            
            st.markdown("""
                <div style="text-align: center; margin-top: 15px; border-top: 1px solid #eee; padding-top: 15px;">
                    <a href="#" style="text-decoration: none; color: #ef4444; font-weight: bold;">
                        <span style="color: red;">❓</span> Lupa Kata Laluan?
                    </a>
                </div>
            """, unsafe_allow_html=True)

if not st.session_state['authenticated']:
    login()
    st.stop()

# --- 2. SIDEBAR (LOGO & TETAPAN) ---
with st.sidebar:
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #00b4ff, #0080ff); 
                    padding: 30px; 
                    border-radius: 15px; 
                    text-align: center; 
                    color: white; 
                    margin-bottom: 20px;">
            <div style="font-size: 50px; margin-bottom: 10px;">👤</div>
            <h2 style="margin: 0; font-size: 24px;">Hai, {st.session_state['user_display'].upper()}!</h2>
            <p style="margin: 5px 0 0 0; opacity: 0.9;">{st.session_state['user_display']}</p>
        </div>
    """, unsafe_allow_html=True)
        
    st.header("⚙️ Kawalan Paparan")
    st_marker_size = st.slider("Saiz Marker Stesen", 5, 50, 22)
    st_line_weight = st.slider("Ketebalan Garisan", 1, 20, 3) 
    st_text_size = st.slider("Saiz Bearing/Jarak", 5, 30, 10)
    st_zoom_level = st.slider("Tahap Zoom", 10, 22, 19)
    poly_color = st.color_picker("Warna Poligon", "#FFFF00") 
    
    st.divider()
    epsg_code = st.text_input("🌐 Kod EPSG:", value="4390")
    st.divider()

# --- 3. BAHAGIAN UTAMA (HEADER) ---
col_logo, col_title = st.columns([0.2, 0.8]) 

with col_logo:
    try:
        st.image("logo politeknik 2.png", use_container_width=True) 
    except:
        st.warning("Fail logo tidak dijumpai.")

with col_title:
    st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 22px; border-left: 10px solid #007bff; border-radius: 10px; height: 160px; display: flex; flex-direction: column; justify-content: center;">
            <h1 style="margin: 0; color: #1f2937; font-family: sans-serif; font-size: 2.5rem;">SISTEM SURVEY LOT</h1>
            <p style="margin: 0; color: #6b7280; font-size: 1.2rem; font-family: sans-serif;">Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p>
        </div>
        """, unsafe_allow_html=True)

st.write("") 

# 4. Fungsi Penukaran DMS
def dd_to_dms(dd):
    dd = abs(dd)
    minutes, seconds = divmod(dd * 3600, 60)
    degrees, minutes = divmod(minutes, 60)
    return f"{int(degrees)}° {int(minutes):02d}' {int(seconds):02d}\""

# 5. Ruang Muat Naik
uploaded_file = st.file_uploader("📂 Muat naik fail CSV (STN, E, N)", type=['csv'])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip()
        
        if 'E' in df.columns and 'N' in df.columns:
            coords = list(zip(df['E'], df['N']))
            if len(coords) < 3:
                st.error("Ralat: Perlu sekurang-kurangnya 3 stesen untuk membentuk poligon.")
            else:
                poly_geom = Polygon(coords)
                gdf_poly = gpd.GeoDataFrame(index=[0], geometry=[poly_geom])
                luas = poly_geom.area
                perimeter = poly_geom.length
                centroid = poly_geom.centroid

                # 6. PAPARAN METRIK
                st.subheader("📊 Statistik Kawasan")
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("Luas Keseluruhan", f"{luas:,.2f} m²")
                col_m2.metric("Perimeter (Parameter)", f"{perimeter:,.2f} m")
                col_m3.metric("Bilangan Stesen", len(df))

                # 7. VISUALISASI MATPLOTLIB
                with st.expander("🖼️ Lihat Pelan Poligon (Standard Ukur)", expanded=False):
                    fig, ax = plt.subplots(figsize=(10, 10))
                    gdf_poly.plot(ax=ax, facecolor=poly_color, edgecolor='blue', alpha=0.3, linewidth=st_line_weight)
                    ax.scatter(df['E'], df['N'], color='black', s=st_marker_size, zorder=5)

                    num_points = len(df)
                    line_data = [] 
                    for i in range(num_points):
                        p1 = df.iloc[i]
                        p2 = df.iloc[(i + 1) % num_points]
                        dist = np.sqrt((p2['E'] - p1['E'])**2 + (p2['N'] - p1['N'])**2)
                        angle_rad = np.arctan2(p2['E'] - p1['E'], p2['N'] - p1['N'])
                        bearing_val = np.degrees(angle_rad) if angle_rad >= 0 else (np.degrees(angle_rad) + 360)
                        bearing_dms = dd_to_dms(bearing_val)
                        line_data.append({'bearing': bearing_dms, 'dist': dist, 'angle': bearing_val})
                        mid_e, mid_n = (p1['E'] + p2['E']) / 2, (p1['N'] + p2['N']) / 2
                        ax.text(mid_e, mid_n, f"{bearing_dms}\n{dist:.2f}m", fontsize=st_text_size, color='darkblue', 
                                ha='center', va='center', bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))
                        ax.text(p1['E'], p1['N'] + 0.5, f"{int(p1['STN'])}", fontsize=10, fontweight='bold', color='red')
                    
                    # PAPARAN LUAS & PARAMETER DI TENGAH PELAN
                    ax.text(centroid.x, centroid.y, f"LUAS: {luas:,.2f} m²\nP: {perimeter:,.2f}m", 
                            fontsize=st_text_size+2, fontweight='bold', ha='center',
                            bbox=dict(facecolor='white', alpha=0.8, edgecolor='black'))

                    ax.set_aspect('equal')
                    st.pyplot(fig)

                # 8. GEOSATELIT INTERAKTIF
                st.divider()
                st.markdown("### 🌍 Pandangan Geosatelit Interaktif")
                try:
                    transformer = Transformer.from_crs(f"EPSG:{epsg_code}", "EPSG:4326", always_xy=True)
                    lon_list, lat_list = transformer.transform(df['E'].values, df['N'].values)
                    df['lat'], df['lon'] = lat_list, lon_list
                    
                    center_lat, center_lon = np.mean(lat_list), np.mean(lon_list)
                    m = folium.Map(location=[center_lat, center_lon], zoom_start=st_zoom_level, max_zoom=28, control_scale=True)
                    
                    folium.TileLayer(
                        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
                        attr='Google', name='Google Satellite (Hybrid)', overlay=False, control=True,
                        max_zoom=22, max_native_zoom=18
                    ).add_to(m)

                    folium.Polygon(
                        locations=list(zip(lat_list, lon_list)),
                        color="white", weight=st_line_weight, fill=True, fill_color=poly_color, fill_opacity=0.4,
                        popup=folium.Popup(f"<b>INFO LOT</b><hr>LUAS: {luas:,.2f} m²<br>PARAMETER: {perimeter:,.2f} m", max_width=250),
                        tooltip="Klik untuk Info Lot"
                    ).add_to(m)

                    folium.map.Marker(
                        [center_lat, center_lon],
                        icon=folium.DivIcon(html=f"""<div style="font-family: sans-serif; color: white; font-weight: bold; font-size: 11pt; text-shadow: 2px 2px #000; width: 160px; margin-left: -80px; text-align: center;">LUAS: {luas:,.2f} m²<br>P: {perimeter:,.2f}m</div>""")
                    ).add_to(m)

                    for i in range(num_points):
                        p1_coords = [df.iloc[i]['lat'], df.iloc[i]['lon']]
                        p2_coords = [df.iloc[(i + 1) % num_points]['lat'], df.iloc[(i + 1) % num_points]['lon']]
                        folium.PolyLine(locations=[p1_coords, p2_coords], color="white", weight=st_line_weight+1, opacity=0.8).add_to(m)
                        mid_lat, mid_lon = (p1_coords[0] + p2_coords[0]) / 2, (p1_coords[1] + p2_coords[1]) / 2
                        current_bearing = line_data[i]['angle']
                        rotation = 90 - current_bearing
                        if rotation < -90: rotation += 180
                        if rotation > 90: rotation -= 180
                        
                        label_text = f"{line_data[i]['bearing']}<br>{line_data[i]['dist']:.2f}m"
                        folium.map.Marker(
                            [mid_lat, mid_lon],
                            icon=folium.DivIcon(html=f"""<div style="font-family: sans-serif; color: #00FFFF; font-weight: bold; font-size: {st_text_size}pt; text-shadow: 1px 1px #000; transform: rotate({-rotation}deg); width: 150px; margin-left: -75px; text-align: center; white-space: nowrap;">{label_text}</div>""")
                        ).add_to(m)

                    # MARKER STESEN - BOLE TEKAN UNTUK INFO
                    for _, row in df.iterrows():
                        popup_info = f"<b>Stesen: {int(row['STN'])}</b><br>E: {row['E']}<br>N: {row['N']}"
                        folium.CircleMarker(
                            location=[row['lat'], row['lon']],
                            radius=6, color="white", weight=1, fill=True, fill_color="red", fill_opacity=1,
                            popup=folium.Popup(popup_info, max_width=200) # Klik untuk papar maklumat
                        ).add_to(m)
                        
                        folium.map.Marker(
                            [row['lat'], row['lon']],
                            icon=folium.DivIcon(html=f"""<div style="font-family: sans-serif; color: yellow; font-weight: bold; font-size: 14pt; text-shadow: 2px 2px #000; width: 40px; margin-left: -10px; margin-top: -20px;">{int(row['STN'])}</div>""")
                        ).add_to(m)

                    st_folium(m, width="100%", height=600, returned_objects=[])
                except Exception as e:
                    st.error(f"Ralat pemprosesan peta: {e}")

                # 9. EKSPORT KE SIDEBAR
                with st.sidebar:
                    st.divider()
                    st.markdown("### 💾 Eksport Data")
                    
                    # ATTRIBUTE UNTUK BATU SEMPADAN (POINT)
                    gdf_points = gpd.GeoDataFrame(
                        df[['STN', 'E', 'N']], 
                        geometry=gpd.points_from_xy(df.E, df.N),
                        crs=f"EPSG:{epsg_code}"
                    )

                    # ATTRIBUTE UNTUK POLIGON (LOT)
                    poly_attr = {
                        'LUAS_M2': round(luas, 2),
                        'PARAM_M': round(perimeter, 2)
                    }
                    gdf_poly_export = gpd.GeoDataFrame([poly_attr], geometry=[poly_geom], crs=f"EPSG:{epsg_code}")

                    combined_features = json.loads(gdf_points.to_json())['features'] + json.loads(gdf_poly_export.to_json())['features']
                    final_geojson = {"type": "FeatureCollection", "features": combined_features}

                    st.download_button(
                        label="🚀 Export to QGIS (.geojson)",
                        data=json.dumps(final_geojson),
                        file_name="data_survey_lengkap_puo.geojson",
                        mime="application/json",
                        use_container_width=True
                    )
                    
                    st.divider()
                    if st.button("🚪 Log Keluar", use_container_width=True):
                        st.session_state['authenticated'] = False
                        st.rerun()

                with st.expander("📋 Lihat Jadual Koordinat"):
                    st.dataframe(df, use_container_width=True)

        else:
            st.error("Kolum E dan N tidak ditemui dalam fail CSV.")
    except Exception as e:
        st.error(f"Fail tidak dapat diproses: {e}")