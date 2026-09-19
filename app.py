import streamlit as st
import sqlite3
import os
import hashlib
from datetime import datetime, timedelta
import random

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
            haslo TEXT,
            opis TEXT DEFAULT '',
            zdjecie_profilowe TEXT DEFAULT '',
            tlo_profilu TEXT DEFAULT '',
            linki TEXT DEFAULT '',
            ostatnia_zmiana_nazwy TEXT DEFAULT ''
        )
    ''')
    
    # Tabela filmów (z dodatkowymi kolumnami widoków i kategorii)
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
            wyswietlenia INTEGER DEFAULT 0,
            kategoria TEXT DEFAULT 'Inne'
        )
    ''')
    
    # Tabela na komentarze (z lajkami komentarzy)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS komentarze (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            film_id INTEGER,
            autor TEXT,
            tekst TEXT,
            lajki INTEGER DEFAULT 0
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
    
    # Tabela powiadomień
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS powiadomienia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            odbiorca TEXT,
            tekst TEXT,
            przeczytane INTEGER DEFAULT 0
        )
    ''')

    # Tabela zgłoszeń
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS zgloszenia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            film_id INTEGER,
            powod TEXT,
            zglaszajacy TEXT
        )
    ''')
    
    # --- BEZPIECZNA MIGRACJA KOLUMN UŻYTKOWNIKÓW ---
    cursor.execute("PRAGMA table_info(uzytkownicy)")
    u_cols = [c[1] for c in cursor.fetchall()]
    if 'opis' not in u_cols:
        cursor.execute("ALTER TABLE uzytkownicy ADD COLUMN opis TEXT DEFAULT ''")
    if 'zdjecie_profilowe' not in u_cols:
        cursor.execute("ALTER TABLE uzytkownicy ADD COLUMN zdjecie_profilowe TEXT DEFAULT ''")
    if 'tlo_profilu' not in u_cols:
        cursor.execute("ALTER TABLE uzytkownicy ADD COLUMN tlo_profilu TEXT DEFAULT ''")
    if 'linki' not in u_cols:
        cursor.execute("ALTER TABLE uzytkownicy ADD COLUMN linki TEXT DEFAULT ''")
    if 'ostatnia_zmiana_nazwy' not in u_cols:
        cursor.execute("ALTER TABLE uzytkownicy ADD COLUMN ostatnia_zmiana_nazwy TEXT DEFAULT ''")

    # --- BEZPIECZNA MIGRACJA KOLUMN FILMÓW ---
    cursor.execute("PRAGMA table_info(filmy)")
    f_cols = [c[1] for c in cursor.fetchall()]
    if 'opis_filmu' not in f_cols:
        cursor.execute("ALTER TABLE filmy ADD COLUMN opis_filmu TEXT DEFAULT ''")
    if 'miniatura' not in f_cols:
        cursor.execute("ALTER TABLE filmy ADD COLUMN miniatura TEXT DEFAULT ''")
    if 'prawa_autorskie' not in f_cols:
        cursor.execute("ALTER TABLE filmy ADD COLUMN prawa_autorskie TEXT DEFAULT 'Zweryfikowane (Czyste)'")
    if 'czy_ai' not in f_cols:
        cursor.execute("ALTER TABLE filmy ADD COLUMN czy_ai INTEGER DEFAULT 0")
    if 'wyswietlenia' not in f_cols:
        cursor.execute("ALTER TABLE filmy ADD COLUMN wyswietlenia INTEGER DEFAULT 0")
    if 'kategoria' not in f_cols:
        cursor.execute("ALTER TABLE filmy ADD COLUMN kategoria TEXT DEFAULT 'Inne'")

    # --- BEZPIECZNA MIGRACJA KOMENTARZY ---
    cursor.execute("PRAGMA table_info(komentarze)")
    k_cols = [c[1] for c in cursor.fetchall()]
    if 'lajki' not in k_cols:
        cursor.execute("ALTER TABLE komentarze ADD COLUMN lajki INTEGER DEFAULT 0")
        
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

# --- BOCZNE MENU Z IKONAMI ---
st.sidebar.markdown(f"### 👤 {st.session_state.uzytkownik}")

# Sprawdzanie nieprzeczytanych powiadomień (Funkcja 2)
conn = sqlite3.connect('baza.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM powiadomienia WHERE odbiorca = ? AND przeczytane = 0', (st.session_state.uzytkownik,))
nieprzeczytane_count = cursor.fetchone()[0]
conn.close()

