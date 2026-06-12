from flask import Flask, request, jsonify
import re
import os
import PlayFab

app = Flask(__name__)

# Fungsi membaca list.txt (Database lokal)
def load_addons():
    addons = []
    if not os.path.exists('list.txt'):
        return addons
    
    # Regex untuk memisahkan Nama, Tipe, dan UUID dari list.txt
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

# 1. ANTARMUKA WEBSITE (HTML + JAVASCRIPT)
@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MCPE Addon Downloader</title>
        <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    </head>
    <body class="bg-gray-950 text-gray-100 min-h-screen font-sans">
        <div class="container mx-auto px-4 py-8 max-w-4xl">
            <header class="text-center mb-10">
                <h1 class="text-4xl font-black text-green-400 tracking-wide mb-2">🎮 MCPE ADDON DOWNLOADER</h1>
                <p class="text-gray-400">Cari addon & mod dari list.txt secara instan</p>
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
                <p class="text-gray-400 text-sm">Mencari di database lokal...</p>
            </div>

            <div id="results-container" class="grid gap-4">
                <p class="text-center text-gray-600 py-10">Masukkan kata kunci untuk memulai pencarian.</p>
            </div>
        </div>

        <script>
            async function performSearch() {
                const query = document.getElementById('search-input').value.trim();
                const container = document.getElementById('results-container');
                const loading = document.getElementById('loading');
                
                if(!query) {
                    container.innerHTML = '<p class="text-center text-yellow-500">Kolom pencarian tidak boleh kosong!</p>';
                    return;
                }

                loading.classList.remove('hidden');
                container.innerHTML = '';

                try {
                    const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
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
                                <h3 class="text-lg font-bold text-white">\${item.name}</h3>
                                <div class="flex flex-wrap gap-2 mt-2">
                                    <span class="px-2.5 py-0.5 text-xs font-bold rounded-md bg-green-950 text-green-400 border border-green-900/50">\${item.type}</span>
                                    <span class="text-xs text-gray-500 font-mono bg-gray-950 px-2 py-0.5 rounded border border-gray-800">\${item.uuid}</span>
                                </div>
                            </div>
                            <button onclick="downloadItem('\${item.uuid}', this)" class="w-full sm:w-auto px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-bold text-sm transition tracking-wide shadow-md">
                                Unduh Pack
                            </button>
                        `;
                        container.appendChild(card);
                    });
                } catch (error) {
                    loading.classList.add('hidden');
                    container.innerHTML = '<p class="text-center text-red-500">Gagal mengambil data dari server.</p>';
                }
            }

            async function downloadItem(uuid, button) {
                const originalText = button.innerText;
                button.innerText = "Memproses...";
                button.disabled = true;
                button.className = "w-full sm:w-auto px-5 py-2.5 bg-gray-800 text-gray-500 rounded-lg font-bold text-sm cursor-not-allowed";

                try {
                    const response = await fetch(`/api/download/\${uuid}`, { method: 'POST' });
                    const data = await response.json();

                    if (data.success && data.download_url) {
                        const a = document.createElement('a');
                        a.href = data.download_url;
                        document.body.appendChild(a);
                        a.click();
                        a.remove();
                        
                        button.innerText = "Sukses!";
                        button.className = "w-full sm:w-auto px-5 py-2.5 bg-green-600 text-white rounded-lg font-bold text-sm";
                    } else {
                        alert("Gagal memproses: " + (data.error || "Token PlayFab expired"));
                        resetButton();
                    }
                } catch (error) {
                    alert("Koneksi bermasalah.");
                    resetButton();
                }

                function resetButton() {
                    button.innerText = originalText;
                    button.disabled = false;
                    button.className = "w-full sm:w-auto px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-bold text-sm transition shadow-md";
                }
            }
        </script>
    </body>
    </html>
    '''

# 2. API PENCARIAN OFFLINE (Membaca langsung dari list.txt)
@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q', '').lower()
    addons = load_addons()
    results = [
        a for a in addons 
        if query in a['name'].lower() or query in a['uuid'].lower()
    ]
    return jsonify(results)

# 3. API RETRIEVE LINK PLAYFAB
@app.route('/api/download/<uuid_code>', methods=['POST'])
def download_addon(uuid_code):
    try:
        # Panggil fungsi pencarian internal PlayFab langsung dari file PlayFab.py Anda
        playfab_results = PlayFab.main([uuid_code])
        
        if not playfab_results or uuid_code not in playfab_results:
            return jsonify({"error": "Item tidak ditemukan di PlayFab"}), 404
            
        item_data = playfab_results[uuid_code]
        
        download_url = None
        if "Contents" in item_data and len(item_data["Contents"]) > 0:
            download_url = item_data["Contents"][0].get("Url")
            
        if not download_url:
            return jsonify({"error": "URL unduhan kosong"}), 404

        return jsonify({
            "success": True, 
            "download_url": download_url
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

app = app
