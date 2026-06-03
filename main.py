import backend.database as database
import backend.employees as employees

database.init()

employees.add_employee("E001", 1, "John", "Smith", pc_model="Dell XPS", ram="16GB")
employees.add_employee("E676767", 1, "Christopher", "Bruh")
print(employees.get_employee("E001"))
