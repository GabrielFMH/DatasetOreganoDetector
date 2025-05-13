import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import quote_plus
import time

def download_images_from_unsplash(query, num_images, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Mejoramos la query para búsqueda
    search_query = query.replace("no", "").strip()  # Eliminamos "no" que podría causar problemas
    encoded_query = quote_plus(search_query)
    url = f"https://unsplash.com/s/photos/{encoded_query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://unsplash.com/"
    }

    try:
        print(f"Buscando imágenes para: {search_query}...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"No se encontraron resultados para '{search_query}'. Probando con términos alternativos...")
        # Intentamos con una búsqueda más simple
        return try_alternative_search(query, num_images, output_folder)
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    image_elements = soup.find_all('figure', {'itemprop': 'image'})

    if not image_elements:
        print("No se encontraron imágenes. Probando con términos alternativos...")
        return try_alternative_search(query, num_images, output_folder)

    count = 0
    downloaded_urls = set()

    for img in image_elements[:num_images*2]:  # Buscamos más porque algunos pueden fallar
        if count >= num_images:
            break
            
        try:
            img_tag = img.find('img')
            if not img_tag:
                continue
                
            src = img_tag.get('src')
            if not src or not src.startswith('https://'):
                src = img_tag.get('data-src') or img_tag.get('data-srcset')
                if src:
                    src = src.split('?')[0].split()[0]
            
            if src and src not in downloaded_urls:
                downloaded_urls.add(src)
                print(f"Descargando imagen {count + 1}...")
                
                # Obtener la imagen en alta resolución
                if 'ixid=' in src:
                    src = src.split('?')[0] + '?auto=format&fit=crop&w=1024&q=80'
                
                img_data = requests.get(src, headers=headers, timeout=10).content
                
                with open(os.path.join(output_folder, f"{search_query.replace(' ', '_')}_{count}.jpg"), "wb") as f:
                    f.write(img_data)
                
                count += 1
                time.sleep(1)  # Espera para no saturar el servidor
                
        except Exception as e:
            print(f"Error al descargar imagen: {e}")

    print(f"Descargadas {count} imágenes en {output_folder}")

def try_alternative_search(original_query, num_images, output_folder):
    alternatives = [
        "plants",  # Término más general en inglés
        "herbs",   # Hierbas en inglés
        "hojas",   # Hojas en español
        "plantas medicinales"  # Término alternativo
    ]
    
    for alt_query in alternatives:
        print(f"Intentando con: {alt_query}")
        download_images_from_unsplash(alt_query, num_images, output_folder)
        if len(os.listdir(output_folder)) >= num_images:
            break

# Ejemplo de uso con manejo de errores
try:
    download_images_from_unsplash("plantas no oregano", 10, "no_oregano/train")
    download_images_from_unsplash("plantas no oregano", 5, "no_oregano/test")
    download_images_from_unsplash("plantas no oregano", 5, "no_oregano/validation")
except Exception as e:
    print(f"Error en el proceso principal: {e}")