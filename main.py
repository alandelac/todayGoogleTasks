import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import copy
import datetime



# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/tasks"]

class Task:
  def __init__(self, id, status = "needsAction", title = "Empty Task", due = datetime.datetime.now):
    self.status = status
    self.title = title
    self.due = due
    self.id = id
    
  def __str__(self) -> str:
    return "Title: " + self.title + ", Date: " + self.date + ", Done: " + self.done + "\n id: " + self.id
    
class TaskList:
  def __init__(self, title, id, tasks = []):
    self.title = title
    self.id = id
    self.tasks = tasks
    
  def __str__(self) -> str:
    return "Title: " + self.title + ", Id: " + self.id
  
# Obtiene la fecha y hora actual en formato RFC 3339
def get_rfc3339_timestamp():
    now = datetime.datetime.now(datetime.timezone.utc)
    end_of_day = now.replace(hour=00, minute=00, second=00, microsecond=00)
    fecha_manana = end_of_day + datetime.timedelta(days=1)

    fecha_formateada = fecha_manana.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    return fecha_formateada
  #'2024-03-01T00:00:00.000Z'
  
def actualizarHoy():
    
    print("actualizando listas")
    
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
      creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
      if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
      else:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", SCOPES
        )
        creds = flow.run_local_server(port=0)
      # Save the credentials for the next run
      with open("token.json", "w") as token:
        token.write(creds.to_json())

    try:
      service = build("tasks", "v1", credentials=creds)

      # Call the Tasks API
      results = service.tasklists().list(maxResults=100).execute()
      lists = results.get("items", [])
      
      TaskLists = []

      if not lists:
        print("No task lists found.")
        return
      
      # Ejemplo de uso
      rfc3339_date = get_rfc3339_timestamp()
      
      hoyId = None
      hoyIndex = -1
      
      i = 0
      
      #GENERAR OBJETOS DE TASKLIST CON RESPECTIVAS TASKS
      for item in lists:
        
        taskList = TaskList(item["title"], item["id"])
        taskList.tasks = []
        
        if item['title'] != "Hoy":
          results2 = service.tasks().list(tasklist = item["id"], showCompleted = False, 
                                         dueMax = rfc3339_date, maxResults = 100).execute()
          tasks = results2.get("items", [])
          
          if not tasks:
            # print("No tasks found in the list: " + item["title"])
            pass
          else:
            for curTask in tasks:
              main_task = Task(curTask["id"], curTask["status"], curTask["title"], curTask["due"])
              taskList.tasks.append(copy.deepcopy(main_task))
                         
              #marcar como completa
              updateStatus = {
                'title': curTask["title"],
                'due': curTask["due"],
                'status': 'completed',
                'id': curTask["id"]
              }
              
              service.tasks().update(tasklist = item["id"], task = curTask["id"], body = updateStatus).execute()
              
            tasks = []
              
        else:
          hoyId = item["id"]
          hoyIndex = i
          
        
        TaskLists.append(copy.deepcopy(taskList))
        
        i = i+1
        
      # iterar sobre cada tarea y moverlas a la lista de hoy
      for task_list in TaskLists:
        if len(task_list.tasks) > 0 and task_list.title != "Hoy":
          
          for task in task_list.tasks:
            
            new_task = {
              'title': task.title,
              'due': task.due,
              'status': task.status,
            }
          
            service.tasks().insert(tasklist = hoyId, body = new_task).execute()
        
        
    except HttpError as err:
      print(err)
    # OBTENER TAREAS DE TODAS LAS LISTA
    # FILTRAR LAS TAREAS PARA FECHAS PASADAS Y DE HOY
    # NO BUSCAR EN LALISTA HOY, SOLO EN LAS DEMAS
    # MOVER LAS TAREAS SELECCIONADAS A LA LISTA DE HOY


def main():

# Schedule the method to run every day at 01:00

  print("corriendo")

  #schedule.every().day.at("04:30").do(actualizarHoy)
  actualizarHoy()
  '''
  while True:
    schedule.run_pending()
    time.sleep(55)  # Wait for one minute
  '''  
  

if __name__ == "__main__":
  main()