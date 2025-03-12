from flask import Flask, request, redirect, url_for, render_template, jsonify
from werkzeug.utils import secure_filename
import os
import subprocess

app = Flask(__name__)

# Configuration
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['RESULT_FOLDER'] = os.path.join('static', 'results')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Run the GFPGAN script
        result = subprocess.run([
            'venv\\Scripts\\python', 'C:\\gamma\\Image restore\\GFPGAN\\inference_gfpgan.py',
            '-i', file_path, '-o', app.config['RESULT_FOLDER'], '-v', '1.3', '-s', '2'
        ], capture_output=True, text=True)
        
        print("Subprocess stdout:", result.stdout)
        print("Subprocess stderr:", result.stderr)
        
        # Ensure the paths are correct
        restored_img_path = os.path.join(app.config['RESULT_FOLDER'], 'restored_imgs', filename)
        if os.path.exists(restored_img_path):
            print(f"Restored image file found at: {restored_img_path}")
            return jsonify({'status': 'success', 'redirect_url': url_for('uploaded_file', filename=filename)})
        else:
            return jsonify({'status': 'error', 'message': 'Restored image file not found'}), 500
    
    return jsonify({'status': 'error', 'message': 'Invalid file type'}), 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    # Define the paths for different results
    result_dir = app.config['RESULT_FOLDER']
    
    # Construct the filenames for various result types
    base_filename = filename.rsplit('.', 1)[0]
    
    cropped_faces = [f for f in os.listdir(os.path.join(result_dir, 'cropped_faces')) if f.startswith(base_filename)]
    restored_faces = [f for f in os.listdir(os.path.join(result_dir, 'restored_faces')) if f.startswith(base_filename)]
    comparisons = [f for f in os.listdir(os.path.join(result_dir, 'cmp')) if f.startswith(base_filename)]
    
    # Render the result page with all required context
    return render_template('result.html', 
                           filename=filename,
                           cropped_faces=cropped_faces,
                           restored_faces=restored_faces,
                           comparisons=comparisons)

if __name__ == '__main__':
    app.run(debug=True)
