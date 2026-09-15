import { useEffect, useRef, useState } from "react";
import { Html5Qrcode } from "html5-qrcode";
import { checkAccess } from "../api/endpoints";

const REASON_LABELS = {
  ruxsat: "Ruxsat berildi",
  topilmadi: "Token topilmadi",
  muddati_tugagan: "Abonement muddati tugagan",
  muzlatilgan: "Abonement muzlatilgan",
  kunlik_limit_tugagan: "Kunlik limitga yetgan",
  umumiy_limit_tugagan: "Umumiy limitga yetgan",
};

export default function ScannerPage() {
  const [cameraOn, setCameraOn] = useState(false);
  const [manualToken, setManualToken] = useState("");
  const [result, setResult] = useState(null);
  const [checking, setChecking] = useState(false);
  const [cameraError, setCameraError] = useState("");
  const scannerRef = useRef(null);
  const busyRef = useRef(false);

  useEffect(() => {
    if (!cameraOn) return undefined;

    const scanner = new Html5Qrcode("qr-reader");
    scannerRef.current = scanner;

    scanner
      .start(
        { facingMode: "environment" },
        { fps: 10, qrbox: 240 },
        (decodedText) => {
          if (busyRef.current) return;
          runCheck(decodedText);
        },
        () => {}
      )
      .catch((err) => setCameraError(String(err)));

    return () => {
      scanner.stop().then(() => scanner.clear()).catch(() => {});
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cameraOn]);

  async function runCheck(token) {
    busyRef.current = true;
    setChecking(true);
    setResult(null);
    try {
      const data = await checkAccess(token);
      setResult(data);
    } catch {
      setResult({ allowed: false, reason: "xatolik", client: null, left_days: null });
    } finally {
      setChecking(false);
      setTimeout(() => {
        busyRef.current = false;
      }, 2500);
    }
  }

  function handleManualSubmit(e) {
    e.preventDefault();
    if (!manualToken.trim()) return;
    runCheck(manualToken.trim());
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <div className="grid grid-cols-2">
        <div className="card">
          <h3>Kamera orqali skanerlash</h3>
          {!cameraOn ? (
            <button className="btn btn-primary" onClick={() => setCameraOn(true)}>
              Kamerani yoqish
            </button>
          ) : (
            <>
              <div id="qr-reader" style={{ width: "100%" }} />
              <div style={{ marginTop: 12 }}>
                <button className="btn" onClick={() => setCameraOn(false)}>
                  Kamerani o'chirish
                </button>
              </div>
              {cameraError && (
                <div className="alert alert-danger" style={{ marginTop: 12 }}>
                  Kameraga ulanib bo'lmadi: {cameraError}
                </div>
              )}
            </>
          )}
        </div>

        <div className="card">
          <h3>Tokenni qo'lda kiritish</h3>
          <form onSubmit={handleManualSubmit}>
            <div className="form-row">
              <label>QR token</label>
              <input
                value={manualToken}
                onChange={(e) => setManualToken(e.target.value)}
                placeholder="masalan: 6bc6e7e3-9e85-..."
              />
            </div>
            <button className="btn btn-primary" type="submit" disabled={checking}>
              {checking ? "Tekshirilmoqda..." : "Tekshirish"}
            </button>
          </form>
        </div>
      </div>

      {result && (
        <div className={`scanner-result ${result.allowed ? "ok" : "fail"}`}>
          <h2>{result.allowed ? "✅" : "⛔"} {REASON_LABELS[result.reason] ?? result.reason}</h2>
          {result.client && (
            <div>
              <p>
                <strong>F.I.SH:</strong> {result.client.full_name}
              </p>
              <p>
                <strong>Karta:</strong> {result.client.card_code}
              </p>
              <p>
                <strong>Tarif:</strong> {result.client.plan}
              </p>
              {result.left_days !== null && (
                <p>
                  <strong>Qolgan kun:</strong> {result.left_days}
                </p>
              )}
              {result.today_visits !== undefined && (
                <p>
                  <strong>Bugungi tashrif:</strong> {result.today_visits}
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
