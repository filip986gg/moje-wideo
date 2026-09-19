import streamlit as st
import sqlite3
import os
import hashlib
from datetime import datetime, timedelta
import random

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="ViShort Mega Pro Ultimate", page_icon="🎬", layout="wide")

if not os.path.exists('uploads'):
    os.makedirs('uploads')

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- INICJALIZACJA BAZY DANYCH ---
def init_db():
    conn = sqlite3.connect('baza.db')
    cursor = conn.cursor()
    
    # Użytkownicy
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uzytkownicy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nazwa TEXT UNIQUE,
            haslo TEXT,
            opis TEXT DEFAULT '',
            zdjecie_profilowe TEXT DEFAULT '',
            tlo_profilu TEXT DEFAULT '',
            linki TEXT DEFAULT '',
            ostatnia_zmiana_nazwy TEXT DEFAULT '',
            punkty INTEGER DEFAULT 0,
            ostatnie_logowanie TEXT DEFAULT '',
            status_konta TEXT DEFAULT 'Aktywne',
            wyrozniony_film_id INTEGER DEFAULT 0
        )
    ''')
    
    # Filmy
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS filmy (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            autor TEXT, 
            tytul TEXT, 
            opis_filmu TEXT DEFAULT '',
            plik TEXT,
            miniatura TEXT DEFAULT '',
            prawa_autorskie TEXT DEFAULT 'Zweryfikowane (Czyste)',
            czy_ai INTEGER DEFAULT 0,
            lajki INTEGER DEFAULT 0,
            dislajki INTEGER DEFAULT 0,
            wyswietlenia INTEGER DEFAULT 0,
            kategoria TEXT DEFAULT 'Inne',
            data_publikacji TEXT DEFAULT '',
            tagi TEXT DEFAULT '',
            reakcje_ogien INTEGER DEFAULT 0,
            reakcje_smiech INTEGER DEFAULT 0,
            reakcje_szok INTEGER DEFAULT 0
        )
    ''')
    
    # Komentarze
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS komentarze (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            film_id INTEGER,
            autor TEXT,
            tekst TEXT,
            lajki INTEGER DEFAULT 0,
            przypniety INTEGER DEFAULT 0
        )
    ''')
    
    # Obserwujący i Znajomi
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS obserwujacy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            obserwujacy TEXT,
            tworca TEXT,
            UNIQUE(obserwujacy, tworca)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS znajomi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uzytkownik TEXT,
            znajomy TEXT,
            UNIQUE(uzytkownik, znajomy)
        )
    ''')
    
    # Historia oglądania
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uzytkownik TEXT,
            film_id INTEGER,
            data_obejrzenia TEXT
        )
    ''')
    
    # Czat i powiadomienia
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wiadomosci (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nadawca TEXT,
            odbiorca TEXT,
            tekst TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS powiadomienia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            odbiorca TEXT,
            tekst TEXT,
            przeczytane INTEGER DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS zgloszenia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            film_id INTEGER,
            powod TEXT,
            zglaszajacy TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logi_admina (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            czas TEXT,
            dzialanie TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ogloszenia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tresc TEXT
        )
    ''')

    # Bezpieczna migracja kolumn
    def dodaj_kolumne(tabela, kolumna, definicja):
        cursor.execute(f"PRAGMA table_info({tabela})")
        cols = [c[1] for c in cursor.fetchall()]
        if kolumna not in cols:
            cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN {kolumna} {definicja}")

    dodaj_kolumne('uzytkownicy', 'punkty', 'INTEGER DEFAULT 0')
    dodaj_kolumne('uzytkownicy', 'ostatnie_logowanie', "TEXT DEFAULT ''")
    dodaj_kolumne('uzytkownicy', 'status_konta', "TEXT DEFAULT 'Aktywne'")
    dodaj_kolumne('uzytkownicy', 'wyrozniony_film_id', 'INTEGER DEFAULT 0')
    
    dodaj_kolumne('filmy', 'dislajki', 'INTEGER DEFAULT 0')
    dodaj_kolumne('filmy', 'data_publikacji', "TEXT DEFAULT ''")
    dodaj_kolumne('filmy', 'tagi', "TEXT DEFAULT ''")
    dodaj_kolumne('filmy', 'reakcje_ogien', 'INTEGER DEFAULT 0')
    dodaj_kolumne('filmy', 'reakcje_smiech', 'INTEGER DEFAULT 0')
    dodaj_kolumne('filmy', 'reakcje_szok', 'INTEGER DEFAULT 0')

    conn.commit()
    conn.close()

