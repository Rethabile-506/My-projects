import requests
import json
from tkinter import *

coin_pl=Tk()
coin_pl.title("Crypto_Coin_Planner")

def color_pl(amt):
    if amt>=0:
        return ("green")
    else:
        return("red")

def data():
    api_req=requests.get("https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?start=1&limit=300&convert=USD&CMC_PRO_API_KEY=509e75dc-7be0-4804-8635-a4a78c1fed28")
    api_jsn=json.loads(api_req.content)
    row1=1
    coins=[
        {
            "symbol":"BTC",
            "amt_no": 5,
            "price":50000,
        },
        {
            "symbol":"BNB",
            "amt_no": 12,
            "price":500,
        },
        {
            "symbol":"USDT",
            "amt_no": 18,
            "price":500,
        },
        {
            "symbol":"ADA",
            "amt_no": 500,
            "price":3,
        }
    ]
    total_pr_l=0
    for i in range(0,300):
        for coin in coins:
            if api_jsn["data"][i]["symbol"] == coin["symbol"] :
                total_paid=coin["amt_no"]*coin["price"]
                current_value=coin["amt_no"]*api_jsn["data"][i]["quote"]["USD"]["price"]
                p_l_coin=api_jsn["data"][i]["quote"]["USD"]["price"]-coin["price"]
                tot_p_l_coin=p_l_coin*coin["amt_no"]
                total_pr_l=total_pr_l+tot_p_l_coin
                # print(api_jsn["data"][i]["symbol"])
                # print("Value - ${0:.4f}".format(api_jsn["data"][i]["quote"]["USD"]["price"]))
                # print("Total Paid - ${0:.4f}".format(total_paid))
                # print("Total Current Value - ${0:.4f}".format(current_value))
                # print("Profit/Loss per coin Value - ${0:.4f}".format(p_l_coin))
                # print("Total Profit/Loss per coin Value - ${0:.4f}".format(tot_p_l_coin))
                # print("*************")


                name=Label(coin_pl,text=api_jsn["data"][i]["symbol"],bg="white", fg="black", font="Arial 14 bold",padx="5",pady="5",borderwidth=4,relief="groove")
                name.grid(row=row1,column=0,sticky=N+S+E+W)

                name3=Label(coin_pl,text= "${0:.4f}".format(api_jsn["data"][i]["quote"]["USD"]["price"]),bg="white", fg="black", font="Arial 14 bold",padx="5",pady="5",borderwidth=4,relief="groove")
                name3.grid(row=row1,column=3,sticky=N+S+E+W)

                name6=Label(coin_pl,text="${0:.4f}".format(current_value),bg="white", fg="black", font="Arial 14 bold",padx="5",pady="5",borderwidth=4,relief="groove")
                name6.grid(row=row1,column=1,sticky=N+S+E+W)

                name2=Label(coin_pl,text="${0:.4f}".format(total_paid),bg="white", fg="black", font="Arial 14 bold",padx="5",pady="5",borderwidth=4,relief="groove")
                name2.grid(row=row1,column=2,sticky=N+S+E+W)


                name4=Label(coin_pl,text="${0:.4f}".format(p_l_coin),bg="white", fg="black", font="Arial 14 bold",padx="5",pady="5",borderwidth=4,relief="groove")
                name4.grid(row=row1,column=4,sticky=N+S+E+W)


                name5=Label(coin_pl,text="${0:.4f}".format(tot_p_l_coin),bg="white", fg=color_pl(float(tot_p_l_coin)), font="Arial 14 bold",padx="5",pady="5",borderwidth=4,relief="groove")
                name5.grid(row=row1,column=5,sticky=N+S+E+W)

                name5=Label(coin_pl,text="${0:.4f}".format(total_pr_l),bg="white", fg=color_pl(float(total_pr_l)), font="Arial 14 bold",padx="5",pady="5",borderwidth=4,relief="groove")
                name5.grid(row=row1+1,column=5,sticky=N+S+E+W)

                row1=row1+1
                

    api_jsn=""
    name5=Button(coin_pl,text="Update",command=data,bg="white", fg=color_pl(float(total_pr_l)), font="Arial 14 bold",padx="5",pady="5",borderwidth=4,relief="groove")
    name5.grid(row=row1+1,column=5,sticky=N+S+E+W)



    print("Total Profit/Loss all coins Value - ${0:.4f}".format(total_pr_l))


name=Label(coin_pl,text="Name   ",bg="#7FFFD4", fg="black", font="Arial 14 bold",padx="5",pady="5",borderwidth=4,relief="groove")
name.grid(row=0,column=0,sticky=N+S+E+W)

name3=Label(coin_pl,text="value  ",bg="#7FFFD4", fg="black",font="Arial 14 bold",padx="5",pady="5",borderwidth=4,relief="groove")
name3.grid(row=0,column=3,sticky=N+S+E+W)

name6=Label(coin_pl,text="Total  current value  ",bg="#7FFFD4", fg="black",font="Arial 14 bold",padx="5",pady="5",borderwidth=4,relief="groove")
name6.grid(row=0,column=1,sticky=N+S+E+W)

name2=Label(coin_pl,text="Total paid  " ,bg="#7FFFD4", fg="black",font="Arial 14 bold",padx="5",pady="5",borderwidth=4,relief="groove")
name2.grid(row=0,column=2,sticky=N+S+E+W)


name4=Label(coin_pl,text="Prof/loss per coin ",bg="#7FFFD4", fg="black",font="Arial 14 bold",padx="5",pady="5",borderwidth=4,relief="groove")
name4.grid(row=0,column=4,sticky=N+S+E+W)


name5=Label(coin_pl,text="Total prf/loss percoin",bg="#7FFFD4", fg="black",font="Arial 14 bold",padx="5",pady="5",borderwidth=4,relief="groove")
name5.grid(row=0,column=5,sticky=N+S+E+W)



data()
coin_pl.mainloop()