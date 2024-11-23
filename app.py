from flask import Flask, request, render_template, redirect, url_for, flash, send_file
import whisper
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from io import BytesIO
import pydub

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'uploads'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Charger le modèle Whisper
model = whisper.load_model("base")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # Vérifier si le fichier audio est valide
        try:
            audio = pydub.AudioSegment.from_file(file_path)
            if audio.duration_seconds == 0:
                flash('Le fichier audio est vide ou corrompu', 'error')
                return redirect(request.url)
        except Exception as e:
            flash(f'Erreur lors de la lecture du fichier audio: {e}', 'error')
            return redirect(request.url)

        # Transcrire l'audio
        try:
            result = model.transcribe(file_path)
            # Générer le PDF
            pdf_path = generate_pdf(result["text"])
            flash('Transcription terminée!', 'success')
            return send_file(pdf_path, as_attachment=True, download_name='transcription.pdf')
        except Exception as e:
            flash(f'Erreur lors de la transcription: {e}', 'error')
            return redirect(request.url)

def generate_pdf(text):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Définir le titre du document
    title = "Transcription de l'audio"
    story.append(Paragraph(title, styles['Title']))
    story.append(Spacer(1, 12))

    # Définir le contenu de la transcription
    text_lines = text.split("\n")

    for line in text_lines:
        story.append(Paragraph(line, styles['BodyText']))
        story.append(Spacer(1, 12))  # Ajuste cette valeur pour l'espacement entre les lignes

    # Construire le document PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

if __name__ == '__main__':
    app.run(debug=True)
