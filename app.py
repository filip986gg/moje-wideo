import streamlit as st
import sqlite3
import os
import hashlib

# Konfiguracja strony
st.set_page_config(page_title="ViShort", page_icon="🎬", layout="wide")

if not os.path.exists('uploads'):
    os.makedirs('uploads')

# Funkcja do szyfrowania haseł (żeby były bezpieczne w bazie danych)
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect('baza.db')
    cursor = conn.cursor()
    
    # Tabela użytkowników z hasłami
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uzytkownicy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nazwa TEXT UNIQUE,
            haslo TEXT
        )
    ''')
    
    # Tabela filmów (zabezpieczona)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS filmy (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            autor TEXT, 
            tytul TEXT, 
            plik TEXT,
            lajki INTEGER DEFAULT 0
        )
    ''')
    
    # Tabela na komentarze
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS komentarze (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            film_id INTEGER,
            autor TEXT,
            tekst TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- SYSTEM LOGOWANIA I REJESTRACJI (BEZPIECZEŃSTWO) ---
if 'uzytkownik' not in st.session_state:
    st.session_state.uzytkownik = ""

if not st.session_state.uzytkownik:
    st.title("🎬 Witaj w ViShort - Zaloguj się lub Zarejestruj")
    
    tab1, tab2 = st.tabs(["🔑 Logowanie", "📝 Rejestracja"])
    
    with tab1:
        with st.form("login_form"):
            login_user = st.text_input("Nazwa użytkownika:")
            login_pass = st.text_input("Hasło:", type="password")
            submit_login = st.form_submit_button("Zaloguj się")
            
            if submit_login:
                if login_user and login_pass:
                    conn = sqlite3.connect('baza.db')
                    cursor = conn.cursor()
                    cursor.execute('SELECT haslo FROM uzytkownicy WHERE nazwa = ?', (login_user,))
                    wynik = cursor.fetchone()
                    conn.close()
                    
                    if wynik and wynik[0] == hash_password(login_pass):
                        st.session_state.uzytkownik = login_user
                        st.success("Zalogowano pomyślnie!")
                        st.rerun()
                    else:
                        st.error("Błędna nazwa użytkownika lub hasło!")
                else:
                    st.warning("Wypełnij wszystkie pola.")
                    
    with tab2:
        with st.form("register_form"):
            reg_user = st.text_input("Wybierz nazwę użytkownika:")
            reg_pass = st.text_input("Wybierz silne hasło:", type="password")
            submit_reg = st.form_submit_button("Utwórz konto")
            
            if submit_reg:
                if reg_user and reg_pass:
                    try:
                        conn = sqlite3.connect('baza.db')
                        cursor = conn.cursor()
                        cursor.execute('INSERT INTO uzytkownicy (nazwa, haslo) VALUES (?, ?)', (reg_user, hash_password(reg_pass)))
                        conn.commit()
                        conn.close()
                        st.success("Konto utworzone! Teraz możesz się zalogować w zakładce 'Logowanie'.")
                    except sqlite3.IntegrityError:
                        st.error("Taka nazwa użytkownika jest już zajęta. Wybierz inną.")
                else:
                    st.warning("Wypełnij wszystkie pola.")
    st.stop()

# --- BOCZNE MENU ---
st.sidebar.title(f"👤 {st.session_state.uzytkownik}")
if st.sidebar.button("Wyloguj się"):
    st.session_state.uzytkownik = ""
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("Nawigacja")
menu = st.sidebar.radio("Wybierz zakładkę", ["Strona główna", "Dodaj film"])

# --- GÓRNY PASEK WYSZUKIWANIA ---
col_title, col_search = st.columns([2, 3])
with col_title:
    st.title("🎬 ViShort")
with col_search:
    szukaj = st.text_input("🔍 Szukaj filmów lub autorów...", "")

st.markdown("---")

# --- ZAKŁADKA: DODAJ FILM ---
if menu == "Dodaj film":
    st.header("➕ Opublikuj nowy film")
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
                cursor.execute('INSERT INTO filmy (autor, tytul, plik, lajki) VALUES (?, ?, ?, 0)', (st.session_state.uzytkownik, tytul, wideo.name))
                conn.commit()
                conn.close()
                
                st.success("Film został dodany!")
                st.rerun()
            else:
                st.error("Podaj tytuł i wybierz plik wideo!")

# --- ZAKŁADKA: STRONA GŁÓWNA ---
else:
    conn = sqlite3.connect('baza.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, autor, tytul, plik, lajki FROM filmy ORDER BY id DESC')
    filmy = cursor.fetchall()
    conn.close()

    if szukaj:
        filmy = [f for f in filmy if szukaj.lower() in f[1].lower() or szukaj.lower() in f[2].lower()]

    if filmy:
        for film_id, autor, tytul, plik, lajki in filmy:
            col_video, col_actions = st.columns([3, 1])
            
            with col_video:
                st.subheader(tytul)
                st.caption(f"👤 Autor: **{autor}**")
                sciezka_pliku = os.path.join('uploads', plik)
                if os.path.exists(sciezka_pliku):
                    st.video(sciezka_pliku)
                else:
                    st.warning("Plik wideo nie istnieje na serwerze.")
            
            with col_actions:
                st.write("") 
                st.write("")
                if st.button(f"❤️ {lajki}", key=f"like_{film_id}"):
                    conn = sqlite3.connect('baza.db')
                    cursor = conn.cursor()
                    cursor.execute('UPDATE filmy SET lajki = lajki + 1 WHERE id = ?', (film_id,))
                    conn.commit()
                    conn.close()
                    st.rerun()
                
                st.markdown("💬 **Komentarze**")

            with st.expander(f"Pokaż/Dodaj komentarze do: {tytul}"):
                conn = sqlite3.connect('baza.db')
                cursor = conn.cursor()
                cursor.execute('SELECT autor, tekst FROM komentarze WHERE film_id = ?', (film_id,))
                komentarze = cursor.fetchall()
                conn.close()
                
                if komentarze:
                    for k_autor, k_tekst in komentarze:
                        st.markdown(f"**{k_autor}**: {k_tekst}")
                else:
                    st.info("Brak komentarzy. Bądź pierwszy!")
                
                with st.form(key=f"comm_form_{film_id}", clear_on_submit=True):
                    nowy_kom = st.text_input("Napisz komentarz...", key=f"input_comm_{film_id}")
                    wyslij_kom = st.form_submit_button("Wyślij")
                    if wyslij_kom and nowy_kom:
                        conn = sqlite3.connect('baza.db')
                        cursor = conn.cursor()
                        cursor.execute('INSERT INTO komentarze (film_id, autor, tekst) VALUES (?, ?, ?)', (film_id, st.session_state.uzytkownik, nowy_kom))
                        conn.commit()
                        conn.close()
                        st.rerun()

            st.markdown("---")
    else:
        st.info("Brak filmów spełniających kryteria.")