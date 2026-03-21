import os

BASE_HTML = r"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}SilverCloud{% endblock %}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
        }

        .container {
            width: 100%;
            max-width: 100%;
            display: flex;
        }

        /* Sidebar: make full-height column so footer sits at bottom */
        .sidebar {
            width: 250px;
            background: #1a1a1a;
            color: white;
            padding: 20px;
            box-shadow: 2px 0 10px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }

        .sidebar-header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 15px;
        }

        .sidebar-header h1 {
            font-size: 20px;
            margin-bottom: 5px;
        }

        .sidebar-header p {
            font-size: 12px;
            color: #999;
        }

        /* Menu area should scroll if long */
        .sidebar-menu {
            list-style: none;
            flex: 1 1 auto;
            overflow: auto;
            padding-left: 12px;
            padding-right: 12px;
        }

        .sidebar-menu li {
            margin: 10px 0;
        }

        .sidebar-menu a {
            color: #ccc;
            text-decoration: none;
            display: block;
            padding: 10px 15px;
            border-radius: 5px;
            transition: all 0.3s;
        }

        .sidebar-menu a:hover {
            background: #667eea;
            color: white;
            padding-left: 20px;
        }

        .sidebar-menu a.active {
            background: #667eea;
            color: white;
            border-left: 3px solid #764ba2;
        }

        .sidebar-menu a.disabled {
            color: #666;
            opacity: 0.6;
            cursor: not-allowed;
            position: relative;
        }

        .sidebar-menu a.disabled:hover {
            background: transparent !important;
            color: #666 !important;
            padding-left: 15px !important;
        }

        .sidebar-menu a.disabled::after {
            content: "🔒";
            position: absolute;
            right: 10px;
            font-size: 12px;
        }

        .sidebar-menu a[title]:hover::before {
            content: attr(title);
            position: absolute;
            left: 100%;
            bottom: 50%;
            transform: translateY(50%);
            background: #333;
            color: white;
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 11px;
            white-space: nowrap;
            margin-left: 5px;
            z-index: 1000;
            pointer-events: none;
        }

        /* Sidebar Accordion Styles */
        .accordion-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 12px;
            margin-top: 15px;
            color: #bdc3c7;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: color 0.2s, background 0.2s;
            border-radius: 4px;
            user-select: none;
        }

        .accordion-header:hover {
            color: #fff;
            background: rgba(255, 255, 255, 0.05);
        }

        .accordion-icon {
            font-size: 10px;
            transition: transform 0.3s ease;
        }

        .accordion-header.active .accordion-icon {
            transform: rotate(180deg);
        }

        .accordion-content {
            display: none;
            overflow: hidden;
            margin: 0;
            padding: 0;
            list-style: none;
            padding-left: 10px;
        }

        .accordion-content.open {
            display: block;
        }

        .sidebar-footer {
            margin-top: auto;
            padding: 12px;
            background: transparent;
        }

        .sidebar-footer .user-info {
            margin-bottom: 8px;
        }

        .logout-btn {
            width: 100%;
            padding: 10px 12px;
            border-radius: 6px;
        }

        /* Topbar User Profile */
        .user-profile {
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            padding: 5px 10px;
            border-radius: 5px;
            transition: background 0.3s;
            position: relative;
        }

        .user-profile:hover {
            background: #f5f5f5;
        }

        .profile-dropdown {
            position: absolute;
            top: 100%;
            right: 0;
            background: white;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border-radius: 5px;
            min-width: 150px;
            display: none;
            z-index: 1000;
            padding: 8px 0;
        }

        .profile-dropdown.show {
            display: block;
        }

        .profile-dropdown form {
            margin: 0;
        }

        .profile-dropdown button {
            width: 100%;
            text-align: left;
            padding: 10px 15px;
            background: none;
            border: none;
            cursor: pointer;
            color: #333;
            transition: background 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .profile-dropdown button:hover {
            background: #f5f5f5;
            color: #e74c3c;
        }

        /* Main Content */
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
        }

        .topbar {
            background: white;
            padding: 15px 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .topbar-left {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 16px;
            font-weight: 500;
            color: #333;
        }

        .topbar-right {
            display: flex;
            align-items: center;
            gap: 20px;
        }

        .topbar-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            color: #555;
        }

        .topbar-item input[type="text"],
        .topbar-item select {
            padding: 6px 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background: white;
            color: #333;
            font-size: 14px;
        }

        .topbar-item input[readonly] {
            background: #f9f9f9;
            cursor: default;
        }

        .content {
            flex: 1;
            padding: 30px;
            overflow-y: auto;
        }

        /* Cards */
        .card {
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            padding: 20px;
            margin-bottom: 20px;
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #667eea;
            margin-bottom: 15px;
            padding-bottom: 10px;
        }

        .card-header h3 {
            color: #333;
            margin: 0;
            border: none;
            padding: 0;
        }
        
        /* Dashboard overrides for card h3 since dashboard has different style */
        .dashboard-content .card h3 {
             border-bottom: 2px solid #667eea;
             padding-bottom: 10px;
             margin-bottom: 15px;
        }

        /* Forms */
        .form-group {
            margin-bottom: 15px;
        }

        .form-group label {
            display: block;
            margin-bottom: 5px;
            color: #333;
            font-weight: 500;
        }

        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-family: inherit;
            font-size: 14px;
        }

        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 5px rgba(102, 126, 234, 0.3);
        }

        .form-group textarea {
            resize: vertical;
            min-height: 100px;
        }

        /* Buttons */
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s;
        }

        .btn-primary {
            background: #667eea;
            color: white;
        }

        .btn-primary:hover {
            background: #5568d3;
        }

        .btn-success {
            background: #27ae60;
            color: white;
        }

        .btn-success:hover {
            background: #229954;
        }

        .btn-danger {
            background: #e74c3c;
            color: white;
        }

        .btn-danger:hover {
            background: #c0392b;
        }

        .btn-secondary {
            background: #95a5a6;
            color: white;
        }

        .btn-secondary:hover {
            background: #7f8c8d;
        }

        /* Tables */
        .table-responsive {
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }

        table thead {
            background: #f5f5f5;
        }

        table th,
        table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }

        table th {
            font-weight: 600;
            color: #333;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        table tbody tr:hover {
            background: #f9f9f9;
        }

        /* Alert */
        .alert {
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }

        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        .alert-info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }

        .alert-close {
            cursor: pointer;
            font-size: 20px;
            color: inherit;
            opacity: 0.7;
        }

        .alert-close:hover {
            opacity: 1;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .container {
                flex-direction: column;
            }

            .sidebar {
                width: 100%;
                display: flex;
                justify-content: space-between;
                align-items: center;
                min-height: auto;
                position: relative;
            }

            .sidebar-menu {
                display: flex;
                gap: 10px;
            }

            .sidebar-footer {
                position: static;
                width: auto;
            }

            .topbar {
                flex-direction: column;
                gap: 15px;
            }

            .content {
                padding: 15px;
            }
        }

        {% block extra_style %}{% endblock %}
    </style>
