from firebase import firebase
firebase = firebase.FirebaseApplication("https://pubquiztracker.firebaseio.com/", None)
def post():

	data = {
		"Scores": [20,21,22]
	}


	result = firebase.put("/pubquiztracker/Scores", "Test", data)
	print(result)

def retrieve():
	#-MMHz4wjFobmUs84vX8b
	# pot = 'BEN@BEN.com'
	result = firebase.get("/pubquiztracker/Users", "")
	# print(result)
	for k, v in result.items():
		if v['Email'] == "test@test.com":
			print(k)
			break
	# print(result)

def update():
	uList =  firebase.get("/pubquiztracker/Scores/-MMfd5aC3j_4GzH7zrOE", "")['Scores']

	uList.append(40)

	# print(id["Scores"])
	# id = id['Scores'].append(20)
	firebase.put(f"/pubquiztracker/Scores/-MMfd5aC3j_4GzH7zrOE", 'Scores', uList)
	# firebase.put(f"/pubquiztracker/Users/{id}", 'Name', "Bob")

def delete():
	id = "-MLj7469JOGwNoDoTMB"
	firebase.delete(f"/pubquiztracker/Users/", id)
	print("Deleted")
#
# scores = retrieve()
#
# for k, v in scores.items():
# 	print(v["Scores"])

post()