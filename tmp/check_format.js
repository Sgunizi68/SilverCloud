const fs = require('fs');
const filePath = "C:\\Users\\sg.msa\\OneDrive - ÇELEBİ AVIATION\\Personel\\Programming\\Yüklemeler\\Archieve\\Şube Bazlı Toplam Tabak Sayısı - 1.03.2026 06_00_00 - 23.03.2026 06_00_00.xlsx";

try {
    const data = fs.readFileSync(filePath, 'utf8');
    if (data.includes('<html') || data.includes('<table')) {
        console.log("This is an HTML file disguised as an Excel file!");
        console.log(data.slice(0, 500));
        
        // Simple HTML table parsing for check
        const rows = data.match(/<tr.*?>(.*?)<\/tr>/gs) || [];
        console.log(`Found ${rows.length} rows using regex.`);
        if (rows.length > 1) {
            console.log("Row 2:", rows[1].replace(/<[^>]+>/g, ' ').trim().replace(/\s+/g, ' '));
        }
    } else {
        console.log("Signature (first 10 chars):", fs.readFileSync(filePath).slice(0, 10).toString('hex'));
    }
} catch (e) {
    console.error(e);
}