</head>
<body>
    <div class="container">
        <!-- Sidebar -->
        <div class="sidebar">
            <div class="sidebar-header">
                <h1>🌐 SilverCloud</h1>
                <p>v2.0.0</p>
            </div>

            <!-- Menu Groups with Permission-Based Disabled State -->
            <ul class="sidebar-menu" id="menu">
                <!-- Dashboard -->
                <li id="menu-dashboard">
                    <a href="/dashboard" class="{% block nav_dashboard %}{% endblock %}" data-permission="Dashboard Ekranı Görüntüleme" title="Dashboard">📊 Dashboard</a>
                </li>

                <!-- Sistem Tabloları -->
                <li>
                    <div class="accordion-header {% block acc_sistem_tablolari %}{% endblock %}" id="acc-sistem-tablolari">
                        <span>SİSTEM TABLOLARI</span>
                        <span class="accordion-icon">▼</span>
                    </div>
                    <ul class="accordion-content {% block acc_sistem_tablolari_content %}{% endblock %}">
                        <li><a href="/subeler" class="{% block nav_subeler %}{% endblock %}" data-permission="Şube Yönetimi Ekranı Görüntüleme" title="Şube Yönetimi">🏢 Şube Yönetimi</a></li>
                        <li><a href="/api/v1/degerler" data-permission="Değer Yönetimi Ekranı Görüntüleme" title="Değer Yönetimi">💰 Değer Yönetimi</a></li>
                        <li><a href="/api/v1/kullanicilar" data-permission="Kullanıcı Yönetimi Ekranı Görüntüleme" title="Kullanıcı Yönetimi">👥 Kullanıcı Yönetimi</a></li>
                        <li><a href="/api/v1/roller" data-permission="Rol Yönetimi Ekranı Görüntüleme" title="Rol Yönetimi">⏱️ Rol Yönetimi</a></li>
                        <li><a href="/api/v1/yetkiler" data-permission="Yetki Yönetimi Ekranı Görüntüleme" title="Yetki Yönetimi">🔑 Yetki Yönetimi</a></li>
                        <li><a href="/api/v1/kullanici-rol-atamalari" data-permission="Kullanıcı Rol Atama Ekranı Görüntüleme" title="Kullanıcı Rol Atama">🛡️ Kullanıcı Rol Atama</a></li>
                        <li><a href="/api/v1/rol-yetki-atamalari" data-permission="Rol Yetki Atama Ekranı Görüntüleme" title="Rol Yetki Atama">🛡️ Rol Yetki Atama</a></li>
                        <li><a href="/api/v1/efatura-referans-yonetimi" data-permission="e-Fatura Referans Yönetimi Ekranı Görüntüleme" title="e-Fatura Referans Yönetimi">🧾 e-Fatura Referans Yönetimi</a></li>
                        <li><a href="/api/v1/odeme-referans-yonetimi" data-permission="Ödeme Referans Yönetimi Ekranı Görüntüleme" title="Ödeme Referans Yönetimi">🧾 Ödeme Referans Yönetimi</a></li>
                        <li><a href="/api/v1/cari-borc-yonetimi" data-permission="Cari Borç Yönetimi Ekranı Görüntüleme" title="Cari Borç Yönetimi">🧾 Cari Borç Yönetimi</a></li>
                    </ul>
                </li>

                <!-- Kategori Sistemi -->
                <li>
                    <div class="accordion-header" id="acc-kategori-sistemi">
                        <span>KATEGORİ SİSTEMİ</span>
                        <span class="accordion-icon">▼</span>
                    </div>
                    <ul class="accordion-content">
                        <li><a href="/api/v1/ust-kategoriler" data-permission="Üst Kategori Yönetimi Ekranı Görüntüleme" title="Üst Kategori Yönetimi">📁 Üst Kategori Yönetimi</a></li>
                        <li><a href="/api/v1/kategoriler" data-permission="Kategori Yönetimi Ekranı Görüntüleme" title="Kategori Yönetimi">📂 Kategori Yönetimi</a></li>
                    </ul>
                </li>

                <!-- Fatura/Harcama -->
                <li>
                    <div class="accordion-header" id="acc-fatura-harcama">
                        <span>FATURA/HARCAMA</span>
                        <span class="accordion-icon">▼</span>
                    </div>
                    <ul class="accordion-content">
                        <li><a href="/api/v1/efaturalar" data-permission="Fatura Yükleme Ekranı Görüntüleme" title="Fatura Yükleme">📄 Fatura Yükleme</a></li>
                        <li><a href="/api/v1/efaturalar" data-permission="Fatura Kategori Atama Ekranı Görüntüleme" title="Fatura Kategori Atama">🏷️ Fatura Kategori Atama</a></li>
                        <li><a href="/api/v1/efaturalar" data-permission="B2B Ekstre Yükleme Ekranı Görüntüleme" title="B2B Ekstre Yükleme">📋 B2B Ekstre Yükleme</a></li>
                        <li><a href="/api/v1/efaturalar" data-permission="B2B Kategori Atama Ekranı Görüntüleme" title="B2B Kategori Atama">🏷️ B2B Kategori Atama</a></li>
                        <li><a href="/api/v1/odemeler" data-permission="Ödeme Yükleme Ekranı Görüntüleme" title="Ödeme Yükleme">💳 Ödeme Yükleme</a></li>
                        <li><a href="/api/v1/odemeler" data-permission="Ödeme Kategori Atama Ekranı Görüntüleme" title="Ödeme Kategori Atama">🏷️ Ödeme Kategori Atama</a></li>
                        <li><a href="/api/v1/diger-harcamalar" data-permission="Diğer Harcamalar Ekranı Görüntüleme" title="Diğer Harcamalar">💰 Diğer Harcamalar</a></li>
                        <li><a href="/api/v1/pos-hareketleri" data-permission="POS Hareketleri Yükleme Ekranı Görüntüleme" title="POS Hareketleri Yükleme">📤 POS Hareketleri Yükleme</a></li>
                        <li><a href="/api/v1/pos-hareketleri" data-permission="Yemek Çeki Ekranı Görüntüleme" title="Yemek Çeki">🍴 Yemek Çeki</a></li>
                    </ul>
                </li>

                <!-- Gelir -->
                <li>
                    <div class="accordion-header" id="acc-gelir">
                        <span>GELİR</span>
                        <span class="accordion-icon">▼</span>
                    </div>
                    <ul class="accordion-content">
                        <li><a href="/api/v1/gelirler" data-permission="Gelir Girişi Ekranı Görüntüleme" title="Gelir Girişi">📈 Gelir Girişi</a></li>
                        <li><a href="/api/v1/nakit" data-permission="Nakit Girişi Ekranı Görüntüleme" title="Nakit Girişi">💵 Nakit Girişi</a></li>
                    </ul>
                </li>

                <!-- Stok -->
                <li>
                    <div class="accordion-header" id="acc-stok">
                        <span>STOK</span>
                        <span class="accordion-icon">▼</span>
                    </div>
                    <ul class="accordion-content">
                        <li><a href="/api/v1/stoklari" data-permission="Stok Tanımlama Ekranı Görüntüleme" title="Stok Tanımlama">📦 Stok Tanımlama</a></li>
                        <li><a href="/api/v1/stok-fiyatlari" data-permission="Stok Fiyat Tanımlama Ekranı Görüntüleme" title="Stok Fiyat Tanımlama">💲 Stok Fiyat Tanımlama</a></li>
                        <li><a href="/api/v1/stok-sayimlari" data-permission="Stok Sayım Ekranı Görüntüleme" title="Stok Sayım">📊 Stok Sayım</a></li>
                    </ul>
                </li>

                <!-- Çalışan -->
                <li>
                    <div class="accordion-header" id="acc-calisan">
                        <span>ÇALIŞAN</span>
                        <span class="accordion-icon">▼</span>
                    </div>
                    <ul class="accordion-content">
                        <li><a href="/api/v1/calisanlar" data-permission="Çalışan Yönetimi Ekranı Görüntüleme" title="Çalışan Yönetimi">👔 Çalışan Yönetimi</a></li>
                        <li><a href="/api/v1/puantaj-secimler" data-permission="Puantaj Seçim Yönetimi Ekranı Görüntüleme" title="Puantaj Seçim Yönetimi">⏰ Puantaj Seçim Yönetimi</a></li>
                        <li><a href="/api/v1/puantajlar" data-permission="Puantaj Girişi Ekranı Görüntüleme" title="Puantaj Girişi">📋 Puantaj Girişi</a></li>
                        <li><a href="/api/v1/avans-istekler" data-permission="Avans Talebi Ekranı Görüntüleme" title="Avans Talebi">💸 Avans Talebi</a></li>
                        <li><a href="/api/v1/calisan-talepler" data-permission="Çalışan Talep Ekranı Görüntüleme" title="Çalışan Talep">📝 Çalışan Talep</a></li>
                    </ul>
                </li>

                <!-- Rapor -->
                <li>
                    <div class="accordion-header" id="acc-rapor">
                        <span>RAPOR</span>
                        <span class="accordion-icon">▼</span>
                    </div>
                    <ul class="accordion-content">
                        <li><a href="/nakit-yatirma-raporu" data-permission="Nakit Yatırma Kontrol Raporu Görüntüleme" title="Nakit Yatırma Kontrol Raporu">💰 Nakit Yatırma Raporu</a></li>
                        <li><a href="/odeme-rapor" data-permission="Ödeme Rapor Görüntüleme" title="Ödeme Rapor">📊 Ödeme Rapor</a></li>
                        <li><a href="/fatura-rapor" data-permission="Fatura Rapor Görüntüleme" title="Fatura Rapor">📈 Fatura Rapor</a></li>
                        <li><a href="/fatura-diger-harcama-rapor" data-permission="Fatura & Diğer Harcama Rapor Görüntüleme" title="Fatura & Diğer Harcama Raporu">📑 Fatura & Diğer Harcama</a></li>
                        <li><a href="/pos-kontrol-dashboard" data-permission="POS Kontrol Dashboard Görüntüleme" title="POS Kontrol Dashboard">🎛️ POS Kontrol Dashboard</a></li>
                        <li><a href="/yemek-ceki-kontrol-dashboard" data-permission="Yemek Çeki Kontrol Dashboard Görüntüleme" title="Yemek Çeki Kontrol Dashboard">🍽️ Yemek Çeki Dashboard</a></li>
                        <li><a href="/vps-dashboard" data-permission="VPS Dashboard Görüntüleme" title="VPS Dashboard">🔍 VPS Dashboard</a></li>
                        <li><a href="/bayi-karlilik-raporu" data-permission="Bayi Karlılık Raporu Görüntüleme" title="Bayi Karlılık Raporu">💹 Bayi Karlılık Raporu</a></li>
                        <li><a href="/ozet-kontrol-raporu" data-permission="Özet Kontrol Raporu Görüntüleme" title="Özet Kontrol Raporu">✓ Özet Kontrol Raporu</a></li>
                        <li><a href="/nakit-akis-gelir-raporu" data-permission="Nakit Akış - Gelir Raporu Görüntüleme" title="Nakit Akış - Gelir">💧 Nakit Akış - Gelir</a></li>
                        <li><a href="/cari-borc-takip-sistemi" data-permission="Cari Borç Takip Sistemi Görüntüleme" title="Cari Borç Takip Sistemi">📌 Cari Borç Takip</a></li>
                    </ul>
                </li>
            </ul>
        </div>

        <!-- Main Content -->
        <div class="main-content">
            <div class="topbar">
                <div class="topbar-left">
                    Hoşgeldiniz, {{ user.Adi_Soyadi if user else 'Misafir' }}
                </div>
                <div class="topbar-right">
                    {% block topbar_right %}
                    {% endblock %}
                    <div class="user-profile" id="userProfileBtn">
                        <div style="font-size: 20px;">👤</div>
                        <div style="font-weight: 500;">{{ user.Kullanici_Adi if user else 'Misafir' }}</div>
                        <div style="font-size: 12px;">▼</div>
                        <div class="profile-dropdown" id="profileDropdown">
                            <form action="/logout" method="POST">
                                <button type="submit">🚪 Çıkış Yap</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
            <div class="content dashboard-content">
                {% block content %}{% endblock %}
            </div>
        </div>
    </div>

    <!-- Base Scripts for Sidebar Accordion & Permissions -->
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            // Profile Dropdown Toggle
            const userProfileBtn = document.getElementById('userProfileBtn');
            const profileDropdown = document.getElementById('profileDropdown');
            if (userProfileBtn && profileDropdown) {
                userProfileBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    profileDropdown.classList.toggle('show');
                });

                document.addEventListener('click', (e) => {
                    if (!userProfileBtn.contains(e.target)) {
                        profileDropdown.classList.remove('show');
                    }
                });
            }

            // Permission logic
            const branchSelect = document.getElementById('branch-select');
            const fetchPermissionsBase = () => {
                // Check if there is an active branch selection somewhere
                const branchId = branchSelect ? branchSelect.value : null;
                const url = branchId ? `/api/v1/permissions?sube_id=${branchId}` : `/api/v1/permissions`;
                
                fetch(url, { method: 'GET', credentials: 'include' })
                    .then(res => res.ok ? res.json() : { permissions: [] })
                    .catch(err => {
                        console.warn('Could not fetch user permissions:', err);
                        return { permissions: [] };
                    })
                    .then(data => {
                        const userPermissions = (data && data.permissions) ? data.permissions : [];
                        const menu = document.getElementById('menu');
                        if (menu) {
                            menu.querySelectorAll('a[data-permission]').forEach(link => {
                                const permName = link.getAttribute('data-permission');
                                const li = link.closest('li');
                                if (!userPermissions.includes(permName)) {
                                    if (li) li.style.display = 'none';
                                } else {
                                    if (li) li.style.display = '';
                                }
                            });

                            const accordions = menu.querySelectorAll('li:has(.accordion-header)');
                            accordions.forEach(accLi => {
                                const content = accLi.querySelector('.accordion-content');
                                if (content) {
                                    const visibleItems = Array.from(content.querySelectorAll('li')).filter(li => li.style.display !== 'none');
                                    if (visibleItems.length === 0) {
                                        accLi.style.display = 'none';
                                    } else {
                                        accLi.style.display = '';
                                    }
                                }
                            });
                        }
                    });
            };

            fetchPermissionsBase();
            if (branchSelect) {
                branchSelect.addEventListener('change', fetchPermissionsBase);
            }

            // Accordion Interaction Logic
            const accHeaders = document.querySelectorAll('.accordion-header');
            accHeaders.forEach(header => {
                header.addEventListener('click', () => {
                    const content = header.nextElementSibling;
                    const isCurrentlyOpen = content.classList.contains('open');

                    document.querySelectorAll('.accordion-content').forEach(c => {
                        c.classList.remove('open');
                    });
                    document.querySelectorAll('.accordion-header').forEach(h => {
                        h.classList.remove('active');
                    });

                    if (!isCurrentlyOpen) {
                        content.classList.add('open');
                        header.classList.add('active');
                    }
                });
            });
        });
    </script>
    {% block scripts %}{% endblock %}
</body>
</html>
"""

with open("c:/projects/SilverCloud/app/templates/base.html", "w", encoding="utf-8") as f:
    f.write(BASE_HTML)