notif_label = f"🔔 Powiadomienia ({nieprzeczytane_count})" if nieprzeczytane_count > 0 else "🔔 Powiadomienia"

if st.sidebar.button("Wyloguj się"):
    st.session_state.uzytkownik = ""
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("📌 Nawigacja")
menu = st.sidebar.radio("Wybierz zakładkę", [
    "Strona główna", 
    "➕ Dodaj film", 
    "👥 Znajomi i Chat", 
    "⚙️ Moje Konto", 
    notif_label,
    "ℹ️ O nas / Zasady"
])

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Filtry i Opcje")
ukryj_ai = st.sidebar.checkbox("🚫 Ukryj filmy AI", value=False) # Funkcja 19
wybrana_kategoria_filtr = st.sidebar.selectbox("📂 Kategoria", ["Wszystkie", "Humor", "Gaming", "Edukacja", "Vlogs", "Muzyka", "Inne"]) # Funkcja 4
tryb_sortowania = st.sidebar.selectbox("📊 Sortowanie", ["Najnowsze", "Najpopularniejsze (❤️)", "Najczęściej odtwarzane (👁️)"]) # Funkcja 14

if st.sidebar.button("🎲 Szczęśliwy Traf (Losowy film)"): # Funkcja 13
    conn = sqlite3.connect('baza.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM filmy')
    wszystkie_id = [r[0] for r in cursor.fetchall()]
    conn.close()
    if wszystkie_id:
        st.session_state.losowy_film = random.choice(wszystkie_id)
        st.success("Wylosowano film! Znajdziesz go na górze strony głównej.")
    else:
        st.warning("Brak filmów w bazie.")

# --- GŁÓWNY NAGŁÓWEK I WYSZUKIWARKA ---
col_title, col_search = st.columns([2, 3])
with col_title:
    st.title("🎬 ViShort")
with col_search:
    szukaj = st.text_input("🔍 Szukaj filmów lub autorów...", "")

st.markdown("---")