init_db()

# --- SESJA UŻYTKOWNIKA ---
if 'uzytkownik' not in st.session_state:
    st.session_state.uzytkownik = ""

# --- LOGOWANIE I REJESTRACJA ---
if not st.session_state.uzytkownik:
    st.title("🎬 ViShort Mega Pro - Zaloguj się")
    
    tab1, tab2 = st.tabs(["🔑 Logowanie", "📝 Rejestracja"])
    
    with tab1:
        with st.form("login_form"):
            login_user = st.text_input("Nazwa użytkownika:")
            login_pass = st.text_input("Hasło:", type="password")
            submit_login = st.form_submit_button("Zaloguj się")
            
            if submit_login:
                if login_user == "admin" and login_pass == "182736":
                    st.session_state.uzytkownik = "admin"
                    st.success("Zalogowano jako Administrator!")
                    st.rerun()
                elif login_user and login_pass:
                    conn = sqlite3.connect('baza.db')
                    cursor = conn.cursor()
                    cursor.execute('SELECT haslo, status_konta FROM uzytkownicy WHERE nazwa = ?', (login_user,))
                    wynik = cursor.fetchone()
                    
                    if wynik:
                        haslo_db, status_k = wynik
                        if status_k == "Zablokowane":
                            st.error("Twoje konto zostało zablokowane przez administratora.")
                        elif haslo_db == hash_password(login_pass):
                            dzis = datetime.now().strftime("%Y-%m-%d")
                            cursor.execute('SELECT ostatnie_logowanie FROM uzytkownicy WHERE nazwa = ?', (login_user,))
                            ost_log = cursor.fetchone()[0]
                            if ost_log != dzis:
                                cursor.execute('UPDATE uzytkownicy SET ostatnie_logowanie = ?, punkty = punkty + 15 WHERE nazwa = ?', (dzis, login_user))
                                st.toast("🎁 Codzienny bonus: +15 punktów XP!", icon="🎉")
                            conn.commit()
                            conn.close()
                            st.session_state.uzytkownik = login_user
                            st.success("Zalogowano pomyślnie!")
                            st.rerun()
                        else:
                            conn.close()
                            st.error("Błędne hasło!")
                    else:
                        conn.close()
                        st.error("Użytkownik nie istnieje!")
                else:
                    st.warning("Uzupełnij pola.")
                    
    with tab2:
        with st.form("register_form"):
            reg_user = st.text_input("Wybierz nazwę:")
            reg_pass = st.text_input("Wybierz hasło:", type="password")
            if st.form_submit_button("Zarejestruj się") and reg_user and reg_pass:
                if reg_user.lower() == "admin":
                    st.error("Ta nazwa jest zarezerwowana.")
                else:
                    try:
                        conn = sqlite3.connect('baza.db')
                        cursor = conn.cursor()
                        cursor.execute('INSERT INTO uzytkownicy (nazwa, haslo, ostatnie_logowanie) VALUES (?, ?, ?)', 
                                       (reg_user, hash_password(reg_pass), datetime.now().strftime("%Y-%m-%d")))
                        conn.commit()
                        conn.close()
                        st.success("Konto utworzone! Możesz się zalogować.")
                    except sqlite3.IntegrityError:
                        st.error("Taka nazwa jest już zajęta.")
    st.stop()

