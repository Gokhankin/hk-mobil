# -*- coding: utf-8 -*-
import pandas as pd

def get_hk_status(conn) -> pd.DataFrame:
    """Oda bazlı temizlik durum dökümü (111 Satılabilir oda planına göre - Yüksek Performanslı CTE Sorgusu)."""
    df = pd.read_sql("""
        DECLARE @Today DATE = CAST(GETDATE() AS DATE);

        WITH MorningSnapshot AS (
            SELECT Room, DirtyClean, HkStatus, GuestName, AgencyName, CheckinDate, CheckOutDate, Fostatus, Pax, 
                   (ISNULL(Child1, 0) + ISNULL(Child2, 0) + ISNULL(Child3, 0) + ISNULL(Child4, 0)) AS Childs,
                   ROW_NUMBER() OVER (PARTITION BY Room ORDER BY RecId ASC) AS rn
            FROM HkHistory
            WHERE CAST(HotelDate AS DATE) = @Today
        ),
        ActiveRes AS (
            SELECT 
                r.RecId, r.Room, r.RoomNummer, r.FirstName1, r.LastName1, r.BedType, r.Remark, r.ResRemark, r.Status, r.CheckinDate, r.CheckOutDate, r.LateCOut,
                r.Pax, r.Childs,
                a.Name AS Acente,
                COALESCE(
                    NULLIF(r.Room, ''), 
                    rm_ref.Room,
                    CASE 
                        WHEN r.Remark LIKE '1[0-9][0-9] %' OR r.Remark LIKE '2[0-9][0-9] %' OR r.Remark LIKE '3[0-9][0-9] %' OR r.Remark LIKE '4[0-9][0-9] %' OR r.Remark LIKE '7[0-9][0-9] %'
                        THEN SUBSTRING(r.Remark, 1, 3)
                        ELSE NULL
                    END
                ) AS MatchRoom,
                ROW_NUMBER() OVER (
                    PARTITION BY COALESCE(
                        NULLIF(r.Room, ''), 
                        rm_ref.Room,
                        CASE 
                            WHEN r.Remark LIKE '1[0-9][0-9] %' OR r.Remark LIKE '2[0-9][0-9] %' OR r.Remark LIKE '3[0-9][0-9] %' OR r.Remark LIKE '4[0-9][0-9] %' OR r.Remark LIKE '7[0-9][0-9] %'
                            THEN SUBSTRING(r.Remark, 1, 3)
                            ELSE NULL
                        END
                    )
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
        TodayArr AS (
            SELECT DISTINCT COALESCE(NULLIF(r.Room, ''), rm_ref.Room) AS Room, 1 AS HasArrival
            FROM Reservation r
            LEFT JOIN Room rm_ref ON r.RoomNummer = rm_ref.RecId
            WHERE r.StatusCode IN (0,1,2,3) AND r.Status = 1 AND CAST(r.CheckinDate AS DATE) = @Today
              AND ISNULL(r.Voucher, '') NOT LIKE '%NOSHOW%' AND ISNULL(r.ResRemark, '') NOT LIKE '%NOSHOW%'
        ),
        TodayDep AS (
            SELECT DISTINCT COALESCE(NULLIF(r.Room, ''), rm_ref.Room) AS Room, 
                   MAX(CASE WHEN r.Status = 2 THEN 1 ELSE 0 END) AS OdadaHala,
                   MAX(CASE WHEN r.Status = 3 THEN 1 ELSE 0 END) AS CikisYapildi
            FROM Reservation r
            LEFT JOIN Room rm_ref ON r.RoomNummer = rm_ref.RecId
            WHERE r.StatusCode IN (0,1,2,3) AND r.Status IN (2,3) AND CAST(r.CheckOutDate AS DATE) = @Today
              AND ISNULL(r.Voucher, '') NOT LIKE '%NOSHOW%' AND ISNULL(r.ResRemark, '') NOT LIKE '%NOSHOW%'
            GROUP BY COALESCE(NULLIF(r.Room, ''), rm_ref.Room)
        ),
        TodayDD AS (
            SELECT Room, [Status], StatusRemark,
                   ROW_NUMBER() OVER (PARTITION BY Room ORDER BY RecId DESC) AS rn
            FROM DailyDetail
            WHERE CAST(StayDate AS DATE) = @Today
        ),
        TodayRC AS (
            SELECT DISTINCT Room
            FROM (
                -- 1. LOG tablosu üzerinden gerçekleşen Oda Değişiklikleri
                SELECT l.Old AS Room FROM LOG l
                INNER JOIN Reservation r ON l.ResId = r.RecId
                WHERE l.FieldName = 'Room' AND l.Old != l.New
                  AND l.Old NOT IN ('Basic Blocking', 'Cancel Blocking', '')
                  AND l.New NOT IN ('Basic Blocking', 'Cancel Blocking', '')
                  AND CAST(l.ADateTime AS DATE) = @Today AND CAST(r.CheckOutDate AS DATE) = @Today
                UNION
                SELECT l.New AS Room FROM LOG l
                INNER JOIN Reservation r ON l.ResId = r.RecId
                WHERE l.FieldName = 'Room' AND l.Old != l.New
                  AND l.Old NOT IN ('Basic Blocking', 'Cancel Blocking', '')
                  AND l.New NOT IN ('Basic Blocking', 'Cancel Blocking', '')
                  AND CAST(l.ADateTime AS DATE) = @Today AND CAST(r.CheckOutDate AS DATE) = @Today
                UNION
                -- 2. Sedna Resmi RC Plan Tablosu (Sadece hedef güne ait planlar)
                SELECT OldRoom AS Room FROM RoomChangePlan WHERE CAST(RCDate AS DATE) = @Today AND ISNULL(Deleted, 0) = 0
                UNION
                SELECT NewRoom AS Room FROM RoomChangePlan WHERE CAST(RCDate AS DATE) = @Today AND ISNULL(Deleted, 0) = 0
                UNION
                -- 3. DailyDetail üzerinden fiili Room Change
                SELECT dd_old.Room AS Room
                FROM DailyDetail dd_new
                JOIN DailyDetail dd_old ON dd_new.ReservationId = dd_old.ReservationId 
                     AND dd_old.StayDate = DATEADD(day, -1, dd_new.StayDate) 
                     AND dd_old.Room <> dd_new.Room
                WHERE CAST(dd_new.StayDate AS DATE) = @Today
                  AND dd_new.ReservationId > 0
                  AND ISNULL(dd_old.Room, '') <> '' 
                  AND ISNULL(dd_new.Room, '') <> ''
                UNION
                SELECT dd_new.Room AS Room
                FROM DailyDetail dd_new
                JOIN DailyDetail dd_old ON dd_new.ReservationId = dd_old.ReservationId 
                     AND dd_old.StayDate = DATEADD(day, -1, dd_new.StayDate) 
                     AND dd_old.Room <> dd_new.Room
                WHERE CAST(dd_new.StayDate AS DATE) = @Today
                  AND dd_new.ReservationId > 0
                  AND ISNULL(dd_old.Room, '') <> '' 
                  AND ISNULL(dd_new.Room, '') <> ''
            ) rc_all
        )
        SELECT 
            rm.Room AS [ODA],
            rm.RoomTypeCode AS [TIP],
            rm.Remark AS [REMARK],
            rm.HkKontrol AS [AKSAM_SERVISI],
            COALESCE(NULLIF(ISNULL(res.FirstName1, '') + ' ' + ISNULL(res.LastName1, ''), ' '), ms.GuestName, '') AS [MISAFIR_ADI],
            ISNULL(res.BedType, '') AS [YATAK_TIPI],
            COALESCE(NULLIF(res.Acente, ''), ms.AgencyName, '') AS [ACENTE],
            CASE 
                WHEN res.CheckinDate IS NOT NULL THEN CONVERT(VARCHAR(10), res.CheckinDate, 104) 
                WHEN ms.CheckinDate IS NOT NULL THEN CONVERT(VARCHAR(10), ms.CheckinDate, 104) 
                ELSE '' 
            END AS [CHECKIN_TARIHI],
            CASE 
                WHEN res.CheckOutDate IS NOT NULL THEN CONVERT(VARCHAR(10), res.CheckOutDate, 104) 
                WHEN ms.CheckOutDate IS NOT NULL THEN CONVERT(VARCHAR(10), ms.CheckOutDate, 104) 
                ELSE '' 
            END AS [CHECKOUT_TARIHI],
            CASE WHEN ISNULL(res.Remark, '') <> '' THEN res.Remark ELSE res.ResRemark END AS [REZ_NOTU],
            CASE WHEN res.Status = 2 AND CAST(res.CheckinDate AS DATE) <= @Today AND CAST(res.CheckOutDate AS DATE) >= @Today THEN 1 ELSE 0 END AS [DOLU_BOS],
            CASE WHEN arr.HasArrival = 1 THEN 1 WHEN res.Status = 1 AND CAST(res.CheckinDate AS DATE) = @Today THEN 1 ELSE 0 END AS [BUGUN_GELEN],
            CASE 
                WHEN dep.Room IS NOT NULL THEN 1
                WHEN (res.Status = 2 OR res.Status = 3) AND CAST(res.CheckOutDate AS DATE) = @Today THEN 1 
                WHEN ms.CheckOutDate = @Today THEN 1
                ELSE 0 
            END AS [BUGUN_GIDECEK],
            CASE 
                WHEN arr.HasArrival = 1 AND (dep.OdadaHala = 1 OR dep.CikisYapildi = 1) THEN 1
                ELSE 0
            END AS [IS_CO_CI],
            CASE 
                WHEN (rm.DirtyClean = 1 OR rm.HkStatus = 1) 
                     AND rm.HkStatus NOT IN (4, 5)
                     AND ISNULL(dd.[Status], 0) NOT IN (3, 4)
                     AND rc.Room IS NULL
                     AND res.RecId IS NULL 
                     AND (ms.CheckOutDate IS NULL OR ms.CheckOutDate <> @Today)
                     AND (ms.CheckinDate IS NULL OR ms.CheckinDate <> @Today)
                     AND ms.DirtyClean = 1
                THEN 1 ELSE 0 
            END AS [BOS_KIRLI],
            CASE 
                WHEN rc.Room IS NOT NULL THEN 1 ELSE 0
            END AS [IS_ROOM_CHANGE],
            CASE 
                WHEN dep.OdadaHala = 1 THEN 'ODADA_HALA'
                WHEN dep.CikisYapildi = 1 THEN 'CO_YAPILDI'
                WHEN CAST(res.CheckOutDate AS DATE) = @Today AND res.Status = 3 THEN 'CO_YAPILDI'
                WHEN CAST(res.CheckOutDate AS DATE) = @Today AND res.Status = 2 THEN 'ODADA_HALA'
                WHEN ms.CheckOutDate = @Today THEN 'CO_YAPILDI'
                ELSE ''
            END AS [CO_DURUM],
            ISNULL(res.LateCOut, '') AS [UZATMA_SAATI],
            dd.StatusRemark AS [STATUS_REMARK],
            ISNULL(dd.[Status], 0) AS [DD_STATUS],
            CASE 
                WHEN ISNULL(dd.[Status], 0) IN (3, 4) THEN 'ARIZALI (OOO)'
                WHEN dd.[Status] = 2 THEN 'BLOKELI'
                WHEN rm.HkStatus = 4 THEN 'ARIZALI (OOO)'
                WHEN rm.HkStatus = 5 THEN 'BLOKELI'
                WHEN rm.HkStatus = 3 THEN 'OK'
                WHEN rm.DirtyClean = 1 OR rm.HkStatus = 1 THEN 'KIRLI'
                WHEN rm.DirtyClean = 0 OR rm.HkStatus = 2 THEN 'TEMIZ'
                ELSE 'KIRLI'
            END AS [DURUM],
            ISNULL(rm.DirtyClean, 1) AS [RM_DIRTY_CLEAN],
            CASE 
                WHEN rm.HkStatus = 3 AND ISNULL(dd.[Status], 0) NOT IN (3, 4) THEN 'EVET'
                ELSE 'HAZIR_MI'
            END AS [HAZIR_MI],
            ISNULL(res.Pax, ms.Pax) AS Pax,
            ISNULL(res.Childs, ms.Childs) AS Childs
        FROM Room rm
        LEFT JOIN ActiveRes res ON rm.Room = res.MatchRoom AND res.rn = 1
        LEFT JOIN TodayArr arr ON rm.Room = arr.Room
        LEFT JOIN TodayDep dep ON rm.Room = dep.Room
        LEFT JOIN MorningSnapshot ms ON rm.Room = ms.Room AND ms.rn = 1
        LEFT JOIN TodayDD dd ON rm.Room = dd.Room AND dd.rn = 1
        LEFT JOIN TodayRC rc ON rm.Room = rc.Room
        WHERE rm.ForeCast = 1
        ORDER BY rm.Room
    """, conn)

    df = df.fillna('')
    # Robust normalization of status fields
    if 'DURUM' in df.columns:
        df['DURUM'] = df['DURUM'].astype(str).apply(
            lambda s: 'ARIZALI (OOO)' if 'ARIZ' in s.upper() or 'OOO' in s.upper()
            else ('BLOKELI' if 'BLOK' in s.upper()
            else ('OK' if s.upper() == 'OK' or 'HAZIR' in s.upper()
            else ('TEMIZ' if 'TEM' in s.upper()
            else ('KIRLI' if 'K' in s.upper() else s))))
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
    
    # HkStatus 1 = Kirli, 3 = OK/Hazır, 4 = OOO, 5 = Blokeli, 0 = Normal/Temiz
    hk_status_val = status if status in [1, 3, 4, 5] else 0
    
    # DD Status Mapping: 3=OOO (Sedna Standart OOO), 2=V.A.D/Blokeli, 0=Normal
    dd_status = 0
    if status == 4: dd_status = 3  # Sedna'da OOO kodu DailyDetail.Status = 3'tür (HkRoomRack & FnOOO standartı)
    if status == 5: dd_status = 2  # Blokeli / V.A.D
    
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
    Sedna veritabanindan Sedna Ön Büro alt durum çubuğu ile %100 birebir örtüşen
    Inhouse, Arrival, Giriş (C/In), Departure (Odada Hâlâ), Çıkış Yapan (C/Out) ve C/Out-C/In istatistiklerini alır.
    """
    cursor = conn.cursor()
    cursor.execute("""
        DECLARE @Today DATE = CAST(GETDATE() AS DATE);
        SELECT 
            -- 1. Inhouse: Konaklayan aktif rezervasyonlar
            (SELECT COUNT(DISTINCT RecId) FROM Reservation WHERE Status = 2 AND CAST(CheckinDate AS DATE) <= @Today AND CAST(CheckOutDate AS DATE) >= @Today AND StatusCode IN (0,1,2,3)) AS Inh_Res,
            (SELECT ISNULL(SUM(Pax + ISNULL(Childs,0)),0) FROM Reservation WHERE Status = 2 AND CAST(CheckinDate AS DATE) <= @Today AND CAST(CheckOutDate AS DATE) >= @Today AND StatusCode IN (0,1,2,3)) AS Inh_Pax,
            
            -- 2. Arrival: Bugün beklenen girişler (Henüz gelmeyenler)
            (SELECT COUNT(DISTINCT RecId) FROM Reservation WHERE Status = 1 AND CAST(CheckinDate AS DATE) = @Today AND StatusCode IN (0,1,2,3)) AS Arr_Res,
            (SELECT ISNULL(SUM(Pax + ISNULL(Childs,0)),0) FROM Reservation WHERE Status = 1 AND CAST(CheckinDate AS DATE) = @Today AND StatusCode IN (0,1,2,3)) AS Arr_Pax,
            
            -- 3. Giriş Yapan: Bugün girişi yapılanlar (C/In)
            (SELECT COUNT(DISTINCT RecId) FROM Reservation WHERE Status = 2 AND CAST(CheckinDate AS DATE) = @Today AND StatusCode IN (0,1,2,3)) AS Cin_Res,
            (SELECT ISNULL(SUM(Pax + ISNULL(Childs,0)),0) FROM Reservation WHERE Status = 2 AND CAST(CheckinDate AS DATE) = @Today AND StatusCode IN (0,1,2,3)) AS Cin_Pax,
            
            -- 4. Departure: Bugün çıkış beklenen ama henüz çıkmamış olanlar (Odada Hâlâ)
            (SELECT COUNT(DISTINCT RecId) FROM Reservation WHERE Status = 2 AND CAST(CheckOutDate AS DATE) = @Today AND StatusCode IN (0,1,2,3)) AS Dep_Res,
            (SELECT ISNULL(SUM(Pax + ISNULL(Childs,0)),0) FROM Reservation WHERE Status = 2 AND CAST(CheckOutDate AS DATE) = @Today AND StatusCode IN (0,1,2,3)) AS Dep_Pax,
            
            -- 5. Çıkış Yapan: Bugün çıkışı tamamlanmış olanlar (C/Out)
            (SELECT COUNT(DISTINCT RecId) FROM Reservation WHERE Status = 3 AND CAST(CheckOutDate AS DATE) = @Today AND StatusCode IN (0,1,2,3)) AS Cout_Res,
            (SELECT ISNULL(SUM(Pax + ISNULL(Childs,0)),0) FROM Reservation WHERE Status = 3 AND CAST(CheckOutDate AS DATE) = @Today AND StatusCode IN (0,1,2,3)) AS Cout_Pax
    """)
    r = cursor.fetchone()
    
    # C/Out - C/In oda sayısı (Aynı gün hem çıkış hem giriş olan turnaround odalar)
    cursor.execute("""
        DECLARE @Today DATE = CAST(GETDATE() AS DATE);
        SELECT COUNT(DISTINCT rm.Room)
        FROM Room rm
        LEFT JOIN DailyDetail dd ON rm.Room = dd.Room AND CAST(dd.StayDate AS DATE) = @Today
        WHERE rm.ForeCast = 1 
          AND ISNULL(dd.[Status], 0) NOT IN (3, 4)
          AND EXISTS (
              SELECT 1 FROM Reservation a 
              WHERE COALESCE(NULLIF(a.Room, ''), (SELECT rm_ref.Room FROM Room rm_ref WHERE a.RoomNummer = rm_ref.RecId)) = rm.Room 
                AND a.Status = 1 AND CAST(a.CheckinDate AS DATE) = @Today AND a.StatusCode IN (0,1,2,3) 
                AND ISNULL(a.Voucher, '') NOT LIKE '%NOSHOW%' AND ISNULL(a.ResRemark, '') NOT LIKE '%NOSHOW%'
          )
          AND EXISTS (
              SELECT 1 FROM Reservation d 
              WHERE COALESCE(NULLIF(d.Room, ''), (SELECT rm_ref.Room FROM Room rm_ref WHERE d.RoomNummer = rm_ref.RecId)) = rm.Room 
                AND d.Status IN (2, 3) AND CAST(d.CheckOutDate AS DATE) = @Today AND d.StatusCode IN (0,1,2,3) 
                AND ISNULL(d.Voucher, '') NOT LIKE '%NOSHOW%' AND ISNULL(d.ResRemark, '') NOT LIKE '%NOSHOW%'
          )
    """)
    coci_cnt = cursor.fetchone()[0] or 0

    return {
        "inhouse": {"oda": int(r[0] or 0), "pax": int(r[1] or 0)},
        "arrivals": {"oda": int(r[2] or 0), "pax": int(r[3] or 0)},
        "checkins": {"oda": int(r[4] or 0), "pax": int(r[5] or 0)},
        "departures": {"oda": int(r[6] or 0), "pax": int(r[7] or 0)},
        "checkouts": {"oda": int(r[8] or 0), "pax": int(r[9] or 0)},
        "coci": {"oda": int(coci_cnt), "pax": 0}
    }

def get_room_changes(conn, target_date=None):
    """Belirtilen tarihte (varsayılan bugün) gerçekleşen veya planlanan Room Change listesini döndürür."""
    cursor = conn.cursor()
    cursor.execute("""
        DECLARE @TargetDate DATE = COALESCE(?, CAST(GETDATE() AS DATE));
        SELECT DISTINCT
            rc_data.OldRoom,
            rc_data.NewRoom,
            COALESCE(NULLIF(ISNULL(r.FirstName1, '') + ' ' + ISNULL(r.LastName1, ''), ' '), '') AS GuestName,
            ISNULL(r.Voucher, '') AS Voucher,
            rc_data.ChangeTime,
            rc_data.Source
        FROM (
            -- 1. LOG tablosu üzerinden gerçekleşen Oda Değişiklikleri (Sedna Ön Büro Değiştirilen Odalar ile %100 birebir)
            SELECT 
                l.Old AS OldRoom, 
                l.New AS NewRoom,
                l.ResId AS ReservationId,
                CONVERT(VARCHAR(5), l.ADateTime, 108) AS ChangeTime,
                'Fiili RC' AS Source
            FROM LOG l
            INNER JOIN Reservation r ON l.ResId = r.RecId
            WHERE l.FieldName = 'Room'
              AND l.Old IS NOT NULL AND l.Old != '' AND l.Old NOT IN ('Basic Blocking', 'Cancel Blocking')
              AND l.New IS NOT NULL AND l.New != '' AND l.New NOT IN ('Basic Blocking', 'Cancel Blocking')
              AND l.Old != l.New
              AND CAST(l.ADateTime AS DATE) = @TargetDate
              AND CAST(r.CheckOutDate AS DATE) = @TargetDate

            UNION

            -- 2. DailyDetail üzerinden gerçekleşmiş fiili Room Change
            SELECT 
                dd_old.Room AS OldRoom, 
                dd_new.Room AS NewRoom,
                dd_new.ReservationId,
                CONVERT(VARCHAR(5), dd_new.UpdateDate, 108) AS ChangeTime,
                'Fiili RC' AS Source
            FROM DailyDetail dd_new
            JOIN DailyDetail dd_old ON dd_new.ReservationId = dd_old.ReservationId 
                 AND dd_old.StayDate = DATEADD(day, -1, dd_new.StayDate) 
                 AND dd_old.Room <> dd_new.Room
            WHERE CAST(dd_new.StayDate AS DATE) = @TargetDate
              AND dd_new.ReservationId > 0
              AND ISNULL(dd_old.Room, '') <> '' 
              AND ISNULL(dd_new.Room, '') <> ''

            UNION

            -- 3. Sedna RoomChangePlan tablosu (Sadece hedef güne ait planlar)
            SELECT 
                rcp.OldRoom, 
                rcp.NewRoom, 
                rcp.ReservationId,
                CONVERT(VARCHAR(5), rcp.[Time], 108) AS ChangeTime,
                'Planlanan RC' AS Source
            FROM RoomChangePlan rcp
            WHERE CAST(rcp.RCDate AS DATE) = @TargetDate
              AND ISNULL(rcp.Deleted, 0) = 0
              AND ISNULL(rcp.OldRoom, '') <> '' 
              AND ISNULL(rcp.NewRoom, '') <> ''
        ) rc_data
        LEFT JOIN Reservation r ON rc_data.ReservationId = r.RecId
        ORDER BY rc_data.OldRoom
    """, (target_date,))
    cols = [c[0] for c in cursor.description]
    return [dict(zip(cols, r)) for r in cursor.fetchall()]

def get_late_checkouts(conn, target_date=None):
    """Belirtilen tarihte (varsayılan bugün) tanımlı Late Check-out (Uzatma) listesini döndürür."""
    cursor = conn.cursor()
    cursor.execute("""
        DECLARE @TargetDate DATE = COALESCE(?, CAST(GETDATE() AS DATE));
        SELECT 
            r.Room,
            r.LateCOut AS UzatmaSaati,
            COALESCE(NULLIF(ISNULL(r.FirstName1, '') + ' ' + ISNULL(r.LastName1, ''), ' '), '') AS GuestName,
            ISNULL(r.Voucher, '') AS Voucher,
            CONVERT(VARCHAR(10), r.CheckOutDate, 104) AS CheckOutDate,
            r.Status,
            CASE 
                WHEN r.Status = 3 THEN 'Çıkış Yaptı'
                WHEN r.Status = 2 THEN 'Odada'
                ELSE 'Bekliyor'
            END AS DurumText
        FROM Reservation r
        INNER JOIN Room rm ON r.Room = rm.Room AND rm.ForeCast = 1
        WHERE CAST(r.CheckOutDate AS DATE) = @TargetDate
          AND NULLIF(RTRIM(LTRIM(r.LateCOut)), '') IS NOT NULL
          AND r.StatusCode IN (0,1,2,3)
          AND r.Status IN (2, 3)
          AND ISNULL(r.Voucher, '') NOT LIKE '%NOSHOW%'
          AND ISNULL(r.Voucher, '') NOT LIKE '%NO-SHOW%'
          AND ISNULL(r.ResRemark, '') NOT LIKE '%NOSHOW%'
          AND ISNULL(r.ResRemark, '') NOT LIKE '%NO-SHOW%'
        ORDER BY r.LateCOut ASC, r.Room ASC
    """, (target_date,))
    cols = [c[0] for c in cursor.description]
    return [dict(zip(cols, r)) for r in cursor.fetchall()]