# --- ZAKŁADKA: DODAJ FILM (Funkcja 16, 17, 19, 20) ---
if menu == "➕ Dodaj film":
    st.header("➕ Opublikuj nowy film")
    with st.form("upload_form", clear_on_submit=True):
        tytul = st.text_input("Tytuł filmu:")
        opis_filmu = st.text_area("Opis filmu:")
        kategoria = st.selectbox("Wybierz kategorię:", ["Humor", "Gaming", "Edukacja", "Vlogs", "Muzyka", "Inne"])
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            wideo = st.file_uploader("Wybierz plik wideo (mp4, mov):", type=["mp4", "mov"])
        with col_f2:
            miniatura = st.file_uploader("Zdjęcie początkowe / Miniatura (opcjonalnie):", type=["png", "jpg", "jpeg"])
            
        jest_ai = st.checkbox("🤖 Ten film został wygenerowany przez Sztuczną Inteligencję (AI)")
            
        submitted = st.form_submit_button("Opublikuj")
        
        if submitted:
            if tytul and wideo:
                nazwa_wideo = wideo.name
                sciezka_wideo = os.path.join('uploads', nazwa_wideo)
                with open(sciezka_wideo, "wb") as f:
                    f.write(wideo.getbuffer())
                
                nazwa_miniatury = ""
                if miniatura:
                    nazwa_miniatury = "min_" + miniatura.name
                    sciezka_min = os.path.join('uploads', nazwa_miniatury)
                    with open(sciezka_min, "wb") as f:
                        f.write(miniatura.getbuffer())
                
                prawa = "⚠️ Oznaczone jako AI" if jest_ai else "✅ Zweryfikowane - Brak naruszeń"
                ai_val = 1 if jest_ai else 0
                
                conn = sqlite3.connect('baza.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO filmy (autor, tytul, opis_filmu, plik, miniatura, prawa_autorskie, czy_ai, lajki, wyswietlenia, kategoria) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, ?)
                ''', (st.session_state.uzytkownik, tytul, opis_filmu, nazwa_wideo, nazwa_miniatury, prawa, ai_val, kategoria))
                conn.commit()
                conn.close()
                
                st.success("Film został opublikowany!")
                st.rerun()
            else:
                st.error("Podaj tytuł i wybierz plik wideo!")

# --- ZAKŁADKA: MOJE KONTO (Funkcja 8, 15, 18) ---
elif menu == "⚙️ Moje Konto":
    st.header("⚙️ Ustawienia Konta i Statystyki")
    
    conn = sqlite3.connect('baza.db')
    cursor = conn.cursor()
    cursor.execute('SELECT nazwa, opis, zdjecie_profilowe, tlo_profilu, linki, ostatnia_zmiana_nazwy FROM uzytkownicy WHERE nazwa = ?', (st.session_state.uzytkownik,))
    u_data = cursor.fetchone()
    
    cursor.execute('SELECT COUNT(*), SUM(lajki), SUM(wyswietlenia) FROM filmy WHERE autor = ?', (st.session_state.uzytkownik,))
    stat_filmy, stat_lajki, stat_wyswietlenia = cursor.fetchone()
    stat_lajki = stat_lajki if stat_lajki else 0
    stat_wyswietlenia = stat_wyswietlenia if stat_wyswietlenia else 0
    conn.close()
    
    st.subheader("📊 Statystyki Twojego Konta")
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    col_s1.metric("Wrzucone filmy", stat_filmy)
    col_s2.metric("Polubienia (❤️)", stat_lajki)
    col_s3.metric("Wyświetlenia (👁️)", stat_wyswietlenia)
    col_s4.metric("Status konta", "Aktywne 🟢")
    
    st.markdown("---")
    st.subheader("✏️ Edytuj Profil")
    
    aktualna_nazwa, opis_p, zdj_p, tlo_p, linki_p, ostatnia_zmiana = u_data
    
    with st.form("profil_form"):
        nowa_nazwa = st.text_input("Nazwa użytkownika:", value=aktualna_nazwa)
        nowy_opis = st.text_area("O mnie (opis profilu / status):", value=opis_p if opis_p else "")
        nowe_linki = st.text_input("Linki do Twoich stron:", value=linki_p if linki_p else "")
        
        col_e1, col_e2 = st.columns(2)
        with col_e1:
             nowe_zdj = st.file_uploader("Zdjęcie profilowe:", type=["png", "jpg", "jpeg"])
        with col_e2:
            nowe_tlo = st.file_uploader("Zdjęcie w tle:", type=["png", "jpg", "jpeg"])
            
        zapisz_profil = st.form_submit_button("Zapisz zmiany")
        
        if zapisz_profil:
            conn = sqlite3.connect('baza.db')
            cursor = conn.cursor()
            
            docelowa_nazwa = aktualna_nazwa
            if nowa_nazwa != aktualna_nazwa:
                dzis = datetime.now()
                mozna_zmienic = True
                if ostatnia_zmiana:
                    data_ostatniej = datetime.strptime(ostatnia_zmiana, "%Y-%m-%d")
                    if dzis - data_ostatniej < timedelta(days=30):
                        mozna_zmienic = False
                        
                if mozna_zmienic:
                    try:
                        cursor.execute('UPDATE uzytkownicy SET nazwa = ? WHERE nazwa = ?', (nowa_nazwa, aktualna_nazwa))
                        cursor.execute('UPDATE filmy SET autor = ? WHERE autor = ?', (nowa_nazwa, aktualna_nazwa))
                        cursor.execute('UPDATE komentarze SET autor = ? WHERE autor = ?', (nowa_nazwa, aktualna_nazwa))
                        cursor.execute('UPDATE uzytkownicy SET ostatnia_zmiana_nazwy = ? WHERE nazwa = ?', (dzis.strftime("%Y-%m-%d"), nowa_nazwa))
                        docelowa_nazwa = nowa_nazwa
                        st.session_state.uzytkownik = nowa_nazwa
                        st.success("Nazwa zmieniona pomyślnie!")
                    except sqlite3.IntegrityError:
                        st.error("Ta nazwa jest już zajęta!")
                else:
                    st.warning("Nazwę można zmienić tylko raz na miesiąc!")
            
            z_path = zdj_p
            if nowe_zdj:
                z_path = "ava_" + nowe_zdj.name
                with open(os.path.join('uploads', z_path), "wb") as f:
                    f.write(nowe_zdj.getbuffer())
                    
            t_path = tlo_p
            if nowe_tlo:
                t_path = "bg_" + nowe_tlo.name
                with open(os.path.join('uploads', t_path), "wb") as f:
                    f.write(nowe_tlo.getbuffer())
                    
            cursor.execute('''
                UPDATE uzytkownicy 
                SET opis = ?, zdjecie_profilowe = ?, tlo_profilu = ?, linki = ? 
                WHERE nazwa = ?
            ''', (nowy_opis, z_path, t_path, nowe_linki, docelowa_nazwa))
            
            conn.commit()
            conn.close()
            st.success("Profil zaktualizowany!")
            st.rerun()

    st.markdown("---")
    st.subheader("🎬 Twoje opublikowane filmy (Zarządzanie)")
    conn = sqlite3.connect('baza.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, tytul, lajki, wyswietlenia FROM filmy WHERE autor = ?', (st.session_state.uzytkownik,))
    moje_filmy = cursor.fetchall()
    conn.close()

    if moje_filmy:
        for m_id, m_tytul, m_lajki, m_wysw in moje_filmy:
            col_m1, col_m2, col_m3 = st.columns([3, 1, 1])
            col_m1.write(f"🎞️ **{m_tytul}** (❤️ {m_lajki} | 👁️ {m_wysw})")
            if col_m3.button("🗑️ Usuń", key=f"del_film_{m_id}"):
                conn = sqlite3.connect('baza.db')
                cursor = conn.cursor()
                cursor.execute('DELETE FROM filmy WHERE id = ?', (m_id,))
                cursor.execute('DELETE FROM komentarze WHERE film_id = ?', (m_id,))
                conn.commit()
                conn.close()
                st.success("Usunięto film.")
                st.rerun()
    else:
            st.info("Nie masz jeszcze żadnych filmów.")

# --- ZAKŁADKA: ZNAJOMI I CHAT ---
elif menu == "👥 Znajomi i Chat":
    st.header("👥 Znajomi i Wiadomości")
    
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
            st.info("Brak znajomych.")
            
        st.markdown("---")
        st.subheader("Dodaj znajomego")
        with st.form("add_friend_form", clear_on_submit=True):
            szukany_login = st.text_input("Nazwa użytkownika:")
            dodaj_btn = st.form_submit_button("Dodaj")
            if dodaj_btn and szukany_login:
                if szukany_login == st.session_state.uzytkownik:
                    st.error("Nie możesz dodać siebie!")
                else:
                    conn = sqlite3.connect('baza.db')
                    cursor = conn.cursor()
                    cursor.execute('SELECT nazwa FROM uzytkownicy WHERE nazwa = ?', (szukany_login,))
                    istnieje = cursor.fetchone()
                    if istnieje:
                        try:
                            cursor.execute('INSERT INTO znajomi (uzytkownik, znajomy) VALUES (?, ?)', (st.session_state.uzytkownik, szukany_login))
                            conn.commit()
                            st.success(f"Dodano {szukany_login}!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.warning("Już na liście.")
                    else:
                        st.error("Brak takiego użytkownika.")
                    conn.close()
                    
    with col_czat:
        if wybrany_znajomy:
            st.subheader(f"💬 Czat z: {wybrany_znajomy}")
            
            conn = sqlite3.connect('baza.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT nadawca, tekst FROM wiadomosci 
                WHERE (nadawca = ? AND odbiorca = ?) OR (nadawca = ? AND odbiorca = ?)
                ORDER BY id ASC
            ''', (st.session_state.uzytkownik, wybrany_znajomy, wybrany_znajomy, st.session_state.uzytkownik))
            wiadomosci = cursor.fetchall()
            conn.close()
            
            chat_container = st.container(height=400)
            with chat_container:
                if wiadomosci:
                    for nadawca, tekst in wiadomosci:
                        if nadawca == st.session_state.uzytkownik:
                            st.chat_message("user").write(tekst)
                        else:
                            st.chat_message("assistant").write(f"**{nadawca}**: {tekst}")
                else:
                    st.info("Brak wiadomości.")
            
            tekst_wiadomosci = st.chat_input("Napisz wiadomość...")
            if tekst_wiadomosci:
                conn = sqlite3.connect('baza.db')
                cursor = conn.cursor()
                cursor.execute('INSERT INTO wiadomosci (nadawca, odbiorca, tekst) VALUES (?, ?, ?)', 
                               (st.session_state.uzytkownik, wybrany_znajomy, tekst_wiadomosci))
                # Dodaj powiadomienie dla odbiorcy
                cursor.execute('INSERT INTO powiadomienia (odbiorca, tekst, przeczytane) VALUES (?, ?, 0)',
                               (wybrany_znajomy, f"Nowa wiadomość od {st.session_state.uzytkownik}"))
                conn.commit()
                conn.close()
                st.rerun()
        else:
            st.info("Wybierz znajomego z listy.")

