from tkinter import messagebox
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from seleniumscraping import scraping
from secrets import config
import os.path
import sys
from macPath import *
from scheduling import set_up_scheduler
import io

#logger
import logging
logger = logging.getLogger(__name__)

def main():
	SCOPES = ["https://www.googleapis.com/auth/calendar.app.created", "https://www.googleapis.com/auth/calendar.calendarlist.readonly"]
	"""Shows basic usage of the Google Calendar API.
	Prints the start and name of the next 10 events on the user's calendar.
	"""

	print("setting up Logger")
	try:
		if sys.platform in ["Linux", "darwin"]:
			logger_path = get_path() / "GradeSync.log"
		else:
			print("logger path created")
			logger_path = get_win_path() / "GradeSync.log"
	
		#Setup Global Logger
		logging.basicConfig(filename=logger_path, encoding='utf-8', level=logging.INFO, filemode ='w')
	except Exception as e:
		print("logger creation failed:", e)

	creds = None
	#Define the token path for the google calendar api
	print("Setting up token path")
	if sys.platform in ["Linux", "darwin"]:
		token_path = get_path() / "token.json"
	else:
		print("token path created")
		token_path = get_win_path() / "token.json"

	# The file token.json stores the user's access and refresh tokens, and is
	# created automatically when the authorization flow completes for the first
	# time.
	first_time = True
	if os.path.exists(token_path):
		creds = Credentials.from_authorized_user_file(token_path, SCOPES)
		first_time = False

	# If there are no (valid) token available, let the user log in.
	if not creds or not creds.valid:
		if creds and creds.expired and creds.refresh_token:
			logger.info("Refreshing token")
			creds.refresh(Request())
		else:
			client_config = config
			flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
			creds = flow.run_local_server(port=0)
		# Save the credentials for the next run
		with open(token_path, "w") as token:
			token.write(creds.to_json())

	try:
		service = build("calendar", "v3", credentials=creds)
		logger.info("running")
		# Check if the Gradescope calendar exists, if not create it
		page_token = None
		grade_scope_cal_exists = False
		while True:
			calendar_list = service.calendarList().list(pageToken=page_token).execute()
			for calendar_list_entry in calendar_list['items']:
				if calendar_list_entry['summary'] == 'Gradescope Assignments':
					grade_scope_cal_exists = True
					id = calendar_list_entry['id']
					break
			page_token = calendar_list.get('nextPageToken')
			if not page_token:
				break
		#
		if not grade_scope_cal_exists:
			calendar = {
				'summary': 'Gradescope Assignments',
			}
			created_calendar = service.calendars().insert(body=calendar).execute()
			id = created_calendar['id']

		# Retrieve list of events
		events_result = service.events().list(calendarId=id).execute()
		events = events_result.get('items', [])
		print(len(events))
		print(events, events_result)
		page_token = None
		while True:
			events = service.events().list(calendarId=id, pageToken=page_token).execute()
			for event in events['items']:
				print(event['summary'])
			page_token = events.get('nextPageToken')
			if not page_token:
				break

		# Delete each event
		for event in events:
			print('deleting event', event['summary'])
			service.events().delete(calendarId=id, eventId=event['id']).execute()
			logger.info(f"Event {event['summary']} deleted.")

		try:
			service.calendars().clear(calendarId=id).execute()
		except Exception as e: 
			print("Failed to clear primary calendar", e)
		# Call scraping function to get events and insert them into the calendar
		events = scraping()
		for event in events:
			if event:
				event = service.events().insert(calendarId=id, body=event).execute()
				logger.info('Event created: %s' % (event.get('htmlLink')))
		
		print("done addding stuff")
		if first_time:
			set_up_scheduler()
	except Exception as error:
		logger.info(f"An error occurred: {error}")


if __name__ == "__main__":
	try:
		main()
	except Exception as e:
		print("Failed!", e)
		logger.error("Failed! %s", e)
