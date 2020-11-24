from bs4 import BeautifulSoup
import requests
from re import match
import smtplib
import conf
from email.mime.text import MIMEText


class GetQuiz:
	def __init__(self):
		self.site = r"https://www.joe.ie/quiz/the-joe-friday-pub-quiz"

	@staticmethod
	def notify(pqn, url, error=None):
		server = smtplib.SMTP('smtp.gmail.com', 587)
		server.ehlo()
		server.starttls()
		server.ehlo()
		server.login(conf.e, conf.p)


		if error:
			# Email only to me
			subject = f"There is an error in the script"

			body = f"{error}<br><br>Probably the type casting of week numbers.<br><br><a href={url}>Pub Quiz {pqn}</a>"
		else:
			# Emails of everyone
			subject = f"New Pub Quiz Is Live!"

			body = f"Hello motherfucker,<br><br><a href={url}>Pub Quiz {pqn}</a> is now live.<br><br>Best Regards,<br>G"

		msg = body

		message = MIMEText(msg, 'html')
		message['From'] = conf.e
		message['To'] = ''
		message['Subject'] = subject
		message = message.as_string()

		server.sendmail(
			conf.e,
			'',
			message
		)

		server.quit()

	def retrieve(self):
		data = requests.get(self.site)
		soup = BeautifulSoup(data.text, 'html.parser')

		for a in soup.find_all('a', {'class': 'time-posted-link'}):
			pot = a.attrs['href']
			
			# Test for now
			cur_quiz = 217
			if match(".*pub-quiz-week-.*", pot):
				pot_new =pot.split('pub-quiz-week-')[1][:3]

				url = f"https://www.joe.ie/{pot}"
				try:
					pot_new = int(pot_new)
				except (ValueError, TypeError) as e:

					self.notify(pot_new, url, e)
					quit()

				if pot_new > cur_quiz:
					# Send email to everyone
					# url = f"https://www.joe.ie/{pot}"
					self.notify(pot_new, url)
					# Update score in DB
					return True
