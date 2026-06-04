import backend.database as database
import backend.departments as departments
import backend.employees as employees

database.init()

# Add departments

departments.add_dept("Engineering")
departments.add_dept("Design")
departments.add_dept("Product")
departments.add_dept("Human Resources")
departments.add_dept("Marketing")
departments.add_dept("Sales")
departments.add_dept("Finance")
departments.add_dept("IT")

# Add some employees

eng = departments.get_dept("Engineering")["id"]
des = departments.get_dept("Design")["id"]

employees.add_employee("E001", eng, "Sarah", "Chen")
employees.add_employee("E002", eng, "Marcus", "Williams")
employees.add_employee("E003", eng, "Elena", "Rodriguez")
employees.add_employee("E004", des, "James", "Park")
employees.add_employee("E005", des, "Priya", "Patel")

employees.delete_employee("E676767")