# --- ZAKŁADKA: POWIADOMIENIA (Funkcja 2) ---
elif menu.startswith("🔔 Powiadomienia"):
    st.header("🔔 Twoje Powiadomienia")
    
    conn = sqlite3.connect('baza.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, tekst, przeczytane FROM powiadomienia WHERE odbiorca = ? ORDER BY id DESC', (st.session_state.uzytkownik,))
    powiadomienia = cursor.fetchall()
    
    # Oznacz jako przeczytane
    cursor.execute('UPDATE powiadomienia SET przeczytane = 1 WHERE odbiorca = ?', (st.session_state.uzytkownik,))
    conn.commit()
    conn.close()

    if powiadomienia:
        for p_id, p_tekst, p_prze in powiadomienia:
            status_p = "📌" if p_prze == 0 else "✔️"
            st.write(f"{status_p} {p_tekst}")
    else:
        st.info("Brak powiadomień.")

# --- ZAKŁADKA: O NAS / ZASADY (Funkcja 9) ---
elif menu == "ℹ️ O nas / Zasady":
    st.header("ℹ️ O platformie ViShort i Regulamin")
    st.markdown("""
    Witaj w **ViShort** – nowoczesnej platformie wideo stworzonej z pasji do dzielenia się krótkimi materiałami i interakcji społecznościowych!
    
    ### 🛡️ Zasady społeczności:
    1. **Szacunek przede wszystkim** – Bądź miły dla innych użytkowników w komentarzach i czacie.
    2. **Autorskie treści** – Publikuj materiały, do których masz prawa, lub oznaczaj filmy wygenerowane przez sztuczną inteligencję (AI).
    3. **Bezpieczeństwo** – Nie spamuj i nie naruszaj prywatności innych.
    
    Dziękujemy, że jesteś częścią naszej społeczności! 🎬❤️
    """)

