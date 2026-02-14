from tkinter import *

coin=Tk()
coin.title("Crypto_Coin_Planner")

name=Label(coin,text="name",bg="green", fg="black")
name.grid(row=0,column=0)

name3=Label(coin,text="value",bg="yellow", fg="black")
name3.grid(row=0,column=3)

name6=Label(coin,text="Total  current value",bg="yellow", fg="black")
name6.grid(row=0,column=1)

name2=Label(coin,text="Total paid",bg="green", fg="black")
name2.grid(row=0,column=2)


name4=Label(coin,text="prof/loss per coin",bg="green", fg="black")
name4.grid(row=0,column=4)


name5=Label(coin,text="total prof/loss per coin",bg="yellow", fg="black")
name5.grid(row=0,column=5)

name=Label(coin,text="name",bg="green", fg="black")
name.grid(row=1,column=0)

name3=Label(coin,text="value",bg="yellow", fg="black")
name3.grid(row=1,column=3)

name6=Label(coin,text="Total",bg="yellow", fg="black")
name6.grid(row=1,column=1)

name2=Label(coin,text="Total paid",bg="green", fg="black")
name2.grid(row=1,column=2)


name4=Label(coin,text="prof/locoin",bg="green", fg="black")
name4.grid(row=1,column=4)


name5=Label(coin,text="total p",bg="yellow", fg="black")
name5.grid(row=1,column=5)



coin.mainloop()


