import streamlit as st
import sqlite3
import os
import hashlib

# Konfiguracja strony
st.set_page_config(page_title="ViShort", page_icon="🎬", layout="wide")

if not os.path.exists('uploads'):
    os.makedirs('uploads')

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect('baza.db')
    cursor = conn.cursor()
    
    # Tabela użytkowników
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uzytkownicy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nazwa TEXT UNIQUE,
            haslo TEXT
        )
    ''')
    
    # Tabela filmów
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS filmy (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            autor TEXT, 
            tytul TEXT, 
            plik TEXT,
            lajki INTEGER DEFAULT 0
        )
    ''')
    
    # Tabela na komentarze pod filmami
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS komentarze (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            film_id INTEGER,
            autor TEXT,
            tekst TEXT
        )
    ''')
    
    # Tabela znajomych
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS znajomi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uzytkownik TEXT,
            znajomy TEXT,
            UNIQUE(uzytkownik, znajomy)
        )
    ''')
    
    # Tabela wiadomości czatu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wiadomosci (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nadawca TEXT,
            odbiorca TEXT,
            tekst TEXT
        )
    ''')
    
    # Bezpieczna migracja kolumny 'lajki'
    cursor.execute("PRAGMA table_info(filmy)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'lajki' not in columns:
        cursor.execute("ALTER TABLE filmy ADD COLUMN lajki INTEGER DEFAULT 0")
        
    conn.commit()
    conn.close()

init_db()

# --- SYSTEM LOGOWANIA I REJESTRACJI ---
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
                        st.success("Konto utworzone! Teraz możesz się zalogować.")
                    except sqlite3.IntegrityError:
                        st.error("Taka nazwa użytkownika jest już zajęta.")
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
menu = st.sidebar.radio("Wybierz zakładkę", ["Strona główna", "Dodaj film", "Znajomi i Chat"])

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

# --- ZAKŁADKA: ZNAJOMI I CHAT ---
elif menu == "Znajomi i Chat":
    st.header("👥 Znajomi i Wiadomości")
    
    # Pobieranie listy znajomych
    conn = sqlite3.connect('baza.db')
    cursor = conn.cursor()
    cursor.execute('SELECT znajomy FROM znajomi WHERE uzytkownik = ?', (st.session_state.uzytkownik,))
    znajomi = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    col_znajomi, col_czat = st.columns([1, 2])
    
    with col_znajomi:
        st.subheader("Twoi znajomi")
        if znajomi:
            wybrany_znajomy = st.selectbox("Wybierz do czatu:", znajomi)
        else:
            wybrany_znajomy = None
            st.info("Brak znajomych na liście.")
            
        st.markdown("---")
        st.subheader("Dodaj znajomego")
        with st.form("add_friend_form", clear_on_submit=True):
            szukany_login = st.text_input("Nazwa użytkownika:")
            dodaj_btn = st.form_submit_button("Dodaj")
            if dodaj_btn and szukany_login:
                if szukany_login == st.session_state.uzytkownik:
                    st.error("Nie możesz dodać samego siebie!")
                else:
                    conn = sqlite3.connect('baza.db')
                    cursor = conn.cursor()
                    cursor.execute('SELECT nazwa FROM uzytkownicy WHERE nazwa = ?', (szukany_login,))
                    istnieje = cursor.fetchone()
                    if istnieje:
                        try:
                            cursor.execute('INSERT INTO znajomi (uzytkownik, znajomy) VALUES (?, ?)', (st.session_state.uzytkownik, szukany_login))
                            conn.commit()
                            st.success(f"Dodano użytkownika {szukany_login}!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.warning("Ten użytkownik jest już na Twojej liście.")
                    else:
                        st.error("Nie ma takiego użytkownika.")
                    conn.close()
                    
    with col_czat:
        if wybrany_znajomy:
            st.subheader(f"💬 Czat z: {wybrany_znajomy}")
            
            # Pobieranie wiadomości
            conn = sqlite3.connect('baza.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT nadawca, tekst FROM wiadomosci 
                WHERE (nadawca = ? AND odbiorca = ?) OR (nadawca = ? AND odbiorca = ?)
                ORDER BY id ASC
            ''', (st.session_state.uzytkownik, wybrany_znajomy, wybrany_znajomy, st.session_state.uzytkownik))
            wiadomosci = cursor.fetchall()
            conn.close()
            
            # Wyświetlanie historii wiadomości
            chat_container = st.container(height=400)
            with chat_container:
                if wiadomosci:
                    for nadawca, tekst in wiadomosci:
                        if nadawca == st.session_state.uzytkownik:
                            st.chat_message("user").write(tekst)
                        else:
                            st.chat_message("assistant").write(f"**{nadawca}**: {tekst}")
                else:
                    st.info("Brak wiadomości. Rozpocznij konwersację!")
            
            # Wysyłanie wiadomości
            tekst_wiadomosci = st.chat_input("Napisz wiadomość...")
            if tekst_wiadomosci:
                conn = sqlite3.connect('baza.db')
                cursor = conn.cursor()
                cursor.execute('INSERT INTO wiadomosci (nadawca, odbiorca, tekst) VALUES (?, ?, ?)', 
                               (st.session_state.uzytkownik, wybrany_znajomy, tekst_wiadomosci))
                conn.commit()
                conn.close()
                st.rerun()
        else:
            st.info("Wybierz znajomego z listy po lewej stronie, aby otworzyć czat.")

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