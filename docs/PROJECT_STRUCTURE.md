# LogiFood — Proje Yapı Şeması ve Gariplikler

## 0. Görsel Özet (Mermaid)

```mermaid
flowchart TB
    subgraph config["config/"]
        settings["settings/"]
        urls["urls.py"]
    end

    subgraph core["apps.core"]
        direction TB
        models_c["TimeStampedModel"]
        cache_c["cache, utils, permissions"]
        cmds_c["load_sample_data, load_dev_data"]
    end

    subgraph src_domain["src/ (domain apps)"]
        direction LR
        users["users\nUser, SupplierProfile,\nSellerProfile, DriverProfile"]
        products["products\nCategory, Product"]
        orders["orders\nDeal, DealItem, Delivery,\nRequestToDriver, ..."]
    end

    users --> core
    products --> core
    products --> users
    orders --> core
    orders --> users
    orders --> products

    config --> core
    config --> src_domain
```

---

## 1. Dizin Yapısı (Üst Seviye)

```
LogiFood/
├── apps/
│   └── core/                    # Paylaşılan altyapı (base model, utils, cache, permissions, health)
├── src/
│   ├── users/                   # Kullanıcı, Supplier/Seller/Driver profilleri
│   ├── products/                # Category, Product
│   └── orders/                  # Deal, DealItem, Delivery, DeliveryItem, RequestToDriver
├── config/                      # Django proje config (settings, urls, wsgi)
├── tests/                       # test_core, test_users, test_products, test_orders, test_e2e
├── docker/
├── templates/
├── static/
├── logs/
├── manage.py
├── docker-compose.yml
└── requirements.txt
```

---

## 2. Katman Şeması (apps vs src)

```
                    ┌─────────────────────────────────────────┐
                    │              config/                     │
                    │  settings, urls, wsgi, asgi              │
                    └─────────────────┬───────────────────────┘
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         ▼                            ▼                            ▼
┌─────────────────┐    ┌──────────────────────────────────────────────┐
│   apps.core     │    │                   src/                        │
│                 │    │  users ──► products ──► orders                │
│ • TimeStamped   │◄───│    │           │           │                  │
│   Model         │    │    │           │           │  (domain apps      │
│ • BaseService   │    │    └───────────┴───────────┘   import core)    │
│ • cache,        │    └──────────────────────────────────────────────┘
│   permissions,  │
│   pagination,   │    Bağımlılık yönü: src.* → apps.core
│   utils,        │    Cross-domain: orders → users, products
│   exceptions    │
│ • load_sample_  │
│   data,         │
│   load_dev_data │
└─────────────────┘
```

---

## 3. Modül Detayı

### apps.core
| Dosya | Rol |
|-------|-----|
| models.py | TimeStampedModel (created_at, updated_at, created_by) |
| services.py | BaseService |
| cache.py | cache_get_or_set, cache_key, invalidate_model_cache |
| permissions.py | IsSupplier, IsSeller, IsDriver |
| pagination.py | StandardResultsSetPagination |
| exceptions.py | BusinessLogicError |
| utils.py | success_response, error_response |
| serializers.py | EmptySerializer vb. |
| urls.py | /api/health/ |
| views.py | (health fonksiyonu urls’te inline) |
| filters.py | Ortak filtreler |
| management/commands/ | load_sample_data, load_dev_data |

### src.users (app label: `users`, AUTH_USER_MODEL = 'users.User')
| Dosya | Rol |
|-------|-----|
| models.py | User, SupplierProfile, SellerProfile, DriverProfile |
| serializers.py | UserSerializer, *ProfileSerializer, Registration |
| services.py | UserService |
| views.py | Register, Login, Profile, ChangePassword, ToggleAvailability |
| urls.py | api/auth/register|login|profile|... |
| utils.py | JWT helpers vb. |
| admin.py | Profil admin’leri |

### src.products (app label: `products`)
| Dosya | Rol |
|-------|-----|
| models.py | Category, Product |
| serializers.py | CategorySerializer, ProductSerializer, ProductCreateSerializer |
| services.py | CategoryService, ProductService |
| views.py | CategoryViewSet, ProductListView/DetailView, SupplierProductViewSet |
| urls.py | api/products/categories, my-products, products/, products/<pk>/ |
| signals.py | Cache invalidation (invalidate_model_cache) |
| admin.py | CategoryAdmin, ProductAdmin |
| management/commands/ | load_categories |

### src.orders (app label: `orders`)
| Dosya | Rol |
|-------|-----|
| models.py | Deal, DealItem, RequestToDriver, Delivery, DeliveryItem |
| serializers.py | Deal*, Delivery*, RequestToDriver* |
| services.py | DealService, DeliveryService, RequestToDriverService, DiscoveryService |
| views.py | DealViewSet, DeliveryViewSet, RequestToDriverViewSet, SupplierListView, DriverListView, … |
| urls.py | api/orders/deals, driver-requests, deliveries, suppliers/, drivers/, available-deliveries/ |
| admin.py | Deal, DealItem, Delivery, DeliveryItem, RequestToDriver admin |

---

## 4. API URL Ağacı

