from rfp_reader.pdf_reader import list_rfp_files, extract_text_from_pdf

def main():
    files = list_rfp_files()
    if not files:
        print("Brak PDF w data/rfps/")
        return

    for f in files:
        print("=" * 80)
        print("RFP:", f.name)
        print("=" * 80)
        txt = extract_text_from_pdf(f)
        print(txt[:1500], "\n")

if __name__ == "__main__":
    main()
