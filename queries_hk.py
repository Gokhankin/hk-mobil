# -*- coding: utf-8 -*-
import pandas as pd

def get_hk_status(conn) -> pd.DataFrame:
    """Oda bazlı temizlik durum dökümü (111 Satılabilir oda planına göre - Yüksek Performanslı CTE Sorgusu)."""
    df = pd.read_sql("""
        DECLARE @Today DATE = CAST(GETDATE() AS DATE);

        WITH ActiveRes AS (
            SELECT 
                r.RecId, r.Room, r.RoomNummer, r.FirstName1, r.LastName1, r.BedType, r.Remark, r.ResRemark, r.Status, r.CheckinDate, r.CheckOutDate, r.LateCOut,
                a.Name AS Acente,
                COALESCE(NULLIF(r.Room, ''), rm_ref.Room) AS MatchRoom,
                ROW_NUMBER() OVER (
                    PARTITION BY COALESCE(NULLIF(r.Room, ''), rm_ref.Room)
                    ORDER BY 
                        CASE 
                            WHEN r.Status = 2 AND CAST(r.CheckinDate AS DATE) <= @Today AND CAST(r.CheckOutDate AS DATE) >= @Today THEN 1
                            WHEN r.Status = 1 AND CAST(r.CheckinDate AS DATE) = @Today THEN 2
                            WHEN (r.Status = 2 OR r.Status = 3) AND CAST(r.CheckOutDate AS DATE) = @Today THEN 3
                            WHEN CAST(r.CheckinDate AS DATE) > @Today THEN 4
                            ELSE 5
                        END ASC,
                        r.CheckinDate ASC
                ) AS rn
            FROM Reservation r
            LEFT JOIN Room rm_ref ON r.RoomNummer = rm_ref.RecId
            LEFT JOIN Agency a ON r.AgencyId = a.RecId
            WHERE r.StatusCode IN (0,1,2,3) 
              AND r.[Status] IN (1,2,3)
              AND ISNULL(r.Voucher, '') NOT LIKE '%NOSHOW%'
              AND ISNULL(r.Voucher, '') NOT LIKE '%NO-SHOW%'
              AND ISNULL(r.ResRemark, '') NOT LIKE '%NOSHOW%'
              AND ISNULL(r.ResRemark, '') NOT LIKE '%NO-SHOW%'
              AND (
                  (CAST(r.CheckinDate AS DATE) <= @Today AND CAST(r.CheckOutDate AS DATE) >= @Today)
                  OR CAST(r.CheckinDate AS DATE) = @Today
                  OR CAST(r.CheckOutDate AS DATE) = @Today
              )
        ),
        TodayDD AS (
            SELECT Room, [Status], StatusRemark,
                   ROW_NUMBER() OVER (PARTITION BY Room ORDER BY RecId DESC) AS rn
            FROM DailyDetail
            WHERE CAST(StayDate AS DATE) = @Today
        )
        SELECT 
            rm.Room AS [ODA],
            rm.RoomTypeCode AS [TIP],
            rm.Remark AS [REMARK],
            rm.HkKontrol AS [AKSAM_SERVISI],
            ISNULL(res.FirstName1, '') + ' ' + ISNULL(res.LastName1, '') AS [MISAFIR_ADI],
            ISNULL(res.BedType, '') AS [YATAK_TIPI],
            ISNULL(res.Acente, '') AS [ACENTE],
            CASE WHEN res.CheckinDate IS NOT NULL THEN CONVERT(VARCHAR(10), res.CheckinDate, 104) ELSE '' END AS [CHECKIN_TARIHI],
            CASE WHEN res.CheckOutDate IS NOT NULL THEN CONVERT(VARCHAR(10), res.CheckOutDate, 104) ELSE '' END AS [CHECKOUT_TARIHI],
            CASE WHEN ISNULL(res.Remark, '') <> '' THEN res.Remark ELSE res.ResRemark END AS [REZ_NOTU],
            CASE WHEN res.Status = 2 AND CAST(res.CheckinDate AS DATE) <= @Today AND CAST(res.CheckOutDate AS DATE) >= @Today THEN 1 ELSE 0 END AS [DOLU_BOS],
            CASE WHEN res.Status = 1 AND CAST(res.CheckinDate AS DATE) = @Today THEN 1 ELSE 0 END AS [BUGUN_GELEN],
            CASE WHEN (res.Status = 2 OR res.Status = 3) AND CAST(res.CheckOutDate AS DATE) = @Today THEN 1 ELSE 0 END AS [BUGUN_GIDECEK],
            CASE WHEN (rm.DirtyClean = 1 OR rm.HkStatus = 1) AND res.RecId IS NULL THEN 1 ELSE 0 END AS [BOS_KIRLI],
            CASE 
                WHEN CAST(res.CheckOutDate AS DATE) = @Today AND res.Status = 3 THEN 'CO_YAPILDI'
                WHEN CAST(res.CheckOutDate AS DATE) = @Today AND res.Status = 2 THEN 'ODADA_HALA'
                ELSE ''
            END AS [CO_DURUM],
            ISNULL(res.LateCOut, '') AS [UZATMA_SAATI],
            dd.StatusRemark AS [STATUS_REMARK],
            CASE 
                WHEN dd.[Status] = 4 THEN 'ARIZALI (OOO)'
                WHEN dd.[Status] = 3 THEN 'BLOKELI'
                WHEN rm.DirtyClean = 1 THEN 'KIRLI'
                WHEN rm.DirtyClean = 0 THEN 'TEMIZ'
                WHEN rm.HkStatus = 1 THEN 'KIRLI'
                WHEN rm.HkStatus = 2 THEN 'TEMIZ'
                WHEN rm.HkStatus = 3 THEN 'OK'
                WHEN rm.HkStatus = 4 THEN 'ARIZALI (OOO)'
                WHEN rm.HkStatus = 5 THEN 'BLOKELI'
                ELSE 'KIRLI'
            END AS [DURUM],
            CASE 
                WHEN rm.HkStatus = 3 AND ISNULL(dd.[Status], 0) NOT IN (3, 4) THEN 'EVET'
                ELSE 'HAZIR_MI'
            END AS [HAZIR_MI]
        FROM Room rm
        LEFT JOIN ActiveRes res ON rm.Room = res.MatchRoom AND res.rn = 1
        LEFT JOIN TodayDD dd ON rm.Room = dd.Room AND dd.rn = 1
        WHERE rm.ForeCast = 1
        ORDER BY rm.Room
    """, conn)

    df = df.fillna('')
    # Robust normalization of status fields
    if 'DURUM' in df.columns:
        df['DURUM'] = df['DURUM'].astype(str).apply(
            lambda s: 'KIRLI' if 'K' in s.upper() and 'OK' not in s.upper() and 'ARIZALI' not in s.upper() and 'BLOK' not in s.upper()
            else ('TEMIZ' if 'TEM' in s.upper()
            else ('BLOKELI' if 'BLOK' in s.upper()
            else ('ARIZALI (OOO)' if 'ARIZ' in s.upper() or 'OOO' in s.upper()
            else ('OK' if 'OK' in s.upper() else s))))
        )
    return df

