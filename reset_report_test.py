import pymongo
from datetime import date

uri = "mongodb+srv://amansahu205_db_user:KCmbbe9sAWvDFmZO@cluster0.yjhwpea.mongodb.net/?retryWrites=true&w=majority"
client = pymongo.MongoClient(uri)
db = client["pilotpm"]

y, w, _ = date.today().isocalendar()
wid = f"{y}-W{w:02d}"

print(f"Checking for finalized reports in week {wid}...")
res = db["status_reports"].delete_many({"week_id": wid, "status": "sent"})
print(f"Deleted {res.deleted_count} sent report(s) from the remote Database.")
