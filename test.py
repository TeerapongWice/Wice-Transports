print("Welcome to Tune")
print("Menu")
print("Item Option Price")
print("1. Pork Rice Porridge 35 Baht")
print("2. Chicken Congee 40 Baht")
print("3. Fried Egg with Rice 30 Baht")

choice = input("Input: choice: (ผู้ใช้กรอกตัวเลือก) ")

if choice == '1':
    print("You selected: Pork Rice Porridge")
    print("Price: 35 Baht")
elif choice == '2':
    print("You selected: Chicken Congee")
    print("Price: 40 Baht")
elif choice == '3':
    print("You selected: Fried Egg with Rice")
    print("Price: 30 Baht")
else:
    print("This item is not on the menu.")

print("Thank you for your order.")