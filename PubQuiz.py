from firebase import firebase
firebase = firebase.FirebaseApplication("https://pubquiztracker.firebaseio.com/", None)
def post():

	data = {
		"Name": "John Doe",
		"Email": "JohnD@gmail.com",
	}

	result = firebase.post("/pubquiztracker/Users", data)
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
