import streamlit as st

from core import (ALPHA, CONDUCTIVITY, REACTANCE, STANDARD_FUSES, check_overload_protection,
                  conductor_resistance, dimension_line, mean_power_factor, voltage_drop)

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

PAGES = [
    "Start",
    "6 · Leitungsdimensionierung",
    "7 · Schutzorgane",
    "8 · Widerstände & Impedanzen",
    "9 · Spannungsfall",
]


def transfer_from_part_6(target: int) -> None:
    """Befuellt den Zielteil und wechselt direkt dorthin."""
    data = st.session_state.get("dimensioning_transfer")
    if not data:
        return

    if target == 7:
        st.session_state["protection_ib"] = float(data["operating_current_a"])
        st.session_state["protection_iz"] = float(data["ampacity_a"])
        st.session_state["protection_nominal"] = int(data["rated_current_a"])
        st.session_state["protection_from_section"] = float(data["section_mm2"])
    elif target == 8:
        st.session_state["resistance_material"] = data["material"]
        st.session_state["resistance_length"] = float(data["length_m"])
        st.session_state["resistance_section"] = float(data["section_mm2"])
        st.session_state["resistance_temperature"] = float(data["temperature_c"])
        st.session_state["resistance_from_part6"] = True
    elif target == 9:
        st.session_state["drop_current"] = float(data["operating_current_a"])
        st.session_state["drop_length"] = float(data["length_m"])
        st.session_state["drop_section"] = float(data["section_mm2"])
        st.session_state["drop_material"] = data["material"]
        st.session_state["drop_network"] = (
            "Drehstrom 400 V" if data["phases"] == 3 else "Wechselstrom 230 V"
        )
        st.session_state["drop_power_factor"] = float(data["power_factor"])
        st.session_state["drop_temperature"] = float(data["temperature_c"])
        st.session_state["drop_line_type"] = data["line_type"]
        st.session_state["drop_from_part6"] = True

    st.session_state["active_page"] = PAGES[target - 5]

with st.sidebar:
    st.header("Arbeitsbereich")
    page = st.radio(
        "Navigation", PAGES, label_visibility="collapsed", key="active_page"
    )
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
            st.session_state["dimensioning_transfer"] = {
                "operating_current_a": result.current_a,
                "ampacity_a": result.corrected_ampacity_a,
                "rated_current_a": result.fuse_a,
                "section_mm2": result.section_mm2,
                "length_m": length,
                "material": material,
                "temperature_c": temp,
                "power_factor": cosphi,
                "phases": 3 if phases_label == "Drehstrom" else 1,
                "line_type": reactance,
            }
            st.markdown('<div class="ok"><b>Dimensionierung erfolgreich:</b> Belastbarkeit, Schutz und Spannungsfall sind rechnerisch erfüllt.</div>', unsafe_allow_html=True)
            m=st.columns(5)
            for col,label,value in zip(m,["Betriebsstrom Iᴮ","Mindest-Referenz Iʳ","Querschnitt","Korrigiertes Iᶻ","Spannungsfall"],
                [f"{result.current_a:.2f} A",f"{result.required_reference_a:.2f} A",f"{result.section_mm2:g} mm²",f"{result.corrected_ampacity_a:.2f} A",f"{result.drop_percent:.2f} %"]): col.metric(label,value)
            st.write(f"Vorgeschlagenes Schutzorgan: **{result.fuse_a} A** · Absoluter Spannungsfall: **{result.drop_v:.2f} V**")
        else:
            st.error("Mit den verfügbaren Tabellenwerten bis 300 mm² wurde keine vollständig gültige Kombination gefunden. Korrekturfaktoren, Leitungslänge oder Verlegeart prüfen.")

    transfer = st.session_state.get("dimensioning_transfer")
    if transfer:
        st.markdown("#### Ergebnis direkt weiterverwenden")
        st.caption(
            f"Letzte gültige Berechnung: {transfer['section_mm2']:g} mm² · "
            f"Iᴮ {transfer['operating_current_a']:.2f} A · "
            f"{transfer['length_m']:g} m · {transfer['material']}"
        )
        target_7, target_8, target_9 = st.columns(3)
        target_7.button(
            "→ In Teil 7 übernehmen",
            type="primary",
            use_container_width=True,
            on_click=transfer_from_part_6,
            args=(7,),
        )
        target_8.button(
            "→ In Teil 8 übernehmen",
            use_container_width=True,
            on_click=transfer_from_part_6,
            args=(8,),
        )
        target_9.button(
            "→ In Teil 9 übernehmen",
            use_container_width=True,
            on_click=transfer_from_part_6,
            args=(9,),
        )
    with st.expander("Formelweg"):
        st.latex(r"I_B=\frac{P}{\sqrt{3}\,U\,\cos\varphi\,\eta}\quad\quad I_{r,min}=\frac{I_B}{\prod f_i}\quad\quad I_z=I_r\prod f_i")
        st.write("Prüfkette: Iᴮ ≤ Iⁿ ≤ Iᶻ · Auslöseregel · zulässiger Spannungsfall.")