# --- ZAKŁADKA: STRONA GŁÓWNA (Funkcja 3, 4, 6, 13, 14, 19) ---
else:
    conn = sqlite3.connect('baza.db')
    cursor = conn.cursor()
    
    # Obsługa sortowania (Funkcja 14)
    order_query = "ORDER BY id DESC"
    if tryb_sortowania == "Najpopularniejsze (❤️)":
        order_query = "ORDER BY lajki DESC"
    elif tryb_sortowania == "Najczęściej odtwarzane (👁️)":
        order_query = "ORDER BY wyswietlenia DESC"
        
    cursor.execute(f'SELECT id, autor, tytul, opis_filmu, plik, miniatura, prawa_autorskie, czy_ai, lajki, wyswietlenia, kategoria FROM filmy {order_query}')
    filmy = cursor.fetchall()
    conn.close()

    # Filtry
    if ukryj_ai:
        filmy = [f for f in filmy if f[7] == 0]

    if wybrana_kategoria_filtr != "Wszystkie":
        filmy = [f for f in filmy if f[10] == wybrana_kategoria_filtr]

    if szukaj:
        filmy = [f for f in filmy if szukaj.lower() in f[1].lower() or szukaj.lower() in f[2].lower() or szukaj.lower() in f[3].lower()]

    # Jeśli użyto szczęśliwego trafu, przesuń wylosowany film na początek
    if 'losowy_film' in st.session_state:
        target_id = st.session_state.losowy_film
        filmy = sorted(filmy, key=lambda x: 0 if x[0] == target_id else 1)
        del st.session_state.losowy_film

    if filmy:
        for film_id, autor, tytul, opis_filmu, plik, miniatura, prawa_autorskie, czy_ai, lajki, wyswietlenia, kategoria in filmy:
            col_video, col_actions = st.columns([3, 1])
            
            with col_video:
                st.subheader(tytul)
                ai_badge = " | 🤖 **Zawiera AI**" if czy_ai == 1 else ""
                st.caption(f"👤 Autor: **{autor}** | 📂 Kategoria: `{kategoria}` | 🛡️ {prawa_autorskie}{ai_badge} | 👁️ Wyświetlenia: **{wyswietlenia}**")
                if opis_filmu:
                    st.write(opis_filmu)
                
                sciezka_pliku = os.path.join('uploads', plik)
                sciezka_mini = os.path.join('uploads', miniatura) if miniatura else ""
                
                if os.path.exists(sciezka_pliku):
                    # Zliczanie wyświetlenia (Funkcja 3) przy renderowaniu wideo
                    if f"viewed_{film_id}" not in st.session_state:
                        conn = sqlite3.connect('baza.db')
                        cursor = conn.cursor()
                        cursor.execute('UPDATE filmy SET wyswietlenia = wyswietlenia + 1 WHERE id = ?', (film_id,))
                        conn.commit()
                        conn.close()
                        st.session_state[f"viewed_{film_id}"] = True

                    if miniatura and os.path.exists(sciezka_mini):
                        st.video(sciezka_pliku, poster=sciezka_mini)
                    else:
                        st.video(sciezka_pliku)
                else:
                    st.warning("Plik wideo nie istnieje na serwerze.")
            
            with col_actions:
                st.write("") 
                st.write("")
                if st.button(f"❤️ Polub ({lajki})", key=f"like_{film_id}"):
                    conn = sqlite3.connect('baza.db')
                    cursor = conn.cursor()
                    cursor.execute('UPDATE filmy SET lajki = lajki + 1 WHERE id = ?', (film_id,))
                    # Powiadomienie dla autora filmu
                    cursor.execute('SELECT autor FROM filmy WHERE id = ?', (film_id,))
                    aut_f = cursor.fetchone()[0]
                    if aut_f != st.session_state.uzytkownik:
                        cursor.execute('INSERT INTO powiadomienia (odbiorca, tekst, przeczytane) VALUES (?, ?, 0)',
                                       (aut_f, f"Użytkownik {st.session_state.uzytkownik} polubił Twój film '{tytul}'!"))
                    conn.commit()
                    conn.close()
                    st.rerun()
                
                # Funkcja 5: Zgłoś film
                with st.popover("⚠️ Zgłoś"):
                    powod_zgl = st.text_input("Powód zgłoszenia:", key=f"z_pow_{film_id}")
                    if st.button("Wyślij zgłoszenie", key=f"btn_z_{film_id}"):
                        if powod_zgl:
                            conn = sqlite3.connect('baza.db')
                            cursor = conn.cursor()
                            cursor.execute('INSERT INTO zgloszenia (film_id, powod, zglaszajacy) VALUES (?, ?, ?)', (film_id, powod_zgl, st.session_state.uzytkownik))
                            conn.commit()
                            conn.close()
                            st.success("Zgłoszenie wysłane do administratora.")
                        else:
                            st.warning("Podaj powód zgłoszenia.")

            # Sekcja komentarzy (z lajkami komentarzy - Funkcja 6)
            with st.expander(f"💬 Komentarze do: {tytul}"):
                conn = sqlite3.connect('baza.db')
                cursor = conn.cursor()
                cursor.execute('SELECT id, autor, tekst, lajki FROM komentarze WHERE film_id = ?', (film_id,))
                komentarze = cursor.fetchall()
                conn.close()
                
                if komentarze:
                    for k_id, k_autor, k_tekst, k_lajki in komentarze:
                        col_k1, col_k2 = st.columns([5, 1])
                        col_k1.markdown(f"**{k_autor}**: {k_tekst}")
                        if col_k2.button(f"❤️ {k_lajki}", key=f"klike_{k_id}"):
                            conn = sqlite3.connect('baza.db')
                            cursor = conn.cursor()
                            cursor.execute('UPDATE komentarze SET lajki = lajki + 1 WHERE id = ?', (k_id,))
                            conn.commit()
                            conn.close()
                            st.rerun()
                else:
                    st.info("Brak komentarzy. Bądź pierwszy!")
                
                with st.form(key=f"comm_form_{film_id}", clear_on_submit=True):
                    nowy_kom = st.text_input("Napisz komentarz...", key=f"input_comm_{film_id}")
                    wyslij_kom = st.form_submit_button("Wyślij")
                    if wyslij_kom and nowy_kom:
                        conn = sqlite3.connect('baza.db')
                        cursor = conn.cursor()
                        cursor.execute('INSERT INTO komentarze (film_id, autor, tekst, lajki) VALUES (?, ?, ?, 0)', (film_id, st.session_state.uzytkownik, nowy_kom))
                        
                        # Powiadomienie dla autora filmu
                        cursor.execute('SELECT autor FROM filmy WHERE id = ?', (film_id,))
                        aut_f = cursor.fetchone()[0]
                        if aut_f != st.session_state.uzytkownik:
                            cursor.execute('INSERT INTO powiadomienia (odbiorca, tekst, przeczytane) VALUES (?, ?, 0)',
                                           (aut_f, f"Nowy komentarz od {st.session_state.uzytkownik} pod filmem '{tytul}'"))
                        
                        conn.commit()
                        conn.close()
                        st.rerun()

            st.markdown("---")
    else:
        st.info("Brak filmów spełniających wybrane kryteria.")
