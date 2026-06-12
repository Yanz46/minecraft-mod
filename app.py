# ... (kode route /api/search dan /api/download tetap sama seperti sebelumnya) ...

# HAPUS ATAU UBAH bagian ini:
# if __name__ == '__main__':
#     app.run(debug=True)

# GANTI dengan ini agar dikenali Vercel sebagai WSGI app
app = app
di folder yang sama dengan main.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "keys.tsv")
    
    try:
        # Membaca file TSV (Tab-Separated Values)
        df = pd.read_csv(file_path, sep="\t")
        return df
    except Exception as e:
        print(f"Error membaca file: {e}")
        return None

@app.get("/")
def home():
    return {
        "message": "API Berhasil Berjalan!",
        "status": "Online",
        "docs": "/docs"
    }

# Endpoint 1: Mengambil semua data keys
@app.get("/keys")
def get_all_keys():
    df = load_data()
    if df is None:
        raise HTTPException(status_code=500, detail="Gagal memuat data dari file keys.tsv")
    
    # Mengubah isi tsv menjadi format JSON (List of Dictionary)
    return df.to_dict(orient="records")

# Endpoint 2: Mencari key berdasarkan MarketUUID
# Contoh: /keys/001ea2b9-3821-466c-b144-0edb9d07d42c
@app.get("/keys/{market_uuid}")
def get_key_by_market_uuid(market_uuid: str):
    df = load_data()
    if df is None:
        raise HTTPException(status_code=500, detail="Gagal memuat data")
    
    # Filter mencari yang MarketUUID-nya cocok
    result = df[df['MarketUUID'] == market_uuid]
    
    if result.empty:
        raise HTTPException(status_code=404, detail="MarketUUID tidak ditemukan")
    
    # Mengembalikan 1 data yang cocok dalam bentuk JSON object
    return result.to_dict(orient="records")[0]

# Endpoint 3: Memfilter berdasarkan TypePack (contoh: world_template)
# Contoh penggunaan: /keys/filter/type?type_pack=world_template
@app.get("/keys/filter/type")
def filter_by_type(type_pack: str):
    df = load_data()
    if df is None:
        raise HTTPException(status_code=500, detail="Gagal memuat data")
    
    # Filter berdasarkan TypePack (ignore huruf besar/kecil)
    result = df[df['TypePack'].str.lower() == type_pack.lower()]
    
    if result.empty:
        return {"message": f"Tidak ada data dengan TypePack: {type_pack}", "data": []}
        
    return result.to_dict(orient="records")