# --- KOMUNIKAT ADMINA ---
conn = sqlite3.connect('baza.db')
cursor = conn.cursor()
cursor.execute('SELECT tresc FROM ogloszenia ORDER BY id DESC LIMIT 1')
glob_ogloszenie = cursor.fetchone()
conn.close()

if glob_ogloszenie:
    st.info(f"📢 **Komunikat:** {glob_ogloszenie[0]}")

# --- BOCZNE MENU ---
st.sidebar.markdown(f"### 👤 {st.session_state.uzytkownik}")

conn = sqlite3.connect('baza.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM powiadomienia WHERE odbiorca = ? AND przeczytane = 0', (st.session_state.uzytkownik,))
nieprzeczytane = cursor.fetchone()[0]
conn.close()

notif_label = f"🔔 Powiadomienia ({nieprzeczytane})" if nieprzeczytane > 0 else "🔔 Powiadomienia"

if st.sidebar.button("Wyloguj się"):
    st.session_state.uzytkownik = ""
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("📌 Nawigacja")

lista_zakladek = [
    "Strona główna", 
    "🔥 Feed: Dla Ciebie",
    "⚡ Trendy / Na czasie",
    "⭐ Subskrypcje",
    "🕒 Historia oglądania",
    "➕ Dodaj film", 
    "👥 Znajomi i Chat", 
    "⚙️ Moje Konto", 
    notif_label,
    "ℹ️ O nas / Zasady"
]

if st.session_state.uzytkownik == "admin":
    lista_zakladek.insert(6, "🛡️ Panel Administratora")

menu = st.sidebar.radio("Wybierz zakładkę", lista_zakladek)

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Opcje widoku i filtrów")
styl_widoku = st.sidebar.radio("Styl wyświetlania:", ["Pionowy strumień (Shorts)", "Siatka kafelková (Grid)"])
ukryj_ai = st.sidebar.checkbox("🚫 Ukryj filmy AI", value=False)
wybrana_kategoria = st.sidebar.selectbox("📂 Kategoria", ["Wszystkie", "Humor", "Gaming", "Edukacja", "Vlogs", "Muzyka", "Inne"])
tryb_sortowania = st.sidebar.selectbox("📊 Sortowanie", ["Najnowsze", "Najpopularniejsze (❤️)", "Najczęściej odtwarzane (👁️)"])
szukaj = st.sidebar.text_input("🔍 Szukaj wideo / hashtagów", "")

if st.sidebar.button("🎲 Szczęśliwy Traf"):
    conn = sqlite3.connect('baza.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM filmy')
    ids = [r[0] for r in cursor.fetchall()]
    conn.close()
    if ids:
        st.session_state.losowy_film = random.choice(ids)
        st.success("Wylosowano film!")

st.title("🎬 ViShort Mega Pro Ultimate")
st.markdown("---")

