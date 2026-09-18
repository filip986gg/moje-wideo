import streamlit as st
import sqlite3
import os

# Konfiguracja strony
st.set_page_config(page_title="ViShort", page_icon="🎬", layout="centered")

# Foldery i baza
if not os.path.exists('uploads'):
    os.makedirs('uploads')

def init_db():
    conn = sqlite3.connect('baza.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS filmy (id INTEGER PRIMARY KEY AUTOINCREMENT, autor TEXT, tytul TEXT, plik TEXT)')
    conn.commit()
    conn.close()

init_db()

# --- SYSTEM KONTA / LOGOWANIA ---
if 'uzytkownik' not in st.session_state:
    st.session_state.uzytkownik = ""

# Jeśli użytkownik nie jest zalogowany, pokaż ekran powitalny
if not st.session_state.uzytkownik:
    st.title("🎬 Witaj w ViShort!")
    st.write("Zanim przejdziesz dalej, wpisz swoją nazwę użytkownika, aby móc oglądać i wrzucać filmy.")
    
    with st.form("login_form"):
        wpisane_imie = st.text_input("Twoje imię lub nick:")
        start = st.form_submit_button("Wejdź do aplikacji")
        if start and wpisane_imie:
            st.session_state.uzytkownik = wpisane_imie
            st.rerun()
    st.stop() # Zatrzymuje dalsze ładowanie strony, dopóki się nie zaloguje

# --- GŁÓWNA APLIKACJA (PO ZALOGOWANIU) ---
st.title("🎬 ViShort")
st.write(f"Zalogowany jako: **{st.session_state.uzytkownik}** | [Zmień użytkownika](?wyloguj=true)")

# Obsługa wylogowania przez przycisk w tekście
if st.query_params.get("wyloguj"):
    st.session_state.uzytkownik = ""
    st.rerun()

st.markdown("---")

# --- PRZYCISK "+" DO DODAWANIA FILMU ---
with st.expander("➕ Dodaj nowy film", expanded=False):
    with st.form("upload_form", clear_on_submit=True):
        tytul = st.text_input("Tytuł filmu:")
        wideo = st.file_uploader("Wybierz plik wideo (mp4):", type=["mp4", "mov"])
        
        submitted = st.form_submit_button("Opublikuj")
        
        if submitted:
            if tytul and wideo:
                sciezka = os.path.join('uploads', wideo.name)
                with open(sciezka, "wb") as f:
                    f.write(wideo.getbuffer())
                
                conn = sqlite3.connect('baza.db')
                cursor = conn.cursor()
                # Zapisujemy automatycznie jako zalogowany użytkownik
                cursor.execute('INSERT INTO filmy (autor, tytul, plik) VALUES (?, ?, ?)', (st.session_state.uzytkownik, tytul, wideo.name))
                conn.commit()
                conn.close()
                
                st.success("Film został dodany!")
                st.rerun()
            else:
                st.error("Podaj tytuł i wybierz plik wideo!")

st.markdown("---")
st.subheader("📱 Ostatnie filmy społeczności")

# --- WYŚWIETLANIE FILMÓW ---
conn = sqlite3.connect('baza.db')
cursor = conn.cursor()
cursor.execute('SELECT autor, tytul, plik FROM filmy ORDER BY id DESC')
filmy = cursor.fetchall()
conn.close()

if filmy:
    for autor, tytul, plik in filmy:
        st.write(f"### {tytul}")
        st.caption(f"👤 Autor: **{autor}**")
        
        sciezka_pliku = os.path.join('uploads', plik)
        if os.path.exists(sciezka_pliku):
            st.video(sciezka_pliku)
        else:
            st.warning("Plik wideo nie istnieje na serwerze.")
        st.markdown("---")
else:
    st.info("Brak filmów w bazie. Rozwiń '➕ Dodaj nowy film' powyżej i wrzuć coś jako pierwszy!")