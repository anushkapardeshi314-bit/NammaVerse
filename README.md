# NammaVerse — Kannada AI Platform

A Streamlit prototype combining six Kannada-focused challenge areas:
1. Kannada document digitization / OCR
2. Kannada learning
3. Voice and pronunciation demo
4. Regional language and heritage explorer
5. Karnataka travel itinerary planner
6. Accessibility, searchable documents, and quality evaluation

## Deploy on Streamlit Community Cloud

1. Create a GitHub repository and upload `app.py`, `requirements.txt`, and `packages.txt`.
2. In Streamlit Community Cloud, create an app from that repository.
3. Set the main file path to `app.py`.
4. Deploy.

The app uses Tesseract OCR. `packages.txt` installs the Tesseract system package and Kannada language data on Streamlit's Linux environment.

## Local run

Install Python, then install the OS package Tesseract OCR with Kannada language data.
- Ubuntu/Debian: `sudo apt-get install tesseract-ocr tesseract-ocr-kan`
- macOS: install Tesseract and the Kannada trained data using your package manager.
- Windows: install Tesseract OCR and Kannada trained data, then ensure `tesseract.exe` is on PATH.

Then:
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Important implementation notes

- The OCR pipeline is real, but accuracy depends on scan quality, Tesseract language data, fonts, and handwriting style.
- Handwriting mode enhances the image but does not magically provide a specialized handwriting model. For research-level handwriting recognition, integrate and evaluate a model trained on Kannada handwriting.
- The current document Q&A is keyword-based search and summaries are extractive. Connect an LLM + retrieval pipeline to enable grounded generative answers.
- Browser speech synthesis is best-effort. Kannada voice availability depends on the visitor's browser/device.
- The library is session-only. Add authentication and a database/object store before production use.
- Heritage entries are illustrative starter data and require community validation before public release.
- Travel suggestions are draft itineraries and are not live routing, opening hours, or booking information.
- Avoid uploading sensitive personal/legal/medical documents to a public demo.
