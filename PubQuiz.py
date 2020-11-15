from firebase import firebase
firebase = firebase.FirebaseApplication("https://pubquiztracker.firebaseio.com/", None)
def post():

	data = {
		"Name" : "Test",
		"Score": 14,
		"Date": "16/11/2020",
	}

	result = firebase.post("/pubquiztracker/Scores", data)
	print(result)

def retrieve():
	result = firebase.get("/pubquiztracker/Users", "")
	print(result)

def update():
	id = "-MLj7469JOGwNoDoTMB-"
	firebase.put(f"/pubquiztracker/Users/{id}", 'Name', "Bob")

def delete():
	id = "-MLj7469JOGwNoDoTMB"
	firebase.delete(f"/pubquiztracker/Users/", id)
	print("Deleted")

post()