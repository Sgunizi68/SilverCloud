import pandas as pd
from datetime import datetime, timedelta

# Sample POS data
data = [
    {
        "Islem_Tarihi": "01.03.2026",
        "Hesaba_Gecis": "02.03.2026",
        "Para_Birimi": "TRY",
        "Islem_Tutari": 1500.50,
        "Kesinti_Tutari": 15.00,
        "Net_Tutar": 1485.50
    },
    {
        "Islem_Tarihi": "02.03.2026",
        "Hesaba_Gecis": "03.03.2026",
        "Para_Birimi": "TRY",
        "Islem_Tutari": 2200.00,
        "Kesinti_Tutari": 22.00,
        "Net_Tutar": 2178.00
    },
    {
        "Islem_Tarihi": "03.03.2026",
        "Hesaba_Gecis": "04.03.2026",
        "Para_Birimi": "TRY",
        "Islem_Tutari": 750.25,
        "Kesinti_Tutari": 7.50,
        "Net_Tutar": 742.75
    }
]

df = pd.DataFrame(data)
df.to_excel("pos_test_data.xlsx", index=False)
print("pos_test_data.xlsx created successfully.")
