# Apps vs Src — Araştırma Özeti

Tek kök seçerken **`apps/`** mu yoksa **`src/`** mu kullanılmalı, Django ve Python dünyasındaki kullanım araştırmasının özeti.

---

## 1. Django tarafında ne kullanılıyor?

### Stack Overflow (22841764 – “Best practice for Django project structure”)

- **En yüksek puanlı cevap (Zulan, 363+):**  
  Uygulamalar **`project_name/apps/`** altında. Örnek:
  ```
  ~/projects/project_name/
  ├── project_name/       # config (settings, urls, wsgi)
  │   └── apps/           # project-specific applications
  │       ├── accounts/
  │       └── ...
  ```
  “I used to put these apps into **project_name/apps/** directory.”

- **Two Scoops referanslı cevap (Rajat Singhal):**  
  Config ayrı `project/` (settings/, urls, wsgi), uygulamalar **root’ta** `app-1`, `app-2` vs.  
  Yani klasik örneklerde **`apps/`** veya root’ta app isimleri var; **`src/`** geçmiyor.

### django-project-skeleton (Mischback, çok referans alan şablon)

- Yapı: `[projectname]/[projectname]/` + **`apps/`** (içi boş veya `__init__.py`).
- Yani şablonda uygulama konteyneri olarak **`apps/`** kullanılıyor.

### Cookiecutter-Django

- **config/** ile Two Scoops tarzı ayrım kullanıyor; uygulamalar “Django root” altında, isimlendirme **`apps`** ile net tanımlanmıyor ama klasik Django projeleriyle uyumlu, **`src`** öne çıkmıyor.

### Özet (Django)

- Toplulukta ve şablonlarda **uygulama klasörü** için **`apps/`** daha yaygın.
- **`src/`** Django proje yapısı örneklerinde nadiren “tüm uygulamaların konteyneri” olarak geçiyor.

---

## 2. Python genelinde “src” ne anlama geliyor?

### “Src layout” (setuptools / PyPA)

- **Amaç:** Paketi `pip install -e .` ile kurduğunda testlerin ve kabukta çalışan kodun **yüklü paketi** değil, **kaynak ağacını** görmesi.
- **Yapı:** Tüm import edilen paket **`src/<pkgname>/`** altında olur.  
  Örnek: `src/mypkg/` — bu **dağıtılabilir kütüphane** için bir convention.
- **Kullanım alanı:** Pip ile yayınlanan **kütüphaneler** (wheel, PyPI). Django **monolith** uygulaması için zorunlu değil.

### Sonuç (Python)

- **`src/`** = “kaynak kodun tek yeri” anlamında daha çok **paket** projelerinde kullanılıyor.
- Django “tek proje, birçok app” yapısında Python’un bu “src layout” geleneği doğrudan karşılık bulmuyor.

---

## 3. Pros & Cons

### A) Tek kök `src/` — apps.core → src.core

| Pros | Cons |
|------|------|
| Tek kök: tüm “kaynak” `src/` altında, config dışında her şey bir yerde | Django topluluğunda **`src`** ile app toplama az görülüyor |
| `src` = “kaynak kod” — genel yazılım dilinde tanıdık | Yeni gelen Django geliştiricisi `src.*` yerine `app_name.*` bekleyebilir |
| Sadece **core** taşınır (users/products/orders zaten src’te); refactor hacmi küçük | “App” kavramıyla isim uyuşmaz: `src.users` “app” mi “module” mı belirsiz |
| Python “src layout” ile terminoloji uyumlu (paket projelerinde) | Django docs / startapp / INSTALLED_APPS örnekleri hep `appname`; `src.appname` örnekleri az |

---

### B) Tek kök `apps/` — src.users/products/orders → apps.*

| Pros | Cons |
|------|------|
| Django dünyasında **en yaygın** pattern: “apps/ altında app’ler” | **3 domain app** taşınır; import, migration, test, url değişikliği fazla |
| “App” = Django’daki kavramla birebir örtüşür: `apps.users` okununca “users app” anlaşılır | AUTH_USER_MODEL = `'users.User'` kalır; app label `users` olunca isim çakışması yok ama dizin adı `apps/users/` olur |
| SO, django-project-skeleton, Two Scoops tarzı örneklerle uyumlu | Mevcut `src.*` import’ları (tests, serializers, views, services, load_sample_data vb.) hepsi güncellenmeli |
| Yeni işe giren biri “app nerede?” derse “apps/ altında” cevabı toplulukla aynı | Migration dosyaları `dependencies`/app label olarak `users`, `products`, `orders` kalmaya devam eder; sadece package path `apps.users` olur |

---

### Kısa özet

| Kritere göre | A (src) | B (apps) |
|--------------|---------|----------|
| Refactor riski / hacmi | Düşük (sadece core) | Yüksek (3 app + tüm import’lar) |
| Django convention | Zayıf | Güçlü |
| Anlam netliği (“app” vs “source”) | “Source” net | “App” net |
| Örnek bulma / dokümana uyum | Az | Çok |

**Pratik sonuç:**  
- **Hızlı ve az risk:** A (sadece core’u `src.core` yap).  
- **Uzun vadede toplulukla uyum:** B (hepsini `apps.*` yap; refactor daha büyük ama bir kere yapılır).

---

## 4. Karşılaştırma (özet tablo)

| Konu | `apps/` (tek kök) | `src/` (tek kök) |
|------|-------------------|-------------------|
| Django SO / şablonlar | ✅ Sık (apps/ içinde app’ler) | ❌ Nadir |
| Two Scoops / config ayrımı | ✅ Uyumlu (config + apps) | ⚠️ Uyumlu ama Django’da az örnek |
| Python “src layout” | Kütüphane konusu değil | ✅ Paket projelerinde standart |
| Anlam | “Uygulamalar burada” | “Kaynak kod burada” |
| LogiFood’da şu an | Sadece `apps.core` | `src.users`, `src.products`, `src.orders` |

---

## 5. Öneri (best practice açısından)

- **Sadece Django topluluğuna ve mevcut repolara bakarsan:**  
  **Tek kök olarak `apps/`** seçmek daha tutarlı: domain app’leri de **`apps.users`**, **`apps.products`**, **`apps.orders`** yapıp core ile aynı çatı altında toplamak, SO + django-project-skeleton + birçok “best practice” örneğiyle uyumlu.

- **`src/`** seçmek:
  - Django tarafında daha az referans var.
  - Anlam olarak “tüm kaynak” (config hariç) için uygun; Django’da config’i `config/` yapınca `src/` = “business logic + app’ler” demek mantıklı olur ama yaygın örnek az.

- **Net cevap:**  
  **Django dünyasında “hangi kök daha iyi?” sorusunun yaygın cevabı `apps/`.**  
  Stack Overflow, django-project-skeleton ve benzeri kaynaklar **`apps/`** kullanımını işaret ediyor. **`src/`** daha çok genel Python/paket projelerinde “kaynak kodu buraya topla” convention’ı.

---

## 6. LogiFood’a uyarlama

- **B seçeneği (tek kök `apps/`):**  
  `src.users` → `apps.users`, `src.products` → `apps.products`, `src.orders` → `apps.orders`  
  → Django best practice ile en uyumlu seçenek.

- **A seçeneği (tek kök `src/`):**  
  `apps.core` → `src.core`  
  → Tutarlı bir tek kök sağlar ama Django örneklerinde **`src`** daha az görülüyor.

**Özet:** Best practice ve diğer repolar/Stack Overflow tarafı **`apps/`** (B seçeneği) lehine; ileride refactor yapılacaksa **B** toplulukla daha uyumlu olur.
