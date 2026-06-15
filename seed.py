import backend.database as database
import backend.departments as departments
import backend.employees as employees

"""
    For testing purposes. Delete this function and its uses in other files.
"""
def seed():
    database.init()

    departments.add_dept("Engineering")
    departments.add_dept("Design")
    departments.add_dept("Product")
    departments.add_dept("Human Resources")
    departments.add_dept("Marketing")
    departments.add_dept("Sales")
    departments.add_dept("Finance")
    departments.add_dept("IT")

    eng = departments.get_dept("Engineering")["id"]
    des = departments.get_dept("Design")["id"]

    employees.add_employee("E001", eng, "Sarah", "Chen")
    employees.add_employee("E002", eng, "Marcus", "Williams")
    employees.add_employee("E003", eng, "Elena", "Rodriguez")
    employees.add_employee("E004", des, "James", "Park")
    employees.add_employee("E005", des, "Priya", "Patel")
    employees.add_employee("E006", des, "Liam", "Smith")
    employees.add_employee("E007", des, "Ava", "Johnson")

if __name__ == "__main__":
    seed()