# =========================================================================
# 1. PANEL ADMINA
# =========================================================================
if menu == "🛡️ Panel Administratora":
    st.header("🛡️ Panel Administratora")
    tab1, tab2, tab3 = st.tabs(["🚨 Zgłoszenia", "👥 Użytkownicy", "📢 Ogłoszenia"])
    with tab1:
        conn = sqlite3.connect('baza.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, film_id, powod, zglaszajacy FROM zgloszenia')
        zgloszenia = cursor.fetchall()
        conn.close()
        if zgloszenia:
            for z_id, f_id, powod, zglaszajacy in zgloszenia:
                st.warning(f"Zgłoszenie filmu ID **{f_id}** | Powód: {powod} (Od: {zglaszajacy})")
                if st.button(f"Usuń film ID {f_id}", key=f"del_z_{z_id}"):
                    conn = sqlite3.connect('baza.db')
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM filmy WHERE id = ?', (f_id,))
                    cursor.execute('DELETE FROM zgloszenia WHERE id = ?', (z_id,))
                    conn.commit()
                    conn.close()
                    st.success("Usunięto.")
                    st.rerun()
        else:
            st.info("Brak zgłoszeń.")
    with tab2:
        conn = sqlite3.connect('baza.db')
        cursor = conn.cursor()
        cursor.execute('SELECT nazwa, status_konta FROM uzytkownicy')
        for u_n, u_s in cursor.fetchall():
            col1, col2 = st.columns([3, 1])
            col1.write(f"Użytkownik: **{u_n}** | Status: `{u_s}`")
            if u_s == "Aktywne":
                if col2.button("Zablokuj", key=f"b_{u_n}"):
                    conn = sqlite3.connect('baza.db')
                    cursor = conn.cursor()
                    cursor.execute('UPDATE uzytkownicy SET status_konta = "Zablokowane" WHERE nazwa = ?', (u_n,))
                    conn.commit()
                    conn.close()
                    st.rerun()
            else:
                if col2.button("Odblokuj", key=f"ub_{u_n}"):
                    conn = sqlite3.connect('baza.db')
                    cursor = conn.cursor()
                    cursor.execute('UPDATE uzytkownicy SET status_konta = "Aktywne" WHERE nazwa = ?', (u_n,))
                    conn.commit()
                    conn.close()
                    st.rerun()
        conn.close()
    with tab3:
        with st.form("ogloszenie_form"):
            tresc = st.text_input("Nowy komunikat globalny:")
            if st.form_submit_button("Opublikuj") and tresc:
                conn = sqlite3.connect('baza.db')
                cursor = conn.cursor()
                cursor.execute('INSERT INTO ogloszenia (tresc) VALUES (?)', (tresc,))
                conn.commit()
                conn.close()
                st.success("Opublikowano!")
                st.rerun()

# =========================================================================
# 2. FEED: DLA CIEBIE
# =========================================================================
elif menu == "🔥 Feed: Dla Ciebie":
    st.header("🔥 Spersonalizowany Feed 'Dla Ciebie'")
    conn = sqlite3.connect('baza.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, autor, tytul, opis_filmu, plik, miniatura, lajki, wyswietlenia, kategoria FROM filmy ORDER BY RANDOM() LIMIT 10')
    for f_id, autor, tytul, opis, plik, mini, lajki, wysw, kat in cursor.fetchall():
        st.subheader(tytul)
        st.caption(f"Autor: {autor} | Kategoria: {kat}")
        if os.path.exists(os.path.join('uploads', plik)):
            st.video(os.path.join('uploads', plik))
        st.markdown("---")
    conn.close()

# =========================================================================
# 3. TRENDY / NA CZASIE
# =========================================================================
elif menu == "⚡ Trendy / Na czasie":
    st.header("⚡ Najpopularniejsze materiały w tym tygodniu")
    conn = sqlite3.connect('baza.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, autor, tytul, plik, wyswietlenia, lajki FROM filmy ORDER BY wyswietlenia DESC, lajki DESC LIMIT 10')
    for f_id, autor, tytul, plik, wysw, lajki in cursor.fetchall():
        st.subheader(f"🔥 {tytul} (👁️ {wysw} wyświetleń | ❤️ {lajki})")
        st.caption(f"Autor: {autor}")
        if os.path.exists(os.path.join('uploads', plik)):
            st.video(os.path.join('uploads', plik))
        st.markdown("---")
    conn.close()

# =========================================================================
# 4. SUBSKRYPCJE
# =========================================================================
elif menu == "⭐ Subskrypcje":
    st.header("⭐ Filmy obserwowanych twórców")
    conn = sqlite3.connect('baza.db')
    cursor = conn.cursor()
    cursor.execute('SELECT tworca FROM obserwujacy WHERE obserwujacy = ?', (st.session_state.uzytkownik,))
    obs = [r[0] for r in cursor.fetchall()]
    if obs:
        q = ','.join(['?'] * len(obs))
        cursor.execute(f'SELECT id, autor, tytul, plik FROM filmy WHERE autor IN ({q}) ORDER BY id DESC', tuple(obs))
        for f_id, autor, tytul, plik in cursor.fetchall():
            st.subheader(tytul)
            st.caption(f"Twórca: {autor}")
            if os.path.exists(os.path.join('uploads', plik)):
                st.video(os.path.join('uploads', plik))
            st.markdown("---")
    else:
        st.info("Nikogo jeszcze nie obserwujesz.")
    conn.close()