def get_hk_stats(conn) -> pd.DataFrame:
    """Genel HK istatistiği: Kirli/Temiz/OOO sayıları."""
    return pd.read_sql("""
        SELECT 
            CASE 
                WHEN HkStatus = 1 THEN 'KİRLİ'
                WHEN HkStatus = 2 THEN 'TEMİZ'
                WHEN HkStatus = 3 THEN 'HAZIR / OK'
                WHEN HkStatus = 4 THEN 'ARIZALI (OOO)'
                ELSE 'BİLİNMİYOR'
            END AS [DURUM],
            COUNT(*) AS [ADET]
        FROM Room
        GROUP BY HkStatus
    """, conn)

def get_maids(conn):
    """Sedna'daki temizlik gorevlilerini (Maid) getirir (MAID1 test kaydi filtrelenir)."""
    df = pd.read_sql("SELECT Code, Name FROM Maid WHERE Code NOT LIKE '%MAID%' AND Name NOT LIKE '%MAID%'", conn)
    maids = df.to_dict(orient='records')
    # HK kullanicisi varsayilan olarak eklenir
    maids.insert(0, {"Code": "HK", "Name": "HK"})
    return maids

def set_hk_status(conn, room: str, status: int, maid_code: str = None):
    """Odalarin temizlik durumlarini gunceller ve DailyDetail ile senkronize eder."""
    # Sedna standartları: DirtyClean (1 = Kirli, 0 = Temiz)
    dirty_clean = 1 if status in [1, 4, 5] else 0
    
    # HkStatus 0 = Normal. (2 değeri Sedna Front Office ekranında Kırmızı S/O (Second OK/Supervisor) uyarısı üretir)
    hk_status_val = status if status in [3, 4, 5] else 0
    
    # DD Status Mapping: 4=OOO, 3=Blocked, 0=Neutral
    dd_status = 0
    if status == 4: dd_status = 4
    if status == 5: dd_status = 3 
    
    cursor = conn.cursor()
    
    # 1. Room Tablosu Guncelleme
    if maid_code:
        cursor.execute("""
            UPDATE Room 
            SET HkStatus = ?, DirtyClean = ?, HkMaid = ?
            WHERE Room = ?
        """, (hk_status_val, dirty_clean, maid_code, room))
    else:
        cursor.execute("""
            UPDATE Room 
            SET HkStatus = ?, DirtyClean = ? 
            WHERE Room = ?
        """, (hk_status_val, dirty_clean, room))
    
    # 2. DailyDetail Senkronizasyonu
    cursor.execute("""
        SELECT TOP 1 RecId FROM DailyDetail 
        WHERE Room = ? AND CAST(StayDate AS DATE) = CAST(GETDATE() AS DATE)
    """, (room,))
    dd_row = cursor.fetchone()
    
    if dd_row:
        cursor.execute("""
            UPDATE DailyDetail
            SET [Status] = ?, UpdateDate = GETDATE()
            WHERE RecId = ?
        """, (dd_status, dd_row[0]))
    elif dd_status != 0:
        cursor.execute("""
            INSERT INTO DailyDetail (Room, StayDate, [Status], UpdateDate, RecordDate)
            VALUES (?, CAST(GETDATE() AS DATE), ?, GETDATE(), GETDATE())
        """, (room, dd_status))
    
    conn.commit()

