import streamlit as st

from core import (ALPHA, CONDUCTIVITY, REACTANCE, conductor_resistance, dimension_line,
                  mean_power_factor, operating_current, voltage_drop)

st.set_page_config(page_title="LF6 Leitungsplaner", page_icon="⚡", layout="wide")

st.markdown("""
<style>
  .stApp {background: linear-gradient(135deg,#f7fafc 0%,#eef4f8 100%)}
  [data-testid="stSidebar"] {background:#102a43;color:white}
  [data-testid="stSidebar"] * {color:#f0f4f8}
  .hero {padding:1.6rem 1.8rem;border-radius:18px;background:linear-gradient(110deg,#0b7285,#1864ab);color:white;margin-bottom:1.2rem;box-shadow:0 12px 30px #102a4322}
  .hero h1 {margin:0;font-size:2.15rem}.hero p{margin:.45rem 0 0;opacity:.92}
  .formula {background:white;border-left:5px solid #0b7285;padding:1rem 1.2rem;border-radius:10px;box-shadow:0 4px 14px #102a4312}
  div[data-testid="stMetric"] {background:white;border-radius:12px;padding:.65rem 1rem;border:1px solid #d9e2ec}
  .ok {padding:.8rem 1rem;background:#d3f9d8;color:#1b4332;border-radius:10px}.warn {padding:.8rem 1rem;background:#fff3bf;color:#5f3c00;border-radius:10px}
</style>
<div class="hero"><h1>⚡ LF6 Leitungsplaner</h1><p>Dimensionieren, prüfen und verstehen – Formelsammlung Teil 6 bis 9</p></div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Arbeitsbereich")
    page = st.radio("Navigation", ["Start", "6 · Leitungsdimensionierung", "7 · Schutzorgane",
                                    "8 · Widerstände & Impedanzen", "9 · Spannungsfall"], label_visibility="collapsed")
    st.divider()
    st.caption("Fachliche Basis: Formelsammlung LF6, Version 1.0.1. Ergebnisse sind rechnerische Planungshilfen und ersetzen keine Normenprüfung.")

if page == "Start":
    st.subheader("Von den Lastdaten zur geprüften Leitung")
    st.write("Die vier Arbeitsbereiche bilden den Planungsweg aus den Teilen 6–9 ab.")
    cols = st.columns(4)
    for col, number, title, text in zip(cols, "6789", ["Dimensionieren", "Schützen", "Widerstand", "Spannungsfall"],
                                       ["Betriebsstrom, Korrekturfaktoren und Querschnitt", "Schutzregeln und Standard-Nennwerte", "Material- und Temperatureinfluss", "Kleine/große Querschnitte und Leistungsfaktor"]):
        with col:
            with st.container(border=True): st.markdown(f"### {number} · {title}\n{text}")
    st.info("Starte links mit Teil 6 für eine vollständige Leitungsdimensionierung.")

elif page == "6 · Leitungsdimensionierung":
    st.subheader("Geführte Leitungsdimensionierung")
    with st.form("dimensioning"):
        a,b,c = st.columns(3)
        with a:
            power = st.number_input("Wirkleistung P [kW]", .1, 10000.0, 15.0)
            phases_label = st.selectbox("Netz", ["Drehstrom", "Wechselstrom"])
            voltage = st.number_input("Nennspannung U [V]", 1.0, 100000.0, 400.0 if phases_label == "Drehstrom" else 230.0)
            cosphi = st.slider("Leistungsfaktor cos φ", .1, 1.0, .9, .01)
        with b:
            efficiency = st.slider("Wirkungsgrad η", .1, 1.0, .95, .01)
            simultaneity = st.slider("Gleichzeitigkeitsfaktor g", .05, 1.0, 1.0, .05)
            installation = st.selectbox("Referenz-Verlegeart", ["A1","A2","B1","B2","C"])
            loaded = st.selectbox("Belastete Adern", [3,2])
        with c:
            length = st.number_input("Einfache Leitungslänge [m]", .1, 100000.0, 35.0)
            material = st.selectbox("Leitermaterial", ["Kupfer","Aluminium"])
            temp = st.number_input("Leitertemperatur [°C]", -20.0, 200.0, 70.0)
            correction = st.number_input("Gesamtkorrekturfaktor f", .01, 2.0, .80, .01, help="Produkt aus Temperatur-, Häufungs-, Vieladrigkeits- und Oberwellenfaktor.")
        d,e = st.columns(2)
        max_drop = d.selectbox("Zulässiger Spannungsfall", [3.0,5.0,.5], format_func=lambda x:f"{x:g} %")
        reactance = e.selectbox("Leitungstyp / Reaktanz", list(REACTANCE), format_func=lambda x:f"{x} ({REACTANCE[x]:.2f} Ω/km)")
        run = st.form_submit_button("Leitung berechnen", type="primary", use_container_width=True)
    if run:
        result = dimension_line(power_kw=power, voltage=voltage, power_factor=cosphi, phases=3 if phases_label=="Drehstrom" else 1,
          efficiency=efficiency, simultaneity=simultaneity, installation=installation, loaded_conductors=loaded,
          correction_factor=correction, length_m=length, material=material, temperature_c=temp,
          max_drop_percent=max_drop, reactance_ohm_km=REACTANCE[reactance], trip_factor=1.45)
        if result.successful:
            st.markdown('<div class="ok"><b>Dimensionierung erfolgreich:</b> Belastbarkeit, Schutz und Spannungsfall sind rechnerisch erfüllt.</div>', unsafe_allow_html=True)
            m=st.columns(5)
            for col,label,value in zip(m,["Betriebsstrom Iᴮ","Mindest-Referenz Iʳ","Querschnitt","Korrigiertes Iᶻ","Spannungsfall"],
                [f"{result.current_a:.2f} A",f"{result.required_reference_a:.2f} A",f"{result.section_mm2:g} mm²",f"{result.corrected_ampacity_a:.2f} A",f"{result.drop_percent:.2f} %"]): col.metric(label,value)
            st.write(f"Vorgeschlagenes Schutzorgan: **{result.fuse_a} A** · Absoluter Spannungsfall: **{result.drop_v:.2f} V**")
        else:
            st.error("Mit den verfügbaren Tabellenwerten bis 300 mm² wurde keine vollständig gültige Kombination gefunden. Korrekturfaktoren, Leitungslänge oder Verlegeart prüfen.")
    with st.expander("Formelweg"):
        st.latex(r"I_B=\frac{P}{\sqrt{3}\,U\,\cos\varphi\,\eta}\quad\quad I_{r,min}=\frac{I_B}{\prod f_i}\quad\quad I_z=I_r\prod f_i")
        st.write("Prüfkette: Iᴮ ≤ Iⁿ ≤ Iᶻ · Auslöseregel · zulässiger Spannungsfall.")

elif page == "7 · Schutzorgane":
    st.subheader("Schutzorgan prüfen")
    c1,c2,c3 = st.columns(3)
    ib = c1.number_input("Betriebsstrom Iᴮ [A]", 0.01, 10000.0, 24.0)
    iz = c2.number_input("Zulässige Belastbarkeit Iᶻ [A]", 0.01, 10000.0, 32.0)
    nominal = c3.selectbox("Bemessungsstrom Iⁿ [A]", [6,10,13,16,20,25,32,35,40,50,63,80,100,125,160])
    kind = st.radio("Schutzorgan", ["Leitungsschutzschalter (I₂ = 1,45 · Iⁿ)", "gG-Sicherung (I₂ = 1,6 · Iⁿ)"], horizontal=True)
    i2 = nominal * (1.45 if kind.startswith("Leitung") else 1.6)
    rule1 = ib <= nominal <= iz; rule2 = i2 <= 1.45*iz
    a,b,c = st.columns(3); a.metric("Bemessungsstromregel", "erfüllt" if rule1 else "nicht erfüllt"); b.metric("Auslösestrom I₂",f"{i2:.2f} A"); c.metric("Auslöseregel", "erfüllt" if rule2 else "nicht erfüllt")
    st.success("Schutz rechnerisch passend.") if rule1 and rule2 else st.warning("Schutzorgan oder Leitungsquerschnitt anpassen.")
    st.latex(r"I_B\leq I_n\leq I_z\qquad I_2\leq1{,}45\cdot I_z")
    with st.expander("Kurzüberblick Schutzorgane"):
        st.markdown("**LS-Schalter:** typisch 6/10 kA · **NEOZED/DIAZED:** typisch 50 kA AC · **NH-System:** typisch bis 120 kA AC. Selektivität ist herstellerbezogen zu prüfen; für zwei gG-Sicherungen gilt als Richtwert ein Nennstromverhältnis von 1 : 1,6.")

elif page == "8 · Widerstände & Impedanzen":
    st.subheader("Leiterwiderstand und Impedanz")
    c1,c2,c3,c4 = st.columns(4)
    material = c1.selectbox("Material", list(CONDUCTIVITY))
    length = c2.number_input("Leiterlänge ℓ [m]", .01, 1e7, 100.0)
    section = c3.number_input("Querschnitt A [mm²]", .01, 10000.0, 16.0)
    temp = c4.number_input("Temperatur ϑ [°C]", -100.0, 500.0, 70.0)
    r20 = conductor_resistance(length, section, material, 20)
    rt = conductor_resistance(length, section, material, temp)
    m=st.columns(4); m[0].metric("R₂₀",f"{r20:.5f} Ω"); m[1].metric(f"R bei {temp:g} °C",f"{rt:.5f} Ω"); m[2].metric("R′",f"{rt/length*1000:.4f} Ω/km"); m[3].metric("Temperaturfaktor",f"{rt/r20:.4f}")
    st.latex(r"R_{20}=\frac{\ell}{\gamma_{20}A}\qquad R_\vartheta=R_{20}\,[1+\alpha_{20}(\vartheta-20^\circ C)]")
    st.caption(f"Verwendet: γ₂₀ = {CONDUCTIVITY[material]:g} MS/m, α₂₀ = {ALPHA.get(material,0.004):.5f} 1/K")

else:
    st.subheader("Spannungsfall und Leitungsverlust")
    c1,c2,c3 = st.columns(3)
    current = c1.number_input("Leiterstrom I [A]", .01, 100000.0, 32.0)
    length = c1.number_input("Einfache Länge ℓ [m]", .01, 1e7, 50.0)
    section = c2.number_input("Querschnitt A [mm²]", .01, 10000.0, 10.0)
    material = c2.selectbox("Material", ["Kupfer","Aluminium"])
    network = c3.selectbox("Netz", ["Drehstrom 400 V","Wechselstrom 230 V"])
    cosphi = c3.slider("cos φ", .1, 1.0, .9, .01)
    temp = c3.number_input("Leitertemperatur [°C]", -20.0, 200.0, 70.0)
    line_type = st.selectbox("Leitungstyp", list(REACTANCE), format_func=lambda x:f"{x} · X′ = {REACTANCE[x]:.2f} Ω/km")
    phases = 3 if network.startswith("Dreh") else 1; voltage = 400 if phases==3 else 230
    drop,pct = voltage_drop(current,length,section,voltage,cosphi,phases,material,temp,REACTANCE[line_type])
    rpkm = conductor_resistance(1000,section,material,temp); loss=(3 if phases==3 else 2)*current**2*rpkm*length/1000
    a,b,c=st.columns(3); a.metric("Spannungsfall ΔU",f"{drop:.2f} V"); b.metric("Relativer Spannungsfall",f"{pct:.2f} %"); c.metric("Leitungsverlust Pᵥ",f"{loss:.1f} W")
    if pct <= 3: st.success("Der Spannungsfall liegt innerhalb der 3-%-Planungsgrenze.")
    elif pct <= 5: st.warning("Für Beleuchtung bzw. die 3-%-Grenze zu hoch; für andere Geräte ggf. noch innerhalb 5 %.")
    else: st.error("Der Spannungsfall überschreitet 5 %. Querschnitt oder Leitungslänge anpassen.")
    st.latex(r"\Delta U=\sqrt{3}\,\ell I(R'\cos\varphi+X'\sin\varphi)\quad\text{(Drehstrom)}")
    with st.expander("Mittleren Leistungsfaktor mehrerer Lasten berechnen"):
        count=st.number_input("Anzahl Lasten",1,6,2)
        loads=[]
        for i in range(count):
            x,y=st.columns(2); loads.append((x.number_input(f"P{i+1} [kW]",.01,1e6,10.0,key=f"p{i}"),y.slider(f"cos φ{i+1}",.1,1.0,.9,.01,key=f"pf{i}")))
        pf,sf,tf=mean_power_factor(loads); st.write(f"**cos φₘ = {pf:.3f}** · sin φₘ = {sf:.3f} · tan φₘ = {tf:.3f}")