elif page == "7 · Schutzorgane":
    st.subheader("Schutzorgan prüfen")
    st.write("Prüfe, ob der Bemessungsstrom des Schutzorgans zur Leitung passt und die Überlastabschaltung sichergestellt ist.")

    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        ib = c1.number_input(
            "Betriebsstrom Iᴮ [A]", 0.01, 10000.0, 24.0, key="protection_ib"
        )
        iz = c2.number_input(
            "Zulässige Belastbarkeit Iᶻ [A]", 0.01, 10000.0, 32.0, key="protection_iz"
        )
        nominal = c3.selectbox(
            "Bemessungsstrom Iⁿ [A]",
            STANDARD_FUSES,
            key="protection_nominal",
        )
        kind = st.radio(
            "Schutzorgan",
            ["Leitungsschutzschalter", "gG-Sicherung"],
            horizontal=True,
        )

    result = check_overload_protection(
        operating_current_a=ib,
        rated_current_a=nominal,
        ampacity_a=iz,
        device="LS" if kind == "Leitungsschutzschalter" else "gG",
    )

    a, b, c = st.columns(3)
    a.metric("Bemessungsstromregel", "Erfüllt" if result.rated_current_ok else "Nicht erfüllt")
    b.metric("Auslösestrom I₂", f"{result.trip_current_a:.2f} A")
    c.metric("Auslöseregel", "Erfüllt" if result.trip_rule_ok else "Nicht erfüllt")

    if result.successful:
        st.success("Das Schutzorgan ist rechnerisch passend.")
    else:
        st.warning("Schutzorgan oder Leitungsquerschnitt anpassen.")

    st.markdown(
        """
        <div class="formula">
          <strong>Prüfbedingungen</strong><br>
          I<sub>B</sub> ≤ I<sub>n</sub> ≤ I<sub>z</sub>
          &nbsp;&nbsp;und&nbsp;&nbsp;
          I<sub>2</sub> ≤ 1,45 · I<sub>z</sub>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(
        f"Aktuell: {ib:.2f} A ≤ {nominal:.2f} A ≤ {iz:.2f} A · "
        f"{result.trip_current_a:.2f} A ≤ {result.max_permitted_trip_current_a:.2f} A"
    )
    if "protection_from_section" in st.session_state:
        st.caption(
            f"Übernommen aus der Dimensionierung mit {st.session_state['protection_from_section']:g} mm²."
        )
    with st.expander("Kurzüberblick Schutzorgane"):
        st.markdown("**LS-Schalter:** typisch 6/10 kA · **NEOZED/DIAZED:** typisch 50 kA AC · **NH-System:** typisch bis 120 kA AC. Selektivität ist herstellerbezogen zu prüfen; für zwei gG-Sicherungen gilt als Richtwert ein Nennstromverhältnis von 1 : 1,6.")

elif page == "8 · Widerstände & Impedanzen":
    st.subheader("Leiterwiderstand und Impedanz")
    if st.session_state.get("resistance_from_part6"):
        st.success("Die Leitungsdaten wurden aus Teil 6 übernommen.")
    c1,c2,c3,c4 = st.columns(4)
    material = c1.selectbox("Material", list(CONDUCTIVITY), key="resistance_material")
    length = c2.number_input("Leiterlänge ℓ [m]", .01, 1e7, 100.0, key="resistance_length")
    section = c3.number_input("Querschnitt A [mm²]", .01, 10000.0, 16.0, key="resistance_section")
    temp = c4.number_input("Temperatur ϑ [°C]", -100.0, 500.0, 70.0, key="resistance_temperature")
    r20 = conductor_resistance(length, section, material, 20)
    rt = conductor_resistance(length, section, material, temp)
    m=st.columns(4); m[0].metric("R₂₀",f"{r20:.5f} Ω"); m[1].metric(f"R bei {temp:g} °C",f"{rt:.5f} Ω"); m[2].metric("R′",f"{rt/length*1000:.4f} Ω/km"); m[3].metric("Temperaturfaktor",f"{rt/r20:.4f}")
    st.latex(r"R_{20}=\frac{\ell}{\gamma_{20}A}\qquad R_\vartheta=R_{20}\,[1+\alpha_{20}(\vartheta-20^\circ C)]")
    st.caption(f"Verwendet: γ₂₀ = {CONDUCTIVITY[material]:g} MS/m, α₂₀ = {ALPHA.get(material,0.004):.5f} 1/K")

else:
    st.subheader("Spannungsfall und Leitungsverlust")
    if st.session_state.get("drop_from_part6"):
        st.success("Die Leitungs- und Lastdaten wurden aus Teil 6 übernommen.")
    c1,c2,c3 = st.columns(3)
    current = c1.number_input("Leiterstrom I [A]", .01, 100000.0, 32.0, key="drop_current")
    length = c1.number_input("Einfache Länge ℓ [m]", .01, 1e7, 50.0, key="drop_length")
    section = c2.number_input("Querschnitt A [mm²]", .01, 10000.0, 10.0, key="drop_section")
    material = c2.selectbox("Material", ["Kupfer","Aluminium"], key="drop_material")
    network = c3.selectbox("Netz", ["Drehstrom 400 V","Wechselstrom 230 V"], key="drop_network")
    cosphi = c3.slider("cos φ", .1, 1.0, .9, .01, key="drop_power_factor")
    temp = c3.number_input("Leitertemperatur [°C]", -20.0, 200.0, 70.0, key="drop_temperature")
    line_type = st.selectbox("Leitungstyp", list(REACTANCE), format_func=lambda x:f"{x} · X′ = {REACTANCE[x]:.2f} Ω/km", key="drop_line_type")
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

