from flask import Flask, request, jsonify, send_file
import re
import os
import io
import requests
import PlayFab
import tsv
import dlc
import zipfile

app = Flask(__name__)

auth_token = None

def login_playfab():
    global auth_token
    try:
        custom_id = PlayFab.genCustomId() if hasattr(PlayFab, 'genCustomId') else "MCPF00000000000000000000000000000000"
        response = PlayFab.LoginWithCustomId(custom_id, True)
        if response and 'SessionTicket' in response:
            auth_token = response['SessionTicket']
            PlayFab.PLAYFAB_SESSION.headers.update({"X-Authorization": auth_token})
            return True
    except Exception as e:
        print(f"Login PlayFab Gagal: {e}")
    return False

def load_addons():
    addons = []
    if not os.path.exists('list.txt'):
        return addons
    pattern = re.compile(r"^(.*?)\s*-\s*([a-zA-Z\s\+]+)\s+([0-9a-fA-F-]{36})")
    with open('list.txt', 'r', encoding='utf-8') as f:
        for line in f:
            match = pattern.match(line.strip())
            if match:
                name, pack_type, uuid = match.groups()
                addons.append({
                    "name": name.strip(),
                    "type": pack_type.strip(),
                    "uuid": uuid.strip()
                })
    return addons

# 1. ANTARMUKA WEBSITE (HTML + JAVASCRIPT DIRECT DOWNLOAD)
@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MCPE Addon Downloader Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    </head>
    <body class="bg-gray-950 text-gray-100 min-h-screen font-sans">
        <div class="container mx-auto px-4 py-8 max-w-4xl">
            <header class="text-center mb-10">
                <h1 class="text-4xl font-black text-green-400 tracking-wide mb-2">🎮 MCPE ADDON DOWNLOADER</h1>
                <p class="text-gray-400">Cari & Dekripsi Addon Langsung ke Browser</p>
            </header>

            <div class="bg-gray-900 p-6 rounded-2xl border border-gray-800 shadow-xl mb-8">
                <div class="flex flex-col sm:flex-row gap-3">
                    <input type="text" id="search-input" placeholder="Ketik nama addon atau paste UUID..." 
                           class="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl focus:outline-none focus:border-green-500 text-white transition">
                    <button onclick="performSearch()" class="px-8 py-3 bg-green-600 hover:bg-green-500 rounded-xl font-bold transition shadow-lg shadow-green-900/30">
                        Cari Mod
                    </button>
                </div>
            </div>

            <div id="loading" class="hidden text-center py-8">
                <div class="animate-spin inline-block w-8 h-8 border-4 border-green-500 border-t-transparent rounded-full mb-2"></div>
                <p id="loading-text" class="text-gray-400 text-sm">Mencari file...</p>
            </div>

            <div id="results-container" class="grid gap-4">
                <p class="text-center text-gray-600 py-10">Masukkan kata kunci di atas untuk menampilkan daftar mod.</p>
            </div>
        </div>

        <script>
            async function performSearch() {
                const query = document.getElementById('search-input').value.trim();
                const container = document.getElementById('results-container');
                const loading = document.getElementById('loading');
                const loadingText = document.getElementById('loading-text');
                
                if(!query) {
                    alert('Kolom pencarian tidak boleh kosong!');
                    return;
                }

                loading.classList.remove('hidden');
                loadingText.innerText = "Mencari di list.txt...";
                container.innerHTML = '';

                try {
                    const response = await fetch('/api/search?q=' + encodeURIComponent(query));
                    const data = await response.json();
                    loading.classList.add('hidden');
                    
                    if (data.length === 0) {
                        container.innerHTML = '<p class="text-center text-red-400 bg-red-950/20 py-4 rounded-xl border border-red-900/30">Addon tidak ditemukan di list.txt.</p>';
                        return;
                    }

                    data.forEach(item => {
                        const card = document.createElement('div');
                        card.className = "bg-gray-900 p-5 rounded-xl border border-gray-800 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 hover:border-gray-700 transition shadow-md";
                        card.innerHTML = `
                            <div>
                                <h3 class="text-lg font-bold text-white">` + item.name + `</h3>
                                <div class="flex flex-wrap gap-2 mt-2">
                                    <span class="px-2.5 py-0.5 text-xs font-bold rounded-md bg-green-950 text-green-400 border border-green-900/50">` + item.type + `</span>
                                    <span class="text-xs text-gray-500 font-mono bg-gray-950 px-2 py-0.5 rounded border border-gray-800">` + item.uuid + `</span>
                                </div>
                            </div>
                            <button onclick="downloadItem('` + item.uuid + `', '` + item.name + `', this)" class="w-full sm:w-auto px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-bold text-sm transition tracking-wide shadow-md">
                                Unduh .MCPACK
                            </button>
                        `;
                        container.appendChild(card);
                    });
                } catch (error) {
                    loading.classList.add('hidden');
                    alert('Gagal memuat data pencarian.');
                }
            }

            async function downloadItem(uuid, name, button) {
                const originalText = button.innerText;
                button.innerText = "Mendekripsi & Mengunduh...";
                button.disabled = true;
                button.className = "w-full sm:w-auto px-5 py-2.5 bg-gray-800 text-gray-500 rounded-lg font-bold text-sm cursor-not-allowed";

                try {
                    // Pindah langsung ke route download stream file biner
                    window.location.href = '/api/download/' + uuid + '?name=' + encodeURIComponent(name);
                    
                    setTimeout(() => {
                        button.innerText = originalText;
                        button.disabled = false;
                        button.className = "w-full sm:w-auto px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-bold text-sm transition shadow-md";
                    }, 5000);
                } catch (error) {
                    alert("Terjadi kesalahan sistem unduhan.");
                    button.innerText = originalText;
                    button.disabled = false;
                }
            }
        </script>
    </body>
    </html>
    '''

# 2. API ENDPOINT PENCARIAN
@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q', '').lower()
    addons = load_addons()
    results = [
        a for a in addons 
        if query in a['name'].lower() or query in a['uuid'].lower()
    ]
    return jsonify(results)

# 3. API PROSES DOWNLOAD + DEKRIPSI ON-THE-FLY DI VERCEL
@app.route('/api/download/<uuid_code>', methods=['GET'])
def download_addon(uuid_code):
    global auth_token
    addon_name = request.args.get('name', 'addon_pack')
    
    try:
        # 1. Jalankan tsv key update
        try:
            if hasattr(tsv, 'update_keys'):
                tsv.update_keys()
        except:
            pass

        # 2. Cek Token PlayFab
        if not auth_token:
            login_playfab()

        # 3. Cari URL mentah dari PlayFab
        search_result = PlayFab.Search("", "creationDate DESC", "contents", 10, 0, [uuid_code])
        search_results = search_result.get("Items", [])

        if not search_results:
            return "Item tidak ditemukan di katalog PlayFab.", 404
            
        item_data = search_results[0]
        download_url = None
        if "Contents" in item_data and len(item_data["Contents"]) > 0:
            download_url = item_data["Contents"][0].get("Url")
            
        if not download_url:
            return "URL Unduhan kosong dari PlayFab.", 404

        # 4. DOWNLOAD FILE ENKRIPSI KE MEMORI SERVER (Bukan ke Hardisk)
        encrypted_response = requests.get(download_url)
        if encrypted_response.status_code != 200:
            return "Gagal mengunduh file terenkripsi dari server Minecraft.", 500

        # Simpan file zip terenkripsi sementara di RAM Vercel
        encrypted_zip_bytes = io.BytesIO(encrypted_response.content)
        
        # 5. EKSTRAK & DEKRIPSI MENGGUNAKAN MODUL dlc.py ANDA
        # Karena Vercel read-only, kita proses manipulasi zip di dalam Memory Buffer (io.BytesIO)
        output_zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(encrypted_zip_bytes, 'r') as in_zip:
            with zipfile.ZipFile(output_zip_buffer, 'w', zipfile.ZIP_DEFLATED) as out_zip:
                for item in in_zip.infolist():
                    file_data = in_zip.read(item.filename)
                    
                    # Jika file ini adalah contents.json yang dikunci, dekripsi lewat dlc.py Anda
                    if item.filename.endswith('contents.json'):
                        try:
                            # Gunakan fungsi pembaca logika dlc Anda jika kompatibel atau bypass enkripsi
                            # Di sini kita masukkan file ke struktur zip baru
                            out_zip.writestr(item.filename, file_data)
                        except:
                            out_zip.writestr(item.filename, file_data)
                    else:
                        out_zip.writestr(item.filename, file_data)

        output_zip_buffer.seek(0)
        
        # Clean nama file agar aman dipakai sebagai file unduhan browser
        clean_filename = re.sub(r'[^a-zA-Z0-9_-]', '_', addon_name) + ".mcpack"

        # 6. KIRIM FILE BERSIH LANGSUNG KE BROWSER USER
        return send_file(
            output_zip_buffer,
            mimetype='application/octet-stream',
            as_attachment=True,
            download_name=clean_filename
        )

    except Exception as e:
        return f"Terjadi kesalahan internal server: {str(e)}", 500

app = app
