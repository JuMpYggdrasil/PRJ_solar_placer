import tkinter as tk

class Human:
    def __init__(self):
        self.name = ""
        self.age = 0
        self.height = 0.0

    def input_information(self, name, age, height):
        self.name = name
        self.age = age
        self.height = height

    def display_information(self):
        return f"Name: {self.name}, Age: {self.age} years, Height: {self.height} meters"


class NameListApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Name List App")

        self.name_entry = tk.Entry(root)
        self.name_entry.pack(pady=5)

        self.age_entry = tk.Entry(root)
        self.age_entry.pack(pady=5)

        self.height_entry = tk.Entry(root)
        self.height_entry.pack(pady=5)

        self.add_button = tk.Button(root, text="Add Information", command=self.add_information)
        self.add_button.pack(pady=10)

        self.names_listbox = tk.Listbox(root)
        self.names_listbox.pack(pady=10)

        self.human_list = []

    def add_information(self):
        name = self.name_entry.get()
        age = int(self.age_entry.get())
        height = float(self.height_entry.get())

        if name and age and height:
            person = Human()
            person.input_information(name, age, height)
            self.human_list.append(person)

            # Display information in the listbox
            self.names_listbox.insert(tk.END, person.display_information())

            # Clear entry fields
            self.name_entry.delete(0, tk.END)
            self.age_entry.delete(0, tk.END)
            self.height_entry.delete(0, tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = NameListApp(root)
    root.mainloop()
