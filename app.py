from flask import Flask, request, jsonify
import re
import os
import PlayFab  # Memanggil file PlayFab.py Anda

app = Flask(__name__)

# Fungsi untuk membaca dan memparse list.txt
def load_addons():
    addons = []
    if not os.path.exists('list.txt'):
        return addons
    
    # Regex untuk memisahkan Nama, Tipe, dan UUID
    pattern = re.compile(r"^(.*?)\s*-\s*([a-zA-Z]+)\s+([0-9a-fA-F-]{36})")
    
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

# Route Utama: Langsung mengembalikan tampilan HTML Website
@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Minecraft Addon Downloader</title>
        <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    </head>
    <body class="bg-gray-900 text-gray-100 min-h-screen font-sans">

        <div class="container mx-auto px-4 py-8 max-w-4xl">
            <header class="text-center mb-10">
                <h1 class="text-4xl font-bold text-green-400 mb-2">📦 MCPE Addon Downloader</h1>
                <p class="text-gray-400">Cari addon dari list.txt dan dapatkan akses download via PlayFab</p>
            </header>

            <div class="mb-8">
                <div class="flex gap-2">
                    <input type="text" id="search-input" placeholder="Masukkan nama addon atau UUID..." 
                           class="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-green-500 text-white">
                    <button onclick="performSearch()" class="px-6 py-3 bg-green-600 hover:bg-green-500 rounded-lg font-semibold transition">
                        Cari
                    </button>
                </div>
            </div>

            <div id="loading" class="hidden text-center py-4 text-gray-400">
                Mencari addon...
            </div>

            <div id="results-container" class="grid gap-4">
                <p class="text-center text-gray-500">Silakan cari nama addon untuk memulai.</p>
            </div>
        </div>

        <script>
            async function performSearch() {
                const query = document.getElementById('search-input').value;
                const container = document.getElementById('results-container');
                const loading = document.getElementById('loading');
                
                loading.classList.remove('hidden');
                container.innerHTML = '';

                try {
                    const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                    const data = await response.json();
                    
                    loading.classList.add('hidden');
                    
                    if (data.length === 0) {
                        container.innerHTML = '<p class="text-center text-red-400">Tidak ada addon yang cocok ditemukan.</p>';
                        return;
                    }

                    data.forEach(item => {
                        const card = document.createElement('div');
                        card.className = "bg-gray-800 p-5 rounded-lg border border-gray-700 flex justify-between items-center hover:border-gray-600 transition";
                        card.innerHTML = `
                            <div>
                                <h3 class="text-lg font-bold text-white">\${item.name}</h3>
                                <div class="flex gap-2 mt-1">
                                    <span class="px-2 py-0.5 text-xs font-semibold rounded bg-blue-900 text-blue-200">\${item.type}</span>
                                    <span class="text-xs text-gray-400 font-mono">\${item.uuid}</span>
                                </div>
                            </div>
                            <button onclick="downloadItem('\${item.uuid}', this)" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded font-medium text-sm transition">
                                Unduh
                            </button>
                        `;
                        container.appendChild(card);
                    });

                } catch (error) {
                    loading.classList.add('hidden');
                    container.innerHTML = '<p class="text-center text-red-500">Terjadi kesalahan saat memuat data.</p>';
                }
            }

            async function downloadItem(uuid, button) {
                const originalText = button.innerText;
                button.innerText = "Processing...";
                button.disabled = true;
                button.className = "px-4 py-2 bg-gray-600 text-gray-400 rounded text-sm cursor-not-allowed";

                try {
                    const response = await fetch(`/api/download/\${uuid}`, { method: 'POST' });
                    const data = await response.json();

                    if (data.success && data.download_url) {
                        const a = document.createElement('a');
                        a.href = data.download_url;
                        document.body.appendChild(a);
                        a.click();
                        a.remove();
                        
                        button.innerText = "Berhasil!";
                        button.className = "px-4 py-2 bg-green-600 text-white rounded text-sm";
                    } else {
                        alert("Gagal: " + (data.error || "URL download tidak ditemukan"));
                        resetButton();
                    }
                } catch (error) {
                    alert("Terjadi kesalahan jaringan.");
                    resetButton();
                }

                function resetButton() {
                    button.innerText = originalText;
                    button.disabled = false;
                    button.className = "px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded font-medium text-sm transition";
                }
            }

            document.getElementById('search-input').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') performSearch();
            });
        </script>
    </body>
    </html>
    '''

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q', '').lower()
    addons = load_addons()
    results = [
        a for a in addons 
        if query in a['name'].lower() or query in a['uuid'].lower()
    ]
    return jsonify(results)

@app.route('/api/download/<uuid_code>', methods=['POST'])
def download_addon(uuid_code):
    try:
        # Menjalankan fungsi login & search milik PlayFab.py Anda
        playfab_results = PlayFab.main(uuid_code)
        
        if not playfab_results or uuid_code not in playfab_results:
            return jsonify({"error": "Item tidak ditemukan di PlayFab"}), 404
            
        item_data = playfab_results[uuid_code]
        
        # Mengambil URL unduhan dari isi data PlayFab
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

# Expose aplikasi untuk Vercel Serverless
app = app