```
/api/
├── auth/                    (src.users)
│   ├── register/
│   ├── login/
│   ├── logout/
│   ├── profile/
│   ├── profile/role/
│   ├── change-password/
│   └── toggle-availability/
├── products/                (src.products)
│   ├── categories/          (ViewSet)
│   ├── my-products/        (ViewSet, supplier’ın ürünleri)
│   ├── items/               (ürün listesi/detay; eskiden products/products)
│   └── items/<id>/
├── orders/                  (src.orders)
│   ├── deals/               (ViewSet)
│   ├── driver-requests/    (ViewSet)
│   ├── deliveries/          (ViewSet)
│   ├── suppliers/
│   ├── drivers/
│   ├── available-deliveries/
│   └── accept-delivery/<pk>/
├── health/                  (apps.core)
├── schema/                  (drf-spectacular)
├── docs/                    (Swagger)
└── redoc/                   (ReDoc)
```

---

## 5. Model Bağımlılıkları (Kabaca)

```
TimeStampedModel (apps.core)
    │
    ├── User (src.users) ─── SupplierProfile, SellerProfile, DriverProfile
    │
    ├── Category, Product (src.products)
    │       Product ──► SupplierProfile, Category
    │
    └── Deal, DealItem, RequestToDriver, Delivery, DeliveryItem (src.orders)
            Deal ──► SellerProfile, SupplierProfile, users.DriverProfile, delivery_count, delivery_handler
            DealItem ──► Deal, Product
            RequestToDriver ──► Deal, DriverProfile
            Delivery ──► Deal, DriverProfile (opsiyonel)
            DeliveryItem ──► Delivery, Product
```

---

## 6. Tespit Edilen Gariplikler / Tutarsızlıklar

### 6.1 İki kök paket: `apps` vs `src`
- **Durum:** Domain modülleri `src.*`, paylaşılan altyapı `apps.core`.
- **Gariplik:** Proje hem `apps` hem `src` kullanıyor; tek kök (ör. hepsi `src` veya hepsi `apps`) daha tutarlı olur.

### 6.2 Products URL’de isim tekrarı
- **Durum:** Ürün listesi/detay artık `api/products/items/`, `api/products/items/<id>/` (düzeltildi).

### 6.3 Management command’ların dağılımı
- **Durum:** `load_categories`, `load_sample_data`, `load_dev_data` hepsi apps.core’da (load_categories products’tan core’a taşındı).

### 6.4 Cache sadece products’ta
- **Durum:** `apps.core.cache` kullanımı: sadece `src.products` (services, views, signals).
- **Gariplik:** Orders/users tarafında cache yok. Bilinçli ise dokümante etmek, değilse orders için de (ör. discovery/supplier listesi) cache düşünülebilir.

### 6.5 Sadece products’ta signals
- **Durum:** `signals.py` yalnızca src.products’ta (cache invalidate).
- **Gariplik:** Orders’ta deal/delivery/request lifecycle için signal yok. Şu anki tasarımda büyük ihtimalle bilinçli; ileride domain event / audit log vb. eklenecekse orders için de signal veya event yapısı düşünülebilir.

### 6.6 Core’da “view” dağınık
- **Durum:** `apps.core.urls` içinde `health_check` fonksiyonu doğrudan tanımlı; ayrı bir `views.py` var ama health orada değil.
- **Gariplik:** Küçük de olsa tutarlılık için health view’ı `views.py`’e alınıp urls’te import edilebilir.

### 6.7 Orders’ta discovery URL’lerinin yeri
- **Durum:** `suppliers/`, `drivers/`, `available-deliveries/` src.orders altında.
- **Gariplik:** Bunlar kullanıcı “keşif” (discovery) endpoint’leri; konsept olarak users veya ayrı bir “discovery” modülüne de taşınabilir. Şu anki haliyle iş mantığı orders (deal/driver/delivery) ile sıkı bağlı olduğu için orders’ta kalmak da mantıklı; sadece ileride büyürse ayrıştırma düşünülebilir.

### 6.8 Test dizin isimlendirmesi
- **Durum:** `test_orders`, `test_products`, `test_users`, `test_core`, `test_e2e`.
- **Gariplik yok:** Modül adlarıyla uyumlu, anlaşılır.

### 6.9 Users’ta User için admin yok
- **Durum:** users admin’de yalnızca SupplierProfile, SellerProfile, DriverProfile var; User model’i için ayrı bir ModelAdmin yok.
- **Gariplik:** User, AUTH_USER_MODEL ve merkezî model; admin’de görünmemesi garip olabilir. En azından basit bir UserAdmin (veya User’ı bir profile admin’i üzerinden inline göstermek) eklenebilir.

---

## 7. Özet Tablo

| Konu | Mevcut | Öneri (opsiyonel) |
|------|--------|--------------------|
| Kök paket | apps + src | Tek kök (src) veya net “core vs domain” ayrımı dokümante et |
| Products URL | .../products/items/ (düzeltildi) | — |
| Management commands | categories@products, sample/dev@core | Hepsi core’da toplanabilir; load_dev_data zaten öyle kullanıyor |
| Cache | Sadece products | Orders’ta ihtiyaç varsa ekle; yoksa “sadece products” notunu yaz |
| Health view | urls’te inline | views.py’e taşı |
| User admin | Yok | Basit UserAdmin veya profile ile birlikte gösterim |

Bu şema ve gariplik listesi, proje yapısını ve geliştirme kararlarını hızlıca gözden geçirmek için kullanılabilir.