# =========================================================================
# 5. HISTORIA OGLĄDANIA
# =========================================================================
elif menu == "🕒 Historia oglądania":
    st.header("🕒 Ostatnio oglądane filmy")
    conn = sqlite3.connect('baza.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT f.id, f.autor, f.tytul, f.plik, h.data_obejrzenia 
        FROM historia h JOIN filmy f ON h.film_id = f.id 
        WHERE h.uzytkownik = ? ORDER BY h.id DESC LIMIT 20
    ''', (st.session_state.uzytkownik,))
    historia = cursor.fetchall()
    conn.close()
    if historia:
        for f_id, autor, tytul, plik, data in historia:
            st.subheader(tytul)
            st.caption(f"Autor: {autor} | Obejrzano: {data}")
            if os.path.exists(os.path.join('uploads', plik)):
                st.video(os.path.join('uploads', plik))
            st.markdown("---")
    else:
        st.info("Twoja historia jest pusta.")

# =========================================================================
# 6. DODAJ FILM (Automatyczne tagowanie AI)
# =========================================================================
elif menu == "➕ Dodaj film":
    st.header("➕ Opublikuj nowy film")
    with st.form("upload_form", clear_on_submit=True):
        tytul = st.text_input("Tytuł filmu:")
        opis_filmu = st.text_area("Opis filmu:")
        kategoria = st.selectbox("Kategoria:", ["Humor", "Gaming", "Edukacja", "Vlogs", "Muzyka", "Inne"])
        
        # Automatyczne tagowanie AI na podstawie tytułu i kategorii
        auto_tagi = f"#{kategoria.lower()} #{tytul.split()[0].lower() if tytul else 'short'}"
        tagi = st.text_input("Hashtagi (wygenerowane automatycznie przez AI):", value=auto_tagi)
        
        col1, col2 = st.columns(2)
        with col1:
            wideo = st.file_uploader("Wybierz plik wideo (mp4, mov):", type=["mp4", "mov"])
        with col2:
            miniatura = st.file_uploader("Miniatura (opcjonalnie):", type=["png", "jpg", "jpeg"])
            
        jest_ai = st.checkbox("🤖 Film wygenerowany przez Sztuczną Inteligencję")
        
        if st.form_submit_button("Opublikuj (+25 XP)") and tytul and wideo:
            nazwa_wideo = wideo.name
            with open(os.path.join('uploads', nazwa_wideo), "wb") as f:
                f.write(wideo.getbuffer())
            
            nazwa_mini = ""
            if miniatura:
                nazwa_mini = "min_" + miniatura.name
                with open(os.path.join('uploads', nazwa_mini), "wb") as f:
                    f.write(miniatura.getbuffer())
            
            conn = sqlite3.connect('baza.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO filmy (autor, tytul, opis_filmu, plik, miniatura, czy_ai, kategoria, data_publikacji, tagi) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (st.session_state.uzytkownik, tytul, opis_filmu, nazwa_wideo, nazwa_mini, 1 if jest_ai else 0, kategoria, datetime.now().strftime("%Y-%m-%d"), tagi))
            cursor.execute('UPDATE uzytkownicy SET punkty = punkty + 25 WHERE nazwa = ?', (st.session_state.uzytkownik,))
            conn.commit()
            conn.close()
            st.success("Opublikowano pomyślnie!")
            st.rerun()

# =========================================================================
# 7. ZNAJOMI I CHAT
# =========================================================================
elif menu == "👥 Znajomi i Chat":
    st.header("👥 Znajomi i Wiadomości")
   
