import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

firebase_credentials = {
    "type": st.secrets["FIREBASE_CREDENTIALS"]["type"],
    "project_id": st.secrets["FIREBASE_CREDENTIALS"]["project_id"],
    "private_key_id": st.secrets["FIREBASE_CREDENTIALS"]["private_key_id"],
    "private_key": st.secrets["FIREBASE_CREDENTIALS"]["private_key"].replace('\\n', '\n'),  # Fix multiline key
    "client_email": st.secrets["FIREBASE_CREDENTIALS"]["client_email"],
    "client_id": st.secrets["FIREBASE_CREDENTIALS"]["client_id"],
    "auth_uri": st.secrets["FIREBASE_CREDENTIALS"]["auth_uri"],
    "token_uri": st.secrets["FIREBASE_CREDENTIALS"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["FIREBASE_CREDENTIALS"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["FIREBASE_CREDENTIALS"]["client_x509_cert_url"],
    "universe_domain": st.secrets["FIREBASE_CREDENTIALS"]["universe_domain"],
}

# 🔹 Firebase Initialization
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_credentials)
    firebase_admin.initialize_app(cred)
db = firestore.client()

# ---------- Load & Save Functions for Firestore -----------

def load_library():
    books_ref = db.collection('library')
    docs = books_ref.stream()
    return [doc.to_dict() for doc in docs]

def save_book(book):
    db.collection('library').add(book)

def delete_book(title):
    books_ref = db.collection('library')
    docs = books_ref.where('title', '==', title).stream()
    for doc in docs:
        doc.reference.delete()

# ---------- Streamlit App Start -------------
st.title("📚 Personal Library Manager (with Firestore)")

# Initialize session state for library
if 'library' not in st.session_state:
    st.session_state.library = load_library()

# ---------- Add a Book Section -------------

with st.expander("➕ Add a Book"):
    with st.form("Add Book Form", clear_on_submit=True):
        title = st.text_input("Book Title")
        author = st.text_input("Author")
        year = st.number_input("Publication Year", min_value=0, step=1)
        genre = st.text_input("Genre")
        read_status = st.checkbox("Have you read this book?")
        submit_add = st.form_submit_button("Add Book")

        if submit_add:
            if not title.strip():
                st.error("❌ please fill all the fields")
            elif not author.strip():
                st.error("❌ please fill all the fields")
            else:
                book = {
                    'title': title.strip(),
                    'author': author.strip(),
                    'year': int(year),
                    'genre': genre.strip(),
                    'read': read_status
                }
                save_book(book)
                st.session_state.library.append(book) 
                st.success(f"✅ Book '{title}' added successfully!")

# ---------- Remove a Book Section -------------

with st.expander("❌ Remove a Book"):
    titles = [book['title'] for book in st.session_state.library]
    if titles:
        selected_book = st.selectbox("Select a book to remove", titles)
        if st.button("Remove Book"):
            delete_book(selected_book)
            st.session_state.library = [book for book in st.session_state.library if book['title'] != selected_book]  
            st.success(f"✅ Book '{selected_book}' removed successfully!")
            st.rerun()
    else:
        st.info("Your library is empty.")

# ---------- Search for a Book Section -------------

with st.expander("🔍 Search for a Book"):
    search_option = st.radio("Search by", ["Author", "Book Title"])
    query = st.text_input(f"Enter {search_option}")

    if st.button("Search"):
        key = 'author' if search_option == "Author" else 'title'
        matches = [book for book in st.session_state.library if query.lower() in book[key].lower()]

        if matches:
            st.subheader("📖 Search Results:")
            for book in matches:
                status = "✅ Read" if book['read'] else "❌ Unread"
                st.markdown(f"- **{book['title']}** by *{book['author']}* ({book['year']}) - Genre: {book['genre']} - Status: {status}")
        else:
            st.warning("⚠️ No book found.")

# ---------- Display All Books Section -------------

with st.expander("📚 Display All Books"):
    if st.session_state.library:
        st.subheader("Your Library:")
        for book in st.session_state.library:
            status = "✅ Read" if book['read'] else "❌ Unread"
            st.markdown(f"- **{book['title']}** by *{book['author']}* ({book['year']}) - Genre: {book['genre']} - Status: {status}")
    else:
        st.info("Your library is empty.")

# ---------- Display Statistics Section -------------

with st.expander("📊 Library Statistics"):
    total_books = len(st.session_state.library)
    read_books = sum(1 for book in st.session_state.library if book['read'])
    read_percentage = (read_books / total_books * 100) if total_books else 0

    st.metric("Total Books", total_books)
    st.metric("Books Read", read_books)
    st.metric("Read Percentage", f"{read_percentage:.2f}%")

# ---------- Footer Save on Close -------------

st.info("Note: All changes are automatically saved to Firestore Database.")
