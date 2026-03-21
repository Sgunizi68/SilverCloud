const XLSX = require('xlsx');
try {
    const workbook = XLSX.readFile(process.argv[2]);
    const firstSheetName = workbook.SheetNames[0];
    const worksheet = workbook.Sheets[firstSheetName];
    const jsonData = XLSX.utils.sheet_to_json(worksheet);
    if (jsonData.length > 0) {
        console.log(JSON.stringify(Object.keys(jsonData[0])));
    } else {
        console.log("Empty sheet");
    }
} catch (e) {
    console.error(e.message);
}
