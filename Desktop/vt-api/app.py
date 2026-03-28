from flask import Flask, jsonify, request
import vtt
from vtt import Semester
import math
import threading  # ← add this

app = Flask(__name__)

# ← add this block
cached_data = {}

def preload():
    subjects = ['CS', 'MATH', 'PHYS', 'ECE', 'ENGL', 'STAT', 'CHEM', 'BIOL', 'ECON', 'HIST']
    for subject in subjects:
        try:
            results = vtt.search_timetable('2026', Semester.SPRING, subject=subject)
            if not results:
                continue
            output = []
            for c in results:
                try:
                    code = c.get_code()
                    if not code or int(code[:4]) > 5000:
                        continue
                    schedule_data = c.get_schedule()
                    if not schedule_data:
                        continue
                    clean_schedule = []
                    for day, times in schedule_data.items():
                        for time_slot in times:
                            clean_schedule.append({
                                "day": day.value,
                                "start": time_slot[0],
                                "end": time_slot[1],
                                "location": time_slot[2]
                            })
                    professor = c.get_professor()
                    modality = c.get_modality()
                    output.append({
                        "name": c.get_name(),
                        "crn": c.get_crn(),
                        "code": code,
                        "professor": professor if not (isinstance(professor, float) and math.isnan(professor)) else "TBA",
                        "credits": c.get_credit_hours(),
                        "schedule": clean_schedule,
                        "modality": modality.name if modality else "UNKNOWN",
                        "open_spots": c.has_open_spots()
                    })
                except Exception:
                    continue
            cached_data[subject] = output
            print(f"✓ Cached {subject} ({len(output)} courses)")
        except Exception as e:
            print(f"✗ Failed to cache {subject}: {e}")

threading.Thread(target=preload, daemon=True).start()  # ← starts on server launch

@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    return response

@app.route('/schedule')
def get_schedule():
    subject = request.args.get('subject', 'CS')
    
    if subject in cached_data:          # ← return instantly if cached
        return jsonify(cached_data[subject])

    # fallback: fetch live if not cached yet
    results = vtt.search_timetable('2026', Semester.SPRING, subject=subject)
    if not results:
        return jsonify({"error": "No classes found"}), 404

    output = []
    for c in results:
        try:
            code = c.get_code()
            if not code or int(code[:4]) > 5000:
                continue
            schedule_data = c.get_schedule()
            if not schedule_data:
                continue
            clean_schedule = []
            for day, times in schedule_data.items():
                for time_slot in times:
                    clean_schedule.append({
                        "day": day.value,
                        "start": time_slot[0],
                        "end": time_slot[1],
                        "location": time_slot[2]
                    })
            professor = c.get_professor()
            modality = c.get_modality()
            output.append({
                "name": c.get_name(),
                "crn": c.get_crn(),
                "code": code,
                "professor": professor if not (isinstance(professor, float) and math.isnan(professor)) else "TBA",
                "credits": c.get_credit_hours(),
                "schedule": clean_schedule,
                "modality": modality.name if modality else "UNKNOWN",
                "open_spots": c.has_open_spots()
            })
        except Exception:
            continue

    return jsonify(output)

if __name__ == "__main__":
    app.run(port=5000, debug=True)