def set_evening_status(conn, room: str, status: int, maid_code: str = None):
    """Odalarin aksam servisi (turndown) durumunu gunceller."""
    # status 1=Done, 0=Pending
    cursor = conn.cursor()
    cursor.execute("UPDATE Room SET HkKontrol = ? WHERE Room = ?", (status, room))
    conn.commit()

def get_guest_stats(conn):
    """
    Sedna veritabanindan Gelen Musteri, Gidecek Musteri ve Inhouse Musteri (Oda & Pax) istatistiklerini tek bir hizli sorguda alir.
    Fiziksel HK oda planindaki (ForeCast = 1) benzersiz oda sayilarini baz alir.
    """
    cursor = conn.cursor()
    
    no_show_clause = """
      AND ISNULL(r.Voucher, '') NOT LIKE '%NOSHOW%'
      AND ISNULL(r.Voucher, '') NOT LIKE '%NO-SHOW%'
      AND ISNULL(r.ResRemark, '') NOT LIKE '%NOSHOW%'
      AND ISNULL(r.ResRemark, '') NOT LIKE '%NO-SHOW%'
      AND ISNULL(r.FirstName1, '') NOT LIKE '%NOSHOW%'
      AND ISNULL(r.LastName1, '') NOT LIKE '%NOSHOW%'
    """

    join_clause = """
        INNER JOIN Room rm ON (
            (r.Room = rm.Room AND ISNULL(r.Room, '') <> '') 
            OR 
            ((r.Room IS NULL OR r.Room = '') AND r.RoomNummer = rm.RecId)
        )
    """

    cursor.execute(f"""
        SELECT 
            COUNT(DISTINCT CASE WHEN r.Status = 1 AND CAST(r.CheckinDate AS DATE) = CAST(GETDATE() AS DATE) THEN rm.Room END) AS Arr_Oda,
            ISNULL(SUM(CASE WHEN r.Status = 1 AND CAST(r.CheckinDate AS DATE) = CAST(GETDATE() AS DATE) THEN ISNULL(r.Pax, 0) + ISNULL(r.Childs, 0) ELSE 0 END), 0) AS Arr_Pax,
            COUNT(DISTINCT CASE WHEN (r.Status = 2 OR r.Status = 3) AND CAST(r.CheckOutDate AS DATE) = CAST(GETDATE() AS DATE) THEN rm.Room END) AS Dep_Oda,
            ISNULL(SUM(CASE WHEN (r.Status = 2 OR r.Status = 3) AND CAST(r.CheckOutDate AS DATE) = CAST(GETDATE() AS DATE) THEN ISNULL(r.Pax, 0) + ISNULL(r.Childs, 0) ELSE 0 END), 0) AS Dep_Pax,
            COUNT(DISTINCT CASE WHEN r.Status = 2 AND CAST(r.CheckinDate AS DATE) <= CAST(GETDATE() AS DATE) AND CAST(r.CheckOutDate AS DATE) >= CAST(GETDATE() AS DATE) THEN rm.Room END) AS Inh_Oda,
            ISNULL(SUM(CASE WHEN r.Status = 2 AND CAST(r.CheckinDate AS DATE) <= CAST(GETDATE() AS DATE) AND CAST(r.CheckOutDate AS DATE) >= CAST(GETDATE() AS DATE) THEN ISNULL(r.Pax, 0) + ISNULL(r.Childs, 0) ELSE 0 END), 0) AS Inh_Pax
        FROM Reservation r
        {join_clause}
        WHERE r.StatusCode IN (0, 1, 2, 3)
          AND rm.ForeCast = 1
          {no_show_clause}
    """)
    row = cursor.fetchone()

    arr_oda = int(row[0]) if row and row[0] else 0
    arr_pax = int(row[1]) if row and row[1] else 0
    dep_oda = int(row[2]) if row and row[2] else 0
    dep_pax = int(row[3]) if row and row[3] else 0
    inh_oda = int(row[4]) if row and row[4] else 0
    inh_pax = int(row[5]) if row and row[5] else 0

    return {
        "arrivals": {"oda": arr_oda, "pax": arr_pax},
        "departures": {"oda": dep_oda, "pax": dep_pax},
        "inhouse": {"oda": inh_oda, "pax": inh_pax}
    }


