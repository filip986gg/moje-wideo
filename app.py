import streamlit as st
import sqlite3
import os

# Utworzenie folderu na pliki, jeśli nie istnieje
if not os.path.exists('uploads'):
    os.makedirs('uploads')

# Szybka baza danych
conn = sqlite3.connect('baza.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS filmy (id INTEGER PRIMARY KEY AUTOINCREMENT, autor TEXT, tytul TEXT, plik TEXT)')
conn.commit()
conn.close()

st.title("🎬 Proste Wideo Społecznościowe")

# Formularz do wrzucania
with st.form("f"):
    autor = st.text_input("Twoje imię:")
    tytul = st.text_input("Tytuł filmu:")
    wideo = st.file_uploader("Wybierz plik mp4:", type=["mp4"])
    
    if st.form_submit_button("Opublikuj") and autor and tytul and wideo:
        # Zapis pliku na komputerze
        sciezka = os.path.join('uploads', wideo.name)
        with open(sciezka, "wb") as f:
            f.write(wideo.getbuffer())
        
        # Zapis w bazie danych
        conn = sqlite3.connect('baza.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO filmy (autor, tytul, plik) VALUES (?, ?, ?)', (autor, tytul, wideo.name))
        conn.commit()
        conn.close()
        
        st.success("Dodano film!")
        st.rerun()

st.markdown("---")
st.subheader("Ostatnie filmy:")

# Pobieranie i wyświetlanie filmów z bazy
conn = sqlite3.connect('baza.db')
cursor = conn.cursor()
cursor.execute('SELECT autor, tytul, plik FROM filmy ORDER BY id DESC')
filmy = cursor.fetchall()
conn.close()

for autor, tytul, plik in filmy:
    st.write(f"### {tytul}")
    st.write(f"Dodane przez: **{autor}**")
    st.video(os.path.join('uploads', plik))
    st.markdown("---")