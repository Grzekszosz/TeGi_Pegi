from cv_reader.pdf_reader import list_cv_files, extract_text_from_pdf

def main():
    pdf_files = list_cv_files()
    if not pdf_files:
        print("⚠️ Brak plików PDF w katalogu data/cvs/")
        return

    for pdf_path in pdf_files:
        print("=" * 80)
        print("CV:", pdf_path.name)
        print("=" * 80)

        text = extract_text_from_pdf(pdf_path)

        print(text[:1200])   # pokazujemy pierwsze 1200 znaków
        print("\n\n")

if __name__ == "__main__":
    main()
